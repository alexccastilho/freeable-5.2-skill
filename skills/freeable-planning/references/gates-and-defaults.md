# Default-path, failure-coverage, gate, default and flag patterns

Sentence patterns to copy. Each has the condition under which it applies and an example from the source tasks. If the condition does not hold, leave the pattern out. A pattern that applies takes one line in the plan unless it holds the plan's main risk.

## Default path

Applies when the request names a solution and a cheaper route may reach the goal. The predicates are in SKILL.md step 3: (a) the requested path takes weeks or has a step a revert or flag cannot undo; (b) the cheaper path can be undone and leaves the requested path open; (c) the cheaper path delivers every stated outcome and you would recommend it for the most likely driver.

The quoted lines under P1 and P3 are constructed from the rule applied to a source task. No trace contains them: the reference trace for that task planned the requested design by default.

### P1. All three hold: the cheaper path is the plan

Opener pattern: "I plan <cheaper path> by default, because <requested path> takes <cost> and cannot be undone after <step>, and <cheaper path> gets <likely goal> and can be reversed. If <driver> is the reason, say so and the branch at the end applies."

Applied to the shared-database task (60 customers, one database each). Predicate (a) holds: the shared-table design takes months and merges 60 databases. Predicate (b) holds for a schema per customer inside one database: each schema can be dumped back out, record IDs do not change, and shared tables remain possible later. Predicate (c) holds if the driver is the cost of running 60 databases, which is the likeliest reading with no driver stated. So:

> Default: one database, a schema per customer. This removes most of the cost of running 60 databases, changes no record IDs, and can be undone per customer. If the driver is cross-customer features or growth to hundreds of customers, shared tables are needed: the branch below.

Branch pattern, six lines or fewer: the phases by name, the largest cost ("every foreign key, polymorphic reference and stored ID is rewritten"), the step after which it cannot be undone, and the answer that selects it.

### P2. A predicate fails: the request is the plan

Applied to the notes-to-website tool: building a small command-line tool takes days and nothing in it is irreversible, so (a) fails. The request stays the default.

> Existing static-site generators already do this. If the goal is only the result, say so and I will plan that route instead.
> Q1. Custom tool, or a thin setup around an existing generator? Default: custom tool, as requested.

Also the pattern when the user states the driver and the cheaper path does not serve it, or says the alternative was considered.

### P3. The cheaper path is a first stage

When the cheaper path is on the way to the requested one, write one plan in stages. The irreversible stage sits behind a decision gate that names its evidence.

> Phase 1 makes the application tenant-aware while each customer still has its own database. It ships to all 60 deployments with no visible change and is worth having whichever design follows. The merge starts only after question 1 is answered.

## Failure coverage

Applies to every change that will run in production, including the smallest. Scope restraint decides which features are built. It has no say over this list.

Run the standard failures of the kind of change and give each that applies one line, in the step it belongs to: the protection, or the reason it does not apply.

| Standard failure | Line from the source tasks |
|---|---|
| Many callers at the same moment | Rate limit: office staff behind one address share one bucket, so no strict limit on their routes |
| Expiry, retry, repeat | Nightly load: a task that inserts, fails late and retries; the load is made idempotent on the business key |
| Partial failure | Cutover: hold not complete in 15 seconds, release with the flag still on the old store |
| Stale or lost data | Migration: a read after a write would see the old value, so reads stay on the old store until writes move |
| Overload | Migration: PostgreSQL connections cost more than MySQL's, so the pool is sized before cutover |
| Several instances, or a dependency down | Rate limit: counters live in memory per process; correct for one process, and stated |
| A caller you did not know about | Migration: write privileges revoked at cutover so a missed writer fails loudly |

A line that says "does not apply: single process" is coverage. A missing line is a gap.

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

### D-f. Tolerances are asked, with a default and a branch

Applies when the unknown is how much of a bad thing is acceptable (staleness, delay, pause, loss). Take the default that fails safe, and write what the other answer changes.

> Is a hold of a few seconds on writes acceptable? Default: yes, once, about 10 seconds. If the answer is "no pause at all", the cutover changes to application dual-writes, which costs more and has more ways to diverge.

### D-g. Say what the answers buy

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

Applies to changes of architecture or process only. One line per item. Use the table when there are four or more items and the losses are the plan's main risk; otherwise one sentence.

| Today, free with the current arrangement | Replacement to build |
|---|---|
| Restore one customer from backup | Per-tenant export and import tool |
| Delete a customer by dropping a database | Tenant deletion job covering every table, files, search and caches |
| One customer's heavy query hurts only them | Statement timeouts, per-tenant limits and monitoring |
| An outage affects one customer | An outage affects all: failover, staged rollouts |

Also ask what the fix will now hide:

> An alert when a run inserts zero rows or skips every file, since the idempotent load will now absorb a re-sent file silently.
