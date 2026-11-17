The button itself is an afternoon's work; what it triggers is where this can go wrong. I haven't seen your code, so this is a plan built on stated defaults. Three of those defaults are product decisions that should be confirmed before anything is built (questions 1–3 below).

## Questions I would ask

1. **What happens to a workspace the user owns that has other members?** Default: deletion is blocked until they transfer ownership or delete the workspace. Workspaces where they are the only member are deleted with the account.
2. **What happens to the Stripe subscription?** Default: cancel immediately, no automatic prorated refund, and say so in the confirmation dialog. This assumes the subscription belongs to the user; if it belongs to a workspace, it follows the workspace's fate under question 1.
3. **Immediate or with a grace period?** Default: the account is locked and hidden at once, then purged for good after 14 days; signing in during that window offers to cancel the deletion. The subscription is cancelled on day 0 either way.
4. **What must be kept for legal or accounting reasons?** Default: invoices and payment records stay in Stripe and in your billing tables, detached from the profile. Everything else personal is removed.
5. **What happens to content the user created inside other people's workspaces?** Default: it stays with the workspace, attributed to "Deleted user".
6. **Which other systems hold user data?** E-mail provider, analytics, support desk, error tracking. Default: only the e-mail list is handled in this change; the rest are listed for a follow-up.

## What the user sees

- **Placement:** a "Delete my account" button in account settings, in a danger zone at the bottom.
- **Blocked state:** if they own shared workspaces, the dialog lists them with links to transfer or delete each one, and the confirm button is disabled.
- **Confirmation:** the dialog states what will be deleted, that the subscription ends now, and the 14-day window. They confirm by typing their e-mail and re-authenticating (password, or a fresh OAuth sign-in).
- **Afterwards:** they are signed out everywhere and get a confirmation e-mail with the purge date and how to cancel.

## How it works

**Request (server action or `POST /api/account/delete`):**

1. Require a recent re-authentication.
2. In one transaction, re-check the workspace rule on the server, set `users.deletion_requested_at` and `purge_after`, and delete all of the user's sessions and API tokens.
3. Cancel the Stripe subscription. If Stripe fails, the request still succeeds and the job retries the cancel, so nobody is billed for an account they can't reach.
4. Send the confirmation e-mail.

**Auth check:** a user with `deletion_requested_at` set can only reach the "cancel deletion" screen. They are hidden from member lists and invitations.

**Purge job (daily, picks users past `purge_after`):** each step is safe to repeat and records its progress, so a failure halfway resumes instead of restarting.

1. Confirm the Stripe subscription is cancelled. Keep the Stripe customer for invoice history, or delete it if question 4 says so.
2. Delete the user's S3 objects and the objects of their sole-member workspaces. Check whether the bucket has versioning or replication; if so, old versions need deleting too.
3. Delete the sole-member workspaces, remove memberships elsewhere, and re-point authored content in shared workspaces to the "Deleted user" placeholder.
4. Delete the user row, or scrub it to a tombstone if billing rows must keep a foreign key.
5. Write an audit record with no personal data: user id, timestamps, and what was removed.

## Things that usually bite

- **Foreign keys:** every table that references `users` needs an explicit decision to cascade, null out, or reassign. I would list them from the schema first; a stray `ON DELETE CASCADE` could wipe shared workspace data, and a missing one will make the purge fail.
- **S3 keys:** if uploads aren't stored under a per-user or per-workspace prefix, the purge has to work from the uploads table. That must happen before those rows are deleted.
- **Stripe webhooks:** events such as `customer.subscription.deleted` and `invoice.*` will arrive after the user is locked or gone. The handlers must not throw on a missing user or re-activate the account.
- **Race on workspaces:** someone could be added to a "sole-member" workspace during the grace period. The purge job re-checks membership and stops for that user rather than deleting a shared workspace.
- **Backups:** deleted data lives on in Postgres backups until they rotate. That is normally acceptable, but the privacy policy should say so.
- **Re-registration:** the e-mail address becomes available again only after the purge.

## Order of work

1. Schema: deletion columns, the foreign-key audit, and the placeholder user.
2. Request endpoint, the lockout in the auth check, and session revocation.
3. Stripe cancellation and webhook hardening.
4. Purge job, including S3.
5. Settings UI, dialog, and e-mails.
6. Tests for the blocked-owner case, cancel during grace, purge resuming after a failed S3 or Stripe step, and a webhook arriving after deletion.

I would test the purge against a staging bucket and Stripe test mode before it runs on real accounts, since it is the only irreversible part.
