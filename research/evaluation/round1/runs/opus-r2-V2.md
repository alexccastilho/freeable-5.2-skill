# "Delete my account": plan

The button is the easy part. The real work is deciding what "delete" means for the four things a user is tied to: their Stripe subscription, the S3 uploads, the Postgres rows, and the **team workspaces they own that other people depend on**. If you get those wrong, either a paying team loses its workspace without warning, or you keep billing someone who thinks they left. Here's how I'd approach it. I haven't seen your codebase yet, so file names below are illustrative, and the first step is mapping the real schema.

## Questions I would ask

1. **What happens to workspaces the user owns that have other members?** This is the big one.
   *Default: block deletion until the user either hands ownership to another member or deletes the workspace themselves. The UI lists each blocking workspace with "Transfer" and "Delete workspace" actions. Workspaces where the user is the only member get deleted along with the account.*
2. **Who pays for team workspaces: the owner's personal Stripe customer, or a separate customer per workspace?**
   *Default: I'll check the schema. If the owner's card pays for a team, transferring ownership has to move billing too. If that isn't built yet, deleting is blocked until the workspace is deleted or billing is sorted out.*
3. **Cancel the subscription right away (with or without a prorated refund), or at the end of the current period?**
   *Default: cancel immediately, no refund. The account is going away, so there's nothing left to use for the rest of the period. Refunds stay a manual support decision.*
4. **Hard delete right away, or soft delete with a grace period?**
   *Default: soft delete with a 14-day grace period. The account is deactivated and the user is signed out immediately, then a scheduled job hard-deletes. That covers "I clicked it by accident" and gives Stripe/S3 failures time to retry.*
5. **Which records do you have to keep?** For example invoices for tax, audit logs, or anything under a legal hold.
   *Default: keep Stripe invoices (they live in Stripe). Keep audit-log rows but anonymise the user reference. Delete everything else.*
6. **Content the user created inside team workspaces** (files they uploaded, comments, documents). Delete it, or leave it with the team?
   *Default: it belongs to the workspace. It stays, and the author shows as "Deleted user". Only personal uploads go away.*
7. **Is GDPR/CCPA in scope**, and do you also need a "download my data" export?
   *Default: yes to deleting within 30 days (the grace period fits that). The export is a separate ticket.*

## Plan, under those defaults

### 0. Map what the user touches (before writing code)
- Go through the Postgres schema and list every table with a FK to `users`. Mark each one as **cascade delete**, **anonymise** (set the FK to null or to a "deleted user" placeholder), or **block** (workspace ownership).
- List every place outside Postgres that keys on the user: Stripe customer, S3 key prefixes, the auth provider (NextAuth/Clerk/Auth0?), the e-mail/marketing provider, analytics, error tracking.
- Check how S3 keys are laid out. If uploads live under `users/{id}/...` and `workspaces/{id}/...`, deletion is a prefix delete. If keys are flat, we need an `uploads` table to find the objects. If there's no such table, adding one comes first.

### 1. Schema
- `users.deleted_at timestamptz null` and `users.deletion_scheduled_for timestamptz null`.
- Auth checks treat `deleted_at IS NOT NULL` as "no access". Do this in one place: the session/middleware lookup.
- Migration with FK behaviour matching step 0. Prefer explicit app-level deletion over adding `ON DELETE CASCADE` everywhere, so nothing disappears by surprise.

### 2. Server: `DELETE /api/account` (or a server action)
In this order:
1. **Re-authenticate.** Require a fresh password, or a recent OAuth sign-in within the last few minutes. That stops a stolen session from deleting the account.
2. **Precondition check.** If the user owns workspaces with other members, return `409` with that list. Do the same check again inside the transaction to avoid a race with someone joining.
3. **Stripe:** cancel the user's active subscriptions with `prorate: false`, and record the cancellation. Do this before the DB changes so the user is never billed after we report success. Use an idempotency key, and handle "already cancelled".
4. **DB transaction:** set `deleted_at` and `deletion_scheduled_for = now() + 14 days`, delete sole-member workspaces, remove memberships in other workspaces, and revoke all sessions and API tokens.
5. Sign the user out (clear the cookie) and send a "your account is scheduled for deletion; reply/click to cancel" e-mail.
6. Write an audit-log entry.

### 3. Hard-delete job (cron / queue, runs daily)
For each user whose `deletion_scheduled_for < now()`:
- Delete their S3 objects (personal uploads only, per question 6). Batch the `DeleteObjects` calls (1000 keys max per call). Check whether the bucket has versioning turned on. If it does, delete the object versions as well, or set a lifecycle rule. Otherwise the "deleted" files are still there.
- Delete the Stripe customer, or leave it with metadata removed if invoices must stay tied to it. Your accountant should decide this one.
- Remove the user from the e-mail provider/analytics, using their delete APIs.
- Delete or anonymise the Postgres rows as mapped in step 0, then delete the `users` row.
- Each step has to be idempotent and safe to retry. If one step fails, the job tries again on the next run, and nothing gets half-deleted with no record. Alert if a user is stuck more than a few days past schedule.

Note that DB backups will still contain the user until they age out. That's normally acceptable under GDPR if you document your backup retention. It's a policy note, not code.

### 4. Cancel during the grace period
If a soft-deleted user signs in within the 14 days, show "Your account is scheduled for deletion. Restore it?" Restoring clears `deleted_at`. The subscription stays cancelled and they re-subscribe, which avoids un-cancelling in Stripe. Sole-member workspaces deleted in step 2 are gone, so either make that deletion soft too or say so clearly in the confirmation copy. *Default: soft-delete those workspaces as well and hard-delete them in the job.*

### 5. UI (Settings → Account → Danger zone)
- A red "Delete my account" button opens a dialog that:
  - lists exactly what happens: subscription cancelled now, personal files deleted after 14 days, contributions to team workspaces stay and show as "Deleted user";
  - lists blocking workspaces with Transfer/Delete links, and keeps the confirm button disabled until that list is empty;
  - asks for re-authentication and has a "type DELETE to confirm" field.
- After success, redirect to a signed-out "Account scheduled for deletion" page.

### 6. Edge cases to test explicitly
- The user owns a workspace with members: blocked. After transferring ownership: allowed.
- The user is the only member of their workspaces: those get deleted.
- A Stripe call fails: nothing in the DB changes, and the user sees an error they can retry.
- Stripe webhooks arriving after deletion (`customer.subscription.deleted`, `invoice.*`) mustn't crash on a missing or soft-deleted user.
- A pending workspace invite *to* the deleted user's e-mail, or *from* them.
- Signing up again with the same e-mail during the grace period and after it. *Default: blocked during the grace period (prompt to restore), allowed after.*
- Concurrent requests (double-click): idempotent.
- An admin "impersonate" or "support view" of a deleted user.

### Rollout
Ship behind a feature flag. Run the hard-delete job in dry-run mode (log only) for the first week on staging and production, and check what it *would* delete before turning it on for real.

---

If you can answer question 1 (and 2, if team billing hangs off the owner), I'll start with the schema map in step 0. That's where the real scope will show up.
