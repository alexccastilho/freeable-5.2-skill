# "Delete my account": plan

The button is the easy part. The real work is deciding what "delete" means for things the user doesn't fully own. In your stack, three things make this more than `DELETE FROM users`:

1. **Team workspaces.** If the user owns a workspace other people belong to, deleting the account must not quietly delete everyone else's work, or leave a workspace with no owner and nobody who can pay for it.
2. **Stripe.** An active subscription has to be cancelled, or the user keeps being charged after the account is gone. That's the support ticket you least want. If the workspace is the subscriber, not the user, the answer changes again.
3. **S3 uploads.** These live outside Postgres, so no `ON DELETE CASCADE` reaches them. Deleting thousands of objects also doesn't belong in a web request.

Also, this is a one-way, destructive action. I'd build it as **"request deletion → short grace period → irreversible purge job"** rather than deleting everything in the click handler.

## Questions I would ask

1. **Workspace owned by the user, with other members: what happens?** Default: **block deletion** until the user transfers ownership or deletes the workspace themselves. The UI lists those workspaces with "Transfer" and "Delete workspace" actions. We never auto-transfer to some member.
2. **Who holds the Stripe subscription: the user or the workspace?** Default: per-workspace subscriptions billed to the owner. That's why the ownership block above also settles billing. Any subscription tied directly to the user is cancelled.
3. **Cancel immediately or at period end? Any refund?** Default: **cancel immediately, no prorated refund**, matching the usual terms of service. Easy to change if your terms say otherwise.
4. **Grace period?** Default: **14 days**. The account is deactivated right away, the user can sign in to restore it during the window, and then it's purged for good.
5. **What must we keep for legal/accounting reasons?** Default: keep invoices and payment records (Stripe keeps them anyway). Keep a minimal deletion audit row: hashed user id, timestamps, and no PII. Everything else, including PII, is deleted or anonymized.
6. **Content the user created inside shared workspaces (comments, documents, uploads in a team space)?** Default: **keep the content, anonymize the author** as "Deleted user". Deleting it would damage the team's data. Uploads in the user's *personal* space are deleted.
7. **Is this GDPR/CCPA-driven, with a deadline?** Default: yes, so the purge must finish within 30 days and also reach third-party processors: e-mail provider, analytics, error tracking.

## Plan

### Phase 1: Data audit (before writing code)
- List every table with a `user_id`-like column and decide for each one: **cascade-delete**, **anonymize** (set to NULL or a "deleted user" sentinel), or **retain**. Check the actual foreign keys. Any `ON DELETE CASCADE` from `users` to workspace-level tables is a trap, because deleting one user could wipe a shared workspace.
- List every S3 prefix keyed by user and check whether keys are namespaced per user (`users/{id}/...`) or per workspace. If personal uploads aren't under a user prefix, the purge needs a DB index of object keys.
- List third parties that hold user data: Stripe customer, e-mail/marketing tool, analytics, auth provider if external (NextAuth/Clerk/Auth0).

The output is a short table we agree on. Everything below follows from it.

### Phase 2: Schema
- `users.deletion_requested_at timestamptz`, `users.deleted_at timestamptz`.
- `account_deletions` audit table: `id`, `user_id_hash`, `requested_at`, `purged_at`, `status`, `error`.
- Partial index on `deletion_requested_at` for the purge job.

### Phase 3: Request flow (Next.js)
- **UI** (Settings → Account → Danger zone): a "Delete my account" button opens a confirmation dialog that:
  - Lists blocking workspaces, if any, with links to transfer or delete them. The confirm button stays disabled while any remain.
  - Spells out the consequences: subscription cancelled, personal files deleted, 14-day window to change their mind.
  - Requires typing the account e-mail (or "DELETE") **and** re-authenticating: password, or a fresh OAuth login / e-mail code for passwordless users.
- **Server action / API route `POST /api/account/delete`:**
  1. Auth check plus a fresh re-auth check. Never trust a client-side "confirmed" flag.
  2. Re-check ownership blockers on the server. Return 409 with the list if any exist.
  3. In one DB transaction: set `deletion_requested_at`, write the audit row, revoke all sessions and refresh tokens, and remove the user's pending invites.
  4. Cancel the Stripe subscription(s) via the API, with an idempotency key. If Stripe fails, roll back and show an error rather than deactivate a user who keeps getting billed. Also update the `stripe` webhook handler so a `customer.subscription.deleted` for a deactivated user doesn't error.
  5. Send a "your account is scheduled for deletion, here's how to undo it" e-mail.
  6. Sign the user out and redirect to a goodbye page.
- **Undo:** signing in during the grace window shows "Restore your account?". Restoring clears `deletion_requested_at`. The subscription stays cancelled and they re-subscribe, which keeps Stripe simple.
- Everywhere: users with `deletion_requested_at` set are blocked from login (except the restore flow), hidden from member lists and search, and can't be invited.

### Phase 4: Purge job (background, idempotent)
Run daily via cron / queue worker, not in a request. For each user past the grace period:
1. Re-check: still requested, and no newly owned shared workspaces. If one appeared, flag it for manual review instead of purging.
2. **S3:** list and batch-delete personal objects (`DeleteObjects`, 1000 per call). Handle versioned buckets by deleting versions too, or the data isn't really gone. Record progress so a crash resumes instead of restarting.
3. **Postgres**, in one transaction: delete the personal workspace and its data, anonymize authored content in shared workspaces, delete memberships, tokens, API keys, notification prefs, then scrub the `users` row (or delete it if FKs allow; see the audit table).
4. **Stripe:** delete the customer object, or keep it per question 5. Invoices stay in Stripe either way.
5. **Third parties:** call delete APIs for the e-mail tool and analytics, as listed in the audit.
6. Mark the audit row `purged_at`. Send the final "your account has been deleted" e-mail to the address captured before scrubbing.

Every step must be safe to re-run. Failures update `status/error`, and the job retries next run. Alert if any row has been stuck longer than N days, because of the legal deadline.

**Backups:** purged data still lives in Postgres backups and S3 versions until they age out. That's normally acceptable if the retention policy is documented (for example, 30 days). Confirm the backup retention matches what the privacy policy promises.

### Phase 5: Tests
- Unit/integration: the blocker check, the request endpoint (re-auth required, 409 on owned workspaces, sessions revoked, Stripe called with an idempotency key, rollback when Stripe fails), restore inside the window, login blocked after the request.
- Purge job against a seeded DB: personal data gone, shared-workspace content anonymized, other members' data untouched (**the most important assertion**), re-run is a no-op.
- S3 against LocalStack or a mocked client; Stripe in test mode.
- One manual end-to-end run in staging with a real Stripe test subscription.

### Rollout
1. Ship schema plus purge job in dry-run mode, which logs what it *would* delete. Review the logs.
2. Ship the UI behind a feature flag for internal accounts.
3. Turn on for everyone. Update the privacy policy / help-center article so it describes exactly what gets deleted and when.

## What I'd deliberately leave out of v1
- Self-service export ("download my data") before deletion. It's worth having, especially under GDPR, but it's separate work.
- Auto-transferring workspace ownership. Silently making someone else the owner (and payer) is worse than asking the user to choose.

If you can answer questions 1 to 3 (workspace ownership rule, who holds the subscription, cancellation terms), I'd start with the Phase 1 data audit. Those answers decide most of the rest.
