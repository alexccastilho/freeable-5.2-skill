The button is the easy part. Two other things decide whether this is safe:
- **Shared workspaces.** Deleting a user must never quietly delete a workspace that other people work in.
- **A deletion that can be finished.** The account's data lives in Postgres, S3 and Stripe, and the delete has to be complete and able to resume across all three.

So I recommend splitting it in two. The button disables the account right away and schedules it. A purge job then removes the data after a grace period. The job is built and run in dry-run mode before it deletes anything.

I have not seen your schema, auth setup, S3 key layout or Stripe model, so the plan rests on the defaults below. The first phase exists to replace them with facts.

**Cheaper path, if the goal is mainly compliance or the occasional request.** The button could create a deletion request: a row plus a support ticket, with the account disabled at once. Someone then works it by hand from a runbook within the legal deadline (GDPR allows one month). That costs a day or two instead of the purge job, and is the right choice while requests are rare. It turns into the automated version later without throwing work away, because the inventory in phase 0 is the runbook. I plan what you asked below.

## Questions I would ask

1. **Self-serve automated deletion, or a request that support carries out?** Default: automated, as asked.
2. **What happens to workspaces the user owns that have other members?** Default: deletion is blocked until the user transfers ownership or deletes each such workspace explicitly. The dialog lists them, each with a link. Workspaces where the user is the only member are deleted with the account. If you would rather transfer ownership automatically (for example to the longest-standing admin), the block becomes a transfer step inside the request. That needs a rule for workspaces with no other admin.
3. **Is billing per user, per workspace, or both?** Default: each user and each workspace can have its own Stripe subscription.
   - The user's personal subscription is cancelled immediately when they confirm, with no prorated refund. Refunds are a setting (`ACCOUNT_DELETE_REFUND=none|prorate`).
   - Workspace subscriptions are covered by question 2: the workspace is either handed over, and its billing with it, or deleted, and its subscription cancelled.
4. **How long a grace period, and can the user undo it?** Default: 30 days, set by `ACCOUNT_PURGE_AFTER_DAYS`. During that time the account is locked, and support can restore it from a link in the confirmation e-mail. If you need immediate deletion, set it to 0. The purge then runs within minutes and nothing else changes.
5. **What must be kept: invoices, tax records, audit logs, abuse reports?** Default: billing records are anonymised, not deleted (amount, date, country, Stripe invoice id, no name or e-mail). Invoices also stay in Stripe. Everything else that identifies the person is deleted.

Answer first: 2 and 3. Question 2 is the one decision that can destroy other people's data. Question 3 decides which Stripe objects the job touches.

Also assumed:
- Content the user created inside other people's workspaces (comments, documents, files) stays with that workspace, credited to "Deleted user".
- Personal uploads are deleted.
- If that is wrong for your product, phase 0 is where it changes.

## Plan

### Phase 0: Inventory (before any code)

Build a deletion map: every place the user exists, and the action for each one (delete, anonymise, transfer, keep).
- **Postgres:** every table with a foreign key to `users`, plus columns holding an e-mail or user id without a foreign key (logs, audit, invitations, analytics events).
  - Record each constraint's `ON DELETE` rule. In particular, if `workspaces.owner_id` references `users` with `ON DELETE CASCADE`, a plain `DELETE FROM users` already wipes team workspaces today. Find that before writing anything.
- **S3:** which key prefixes belong to a user versus a workspace. Also whether the bucket has versioning, replication or lifecycle rules, because a delete on a versioned bucket only adds a delete marker.
- **Stripe:** customer and subscription objects per user and per workspace.
- **Third parties:** the auth provider (NextAuth/Auth.js tables, or Clerk/Auth0 if used), the e-mail provider's contact lists, analytics, error tracking.

Check: a seeded test user with a row in every table and an object under every prefix. The map lists each of those locations.

### Phase 1: The request flow (ships alone and is reversible)

- **Settings → Danger zone → "Delete my account".** Opens a dialog that:
  - asks the user to sign in again (password, or a one-time e-mail code for OAuth users);
  - lists what will be deleted and what stays (content in shared workspaces);
  - lists blocking workspaces with transfer or delete links, and keeps the button disabled while any remain;
  - asks the user to type their e-mail to confirm.
- **Server action:**
  - Check the block again on the server; never trust the dialog.
  - In one transaction, set `users.deleted_at` and `purge_after`, and revoke all sessions and API tokens. Then cancel the personal Stripe subscription with an idempotency key tied to the user id.
  - Record a `account_deletions` row (user id, requested at, status, step reached).
  - Send the confirmation e-mail with the restore link.
- **Locked accounts:** login, API auth and invitations reject `deleted_at IS NOT NULL`. Workspace member lists show the person as "Deleted user" immediately.

Check: e2e tests for the blocked case, the re-auth requirement, and that sessions die (an old cookie gets a 401). Stripe is checked in test mode: the subscription shows as cancelled.

### Phase 2: The purge job (dry run first)

A scheduled job (cron or queue worker) picks rows whose `purge_after` has passed and works through them in this order:
1. **S3 objects.** List by the user's prefixes plus the keys referenced in their rows, then delete in batches, all versions if versioning is on.
2. **Postgres.** Delete and anonymise in one transaction, following the map.
3. **Stripe customer.** Delete or redact it, per question 5.
4. **Third parties.**
5. **Mark complete.** Reduce the `account_deletions` row to an id hash plus timestamps.

**Why S3 goes first:** the database rows are the index to the files. Delete them first and any object you missed can never be found again.

Each step records progress, so a crash resumes where it stopped instead of starting over. The e-mail address becomes free to register again only after step 2.

**Rollout:**
- Run with `PURGE_MODE=dry-run` for at least one full grace-period cohort. The job logs exactly what it would delete per account, and a person compares that log with the phase 0 map for a few accounts.
- Then switch to `enforce`.

**Abort rules inside the job:**
- If an account still owns a workspace with other members, skip it and alert. This should be impossible after phase 1, so it means a bug.
- If one run would purge more accounts than `PURGE_MAX_PER_RUN`, stop the whole run and alert. Set the cap after seeing dry-run volumes, not before.
- If any step errors for an account, leave it at the step it reached and alert. Never skip ahead.

### GO / NO-GO before switching the purge to `enforce`

All of these must be true:
- The dry-run log matches the phase 0 map for at least five real accounts, checked by someone other than the author.
- The seeded test user is purged in staging, and afterwards a query of every mapped table and S3 prefix finds zero identifying rows or objects, apart from the anonymised billing rows.
- Deletion of a user who belongs to, but does not own, a shared workspace is tested in staging. The workspace and its other members' data are unchanged.
- No `ON DELETE CASCADE` from `users` to a shared table remains (or it has been changed to `RESTRICT` or `SET NULL`).
- Backups are known to hold deleted data for N days (your retention), and the privacy policy says so.

**Limit of rollback:** until a user's purge runs, restore is clearing `deleted_at`. After it runs, the only way back is a database backup restore, which does not bring back S3 objects that had no versioning. That is why the grace period and the dry run come first.

## Need from you

- The database schema (Prisma schema, Drizzle files or SQL migrations).
- How auth is done.
- The S3 bucket settings: versioning, lifecycle.
- Whether Stripe customers belong to users or to workspaces.
- Any legal retention requirements from your privacy policy or contracts.
