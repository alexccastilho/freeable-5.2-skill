# Gate, default and flag patterns

Sentence patterns to copy. Each has the condition under which it applies and an example quoted from the source traces. If the condition does not hold, leave the pattern out.

## Gates

Applies when a step touches production, data or other people. Does not apply to local, reversible work: a rename needs no go/no-go list.

### G1. Go/no-go list before an irreversible step

Pattern: a short list headed "All of these must be true", every item measurable.

> - Zero unexplained checksum differences for 7 consecutive days.
> - Replication lag under 1 second at peak for 7 days.
> - Cutover and rollback each rehearsed in staging at least twice, within the time budget.
> - Every writer to `users` accounted for and on the seam.
> - Backups restored successfully; on-call staff have the runbook.

Test for each item: could two people disagree about whether it is met? If yes, add the number or the observation.

### G2. Abort rule inside the step

Pattern: "If X has not happened within N, back out and leave the system on the old path."

> Put a hard timeout on the hold: if step 2 has not completed in, say, 15 seconds, release the hold with the flag still on MySQL and try another day.

This is the form most often missing. Write one for any step that holds, locks, pauses or freezes something.

### G3. Revert rule after the step

Pattern: "A change that does not <observable result> is reverted."

> A change that does not move its number is reverted.

Pair it with a scope rule when the work is open-ended: "Anything not on the list is left alone."

### G4. Proof of a diagnosis

Pattern: the step ends when the fault reproduces with the suspected cause present and does not with it absent.

> Step 2 ends with a cause I can demonstrate: re-running the load for one affected night in a staging copy reproduces the duplicates, and the same run with the suspected change reverted does not. If I cannot reproduce it, I do not have the cause yet.

"Ideally reproduced" is not a gate.

### G5. Stop criteria for a repeated rollout

Pattern: "Stop criteria for any wave: A, B, or C."

> Stop criteria for any wave: a verification mismatch, a cross-tenant result in any log or test, or shared-database latency above the agreed threshold.

### G6. Gate on a destructive step

Pattern: sign-off on the rule, a backup whose count is checked, the delete inside a transaction with a count check before commit, and a waiting condition before it starts.

> This step deletes production data, so it has its own safeguards and needs your sign-off on the rule before it runs.
> Before committing, check that the number of deleted rows equals the backup count and that the duplicate query from step 1 returns nothing.
> Cleanup runs after step 4 is deployed and one clean night has passed.

Prefer rename to drop, and state it: "rename it (do not drop yet)".

### G7. Loud failure for the case you may have missed

Pattern: remove the permission or path so a missed case fails instead of silently continuing.

> Revoke write privileges on `users` in MySQL for everything except the reverse-replication user, so a missed writer fails loudly instead of silently writing to the old store.

Do this at the cutover, not weeks later at decommission.

### G8. Limit of the rollback

Pattern: say where rollback stops being simple and what must exist before that point.

> Rollback is flipping the directory entry back. After the tenant has taken writes on the shared database, rollback needs a reverse export, so build and test that before wave 2.

## Rollout patterns to keep

These come from the baseline traces. The gates above do not replace them.

### R1. Observe-only before enforcement

Applies when limits, thresholds or rules are guessed.

> Deploy first in log-only mode (would-be-limited requests are logged, not blocked) for a day or two. Compare against normal traffic. Tune the numbers, then enforce.

Check that the system actually has an observe-only mode before you name one. If it does not, say what stands in for it (a shadow copy, a dry run, a staging replay).

### R2. Containment before diagnosis

Applies to incidents with damage still accumulating.

> Step 0: Contain (today). No manual backfills or re-runs until the cause is known; those can add more duplicates. Add a post-load check that fails the run, put a dedup view in front of consumers, and snapshot the affected rows before anyone cleans anything up.

Reason to state: cleaning first destroys the evidence.

### R3. Verify the built artefact

Applies when the work produces an output others consume.

