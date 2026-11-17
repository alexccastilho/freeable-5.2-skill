I have not seen the codebase, so this is a plan, not a change. The button is the small part. The work is in what deletion does to billing, files and workspaces that other people use, and several of those are product decisions. I've assumed a default for each so the plan is complete; correct any that are wrong before I build.

## Questions I would ask

1. **What happens to a workspace the user owns that has other members?** This is the one that can hurt other customers. Default assumed: deletion is blocked until the user transfers ownership or deletes the workspace. Workspaces where they are the only member are deleted with the account.
2. **Is there an undo window?** Default assumed: no. The account is disabled immediately and data is purged within minutes. A 7- or 30-day grace period is safer against accidents but means keeping personal data longer and deciding what happens to billing meanwhile.
3. **What happens to the Stripe subscription?** Default assumed: cancel immediately, no prorated refund, and keep the Stripe customer and invoices, since financial records usually have to be retained.
4. **What happens to content the user created inside other people's workspaces?** Default assumed: it stays with the workspace and the author shows as "Deleted user". Their uploads in those workspaces stay too.
5. **How does the user confirm?** Default assumed: type their e-mail address, plus a fresh login if the session is older than a few minutes. This also works for users who sign in with Google or similar and have no password.
6. **Which other systems hold their data?** Default assumed: out of scope for the first version, but listed for you: analytics, e-mail provider, support desk, error tracker, database backups.

## Plan

**1. Inventory first.** List every table with a foreign key to `users.id` and decide per table: delete, anonymise, or block. This is where most surprises are, so I'd bring the list back to you before writing the deletion code.

**2. Settings page.** A "Delete my account" button in a danger zone at the bottom of account settings. It opens a dialog that states what will be deleted, what will be cancelled, and that it cannot be undone. If the user owns shared workspaces, the dialog lists them with links to transfer or delete each, and the confirm button stays disabled.

**3. Request endpoint.** A server action or route handler that:
- re-checks the confirmation and the owned-workspace rule on the server;
- sets `deletion_requested_at` on the user, in a transaction, so they cannot log in again;
- revokes all sessions, API tokens and pending invitations they sent;
- enqueues the purge job and signs them out.

**4. Purge job.** Runs in the background, because Stripe and S3 can fail and a web request should not be the thing retrying them. Each step is safe to repeat:
- **Stripe:** cancel the user's subscriptions, and those of sole-member workspaces being deleted.
- **S3:** delete the user's objects and those of deleted workspaces. If the bucket has versioning on, old versions need deleting too, or a lifecycle rule.
- **Postgres:** in one transaction, delete or anonymise rows according to the inventory, then delete the user row. This comes last so a failed earlier step can still be retried against a user that exists.
- **Record:** keep a minimal log line (user id, time, outcome) with no personal data.
- **Confirmation:** send a final "your account was deleted" e-mail before the address is erased.

**5. Stripe webhooks.** Cancelling triggers `customer.subscription.deleted`, which will arrive for a user that no longer exists. The handler has to accept that quietly instead of failing and making Stripe retry.

**6. Tests.**
- Deletion is refused while the user owns a workspace with other members.
- After deletion: login fails, the e-mail address can sign up again, and other members' workspaces and content are intact.
- The purge job run twice ends in the same state.
- A Stripe or S3 failure leaves the job retryable and the user unable to log in.
- One end-to-end run in staging with Stripe test mode and a real bucket.

## What I need from the repo before starting

- Which auth library and ORM are in use, and how sessions are revoked.
- Whether a background job runner already exists. If not, the smallest option is a `deletion_requested_at` column polled by a scheduled function.
- How S3 keys are laid out. If they are not prefixed by user or workspace, the job has to look them up from the database before the rows are deleted.

## Risk

The whole feature is irreversible by design, so I'd ship it behind a flag, try it on test accounts in production, and only then turn it on for everyone.
