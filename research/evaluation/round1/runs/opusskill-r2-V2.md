The button is the easy part. Most of the work is deciding what happens to the people and objects attached to the account: team workspaces the user owns that other people still use, a Stripe subscription that may be paying for those people, and S3 files that sit in shared workspaces. The second hard part is that deletion can't be undone. I recommend this design: the button schedules the deletion and immediately locks the account. A background job purges the data after a short grace period, in a fixed order, and can resume after a failure. The job runs in dry-run mode before it is allowed to delete anything.

Not seen: your schema, codebase, Stripe setup and S3 layout. The plan rests on the defaults below.

## Questions I would ask

1. **Is the subscription billed to the user or to a workspace?** Default: to a workspace, paid by its owner's Stripe customer. That is why ownership has to be dealt with before the account can go (question 2). If billing is strictly per user, cancelling the user's subscription is the whole billing step, and phase 2 shrinks.
2. **What happens to a workspace the user owns that has other members?** Default: deletion is blocked until the user transfers ownership, which includes billing, to another member, or deletes the workspace. A workspace where the user is the only member is deleted along with the account. If you want ownership to transfer automatically, it goes to the longest-standing admin and the payment method has to change too. That needs its own e-mail flow to the new owner, and a rule for when the workspace has no admin.
3. **Grace period or immediate deletion?** Default: 14 days, exposed as a setting (`ACCOUNT_DELETION_GRACE_DAYS`). Logging in during that time offers to cancel the deletion. If deletion must be immediate, the purge job runs right after the request and there is no restore path. Then the confirmation step in phase 1 needs to be stricter.
4. **Refund the unused part of the current billing period?** Default: no prorated refund. The subscription is cancelled at the end of the grace period, or at the end of the current billing period if that comes first.
5. **Do files a user uploaded into a shared workspace stay with the workspace?** Default: yes. They stay, and are attributed to "Deleted user". Only files in the user's personal space are deleted. If they must go with the user, other members lose content without warning, so they would need notice before the purge.

Answer first: 1 and 2. Together they decide whether phase 2 exists in its full form. Questions 3 to 5 change settings and wording only.

On timing: under GDPR, a deletion request generally has to be acted on within one month. That is why the default grace period is well below 30 days. I am recalling this rather than checking it, so confirm it with whoever handles your privacy obligations, and update your privacy policy text to match.

## Plan

### Phase 0: Inventory of what belongs to a user

Before writing any deletion code, list:

- Every Postgres table with a foreign key to `users`, or a user ID stored without one. For each table, choose delete, anonymize, or keep. My default is to keep the `users` row as a tombstone (personal data cleared, e-mail replaced with a random value) so that shared content in workspaces still points at a valid row. Rows belonging only to the user are deleted.
- The S3 key layout, whether bucket versioning is on, and any replication or backups. With versioning on, an ordinary delete only adds a delete marker. The purge has to delete every version.
- Every third party that holds the user's data: Stripe, your e-mail provider and marketing lists, analytics, error tracking, support tools.
- Data you must keep for legal reasons, such as invoices for tax. Keep the record and drop the personal data from it where the law allows.

Check: a written table of every data location and its action, signed off before phase 3 starts.

### Phase 1: Request flow (the button)

- Settings page, "Delete my account". The confirmation screen lists what will happen. It names any workspaces that block deletion, with links to transfer or delete them.
- Ask for the password again, or a recent login or SSO re-check, and have the user type a confirmation phrase.
- On confirm, in one database transaction: set `deletion_requested_at` and `deletion_scheduled_for`, and mark the account locked. Then revoke all sessions, API tokens and OAuth grants.
- Send an e-mail with the scheduled date and a link to cancel. Logging in during the grace period shows a "Cancel deletion" screen and nothing else.
- Stripe: set the subscription to cancel at the end of the period (`cancel_at_period_end`), so that cancelling the deletion can undo it.

Check: integration tests for a blocked owner, a sole-member workspace, cancel during the grace period, and old sessions rejected after the request.

### Phase 2: Workspace ownership and billing transfer

This exists only under the default answer to question 1. It covers the transfer-ownership action: the new owner accepts, the subscription's customer or payment method moves to the new owner, and the old owner's role drops to member. It is also useful without account deletion.

Check: after a transfer, the next invoice goes to the new owner. Confirm this with a Stripe test clock in test mode.

### Phase 3: Purge job

A scheduled job picks up accounts whose `deletion_scheduled_for` has passed. It works through the steps in this order and records each step as it completes, so a failed run resumes where it stopped:

1. **Re-check the blockers.** If the user owns a workspace that has other members, stop and alert. Membership can change during the grace period.
2. **Stripe.** Cancel any subscription that is still active, then delete the customer.
3. **S3.** Delete the user's personal objects, every version of them.
4. **Third parties.** Send deletion requests through each provider's API, or log them for manual handling.
5. **Postgres, last.** Delete rows that belong only to the user, and turn the `users` row into a tombstone.

The database goes last on purpose. It holds the Stripe IDs and S3 keys the earlier steps need, so deleting it first would leave orphaned files and live billing that nothing can find any more.

**Dry run first.** The job ships with `PURGE_MODE=dry_run`. In that mode it logs what it would cancel, delete and anonymize, with counts, and changes nothing.

### Rollout

1. Ship phases 1 and 2 behind a feature flag. Turn it on for staff accounts first, then everyone. Requests pile up safely, because nothing is purged yet.
2. Run the purge in dry-run mode against real scheduled requests, and against seeded staging accounts that cover each case.
3. Turn on real deletion only when the go/no-go list below holds.
4. Send a final e-mail when the purge completes, to an address captured before the tombstone overwrites it.

## Go / no-go before `PURGE_MODE=live`

All of these must be true:

- The phase 0 inventory is signed off, and every table on it is covered by the job.
- The dry run has covered at least 10 staging accounts across every case (sole owner, blocked owner, member only, personal and shared uploads, active, cancelled and no subscription). A person has checked every object it planned to delete.
- No dry-run log line plans to delete anything in a workspace that has other members.
- A purge of a staging account was interrupted halfway, then resumed and finished, with no orphans in S3 or Stripe.
- A database backup has been restored successfully within the last 30 days. Know how long backups keep deleted users' data, and state that period in the privacy policy.

**Abort rule inside the job:** if a single account's planned S3 deletions exceed the count recorded at request time by more than 20%, or touch a key outside that user's prefix, skip that account and alert. Don't delete. The same applies to a Stripe customer linked to more than one user.

**After go-live:** watch the first week of live purges. Any support ticket about missing shared content, or any invoice sent to a deleted customer, sets the mode back to `dry_run` while it is investigated.

## Need from you

- The schema, or at least the list of tables that reference users, and how workspaces and memberships are modelled.
- How Stripe customers and subscriptions map to users and workspaces.
- The S3 bucket layout, and whether versioning or replication is enabled.
- The list of third-party services that receive user data.