> A link checker over the built output: every internal `href`/`src` must resolve to a file in the output folder under the base path.

## Defaults

Applies when an unknown would otherwise block the work. Does not apply to destructive actions, which wait for confirmation.

### D-a. Fail safe

Choose the default whose wrong guess does least damage or is noticed soonest. Check which way it fails. Example: trusting one proxy hop by default fails open when there is no proxy, because a client can then forge the forwarded address. Assuming no proxy fails visibly and is caught by one check.

### D-b. Expose it as a setting

> Default: the app is reached directly, with no proxy. The setting is exposed as `TRUST_PROXY` so it can be corrected without a code change.

For a cutover: "The flag must change without a deploy."

### D-c. Add the observation that settles it

> Before production: log `req.ip` for one real request in the deployed environment. If it shows a proxy address instead of the client's, set `TRUST_PROXY` before enabling the limits.

One concrete check the user or an operator can run replaces a question that might never be answered.

### D-d. Let the default shrink the change

> Do the warehouse staff share one office IP address? Default: yes. For that reason I have not put a strict limit on the shipping and import routes.

If a default makes part of the change risky, leave that part out and say why.

### D-e. Structure in place of an unknown number

| Unknown | Write | Do not write |
|---|---|---|
| Budget | "Not set. A percentage split is below; you supply the total." | A currency and a per-person figure |
| Performance target | "Targets proposed after the baseline." | "2.5 s at p75" with no measurement |
| Duration | Which phase is largest and what the estimate depends on | "4 to 6 months" before knowing who does the work |
| Tunable parameter the change needs | A value labelled as a guess, as a setting, with an observe-only stage | The value stated flatly |

A hedged number is still a number and will be quoted back.

### D-f. Say what the answers buy

> If you can answer questions 1 to 3 now, I can skip most of the broad measurement and go straight to profiling the screens you name, which would bring the first fix forward by several days.

And state that the plan runs without them: "a plan that starts with measurement and will work even if nobody answers them."

## Flags

Applies when the plan holds version-sensitive specifics, unrun code, or estimates resting on unseen facts. One sentence, next to the thing. Not for common knowledge.

### F1. Recalled specific

> The option names (`limit`, `standardHeaders`) are from version 7 of the library as I remember it. I would check them against the installed version's documentation before committing, since older versions used `max` instead of `limit`.

> To verify at implementation time: the current major versions of the Pages actions. I am not pinning these from memory.

### F2. Unrun code

First paragraph: "I have not changed anything yet. The code has not been run." Then at the weakest point:

> The count in the last three lines depends on the blocked request still counting toward the general limit. That is the first thing I would confirm when running it.

If you can run it, run it and report the result. The flag is for when you cannot.

### F3. Unseen facts

> I have not seen your schema, application or infrastructure, so the plan rests on the defaults in the next section.

### F4. Relative dates

> I am reading "last Tuesday" as 10 November 2026. If you mean 3 November, the steps are the same with a longer window.

Write the date into queries and schedules too; no `<last Monday>` placeholders when today's date is known.

## Order and loss

### O1. Reason for the order

> Cleanup comes after the fix on purpose: cleaning first would mean cleaning again after every night the faulty load runs.

> Send a save-the-date the day the contract is signed.

### O2. A standard step left out

> I would not move all reads to PostgreSQL ahead of writes. With heavy writes, any replication lag means a user updates their profile and then reads the old value.

### O3. What you lose, and what replaces it

Applies to changes of architecture or process only.

| Today, free with the current arrangement | Replacement to build |
|---|---|
| Restore one customer from backup | Per-tenant export and import tool |
| Delete a customer by dropping a database | Tenant deletion job covering every table, files, search and caches |
| One customer's heavy query hurts only them | Statement timeouts, per-tenant limits and monitoring |
| An outage affects one customer | An outage affects all: failover, staged rollouts |

Also ask what the fix will now hide:

> An alert when a run inserts zero rows or skips every file, since the idempotent load will now absorb a re-sent file silently.
