# Worked examples

Drawn from eight paired planning traces. "Baseline" is what a capable model wrote with no skill. "Target" is the shape this skill asks for. Where the baseline did something better, the target keeps it, and the example says so.

## 1. Migration: say where the work is

**Request:** "Migrate our `users` table (8M rows, heavy write traffic) from MySQL 5.7 to PostgreSQL 16 with zero downtime."

**Baseline.** Opens with the replication approach. The fact that only one table moves is raised in question 1 ("Any SQL JOIN between `users` and other MySQL tables stops working") and handled in a "Cross-cutting concerns" bullet after the cutover phase. Transactions that write `users` and another table together are never addressed. Reads move to PostgreSQL gradually before writes.

**Target.**

> Two things shape the plan more than the row count:
> - **Only `users` is moving.** Every foreign key, join and transaction that spans `users` and a table staying in MySQL stops working once `users` lives elsewhere. Untangling that is most of the effort, and it has to be done before any data moves.
> - **8M rows is small.** The backfill takes minutes to an hour. The risk is in the behavioural differences between the two databases and in the cutover, not in volume.

Then:

- Phase 1 is "Make the application ready (the bulk of the work)", shipped against MySQL with no behaviour change.
- "I would not move all reads to PostgreSQL ahead of writes. With heavy writes, any replication lag means a user updates their profile and then reads the old value."
- Cutover: "if step 2 has not completed in, say, 15 seconds, release the hold with the flag still on MySQL and try another day."
- A go/no-go list of seven measurable conditions.
- Write privileges revoked at cutover "so a missed writer fails loudly".

**Kept from the baseline:** weigh a reverse-fed read-only copy of `users` in MySQL, which keeps joins working and may shrink phase 1 for read paths. Encrypt the pipeline, since the table holds personal data.

**Not repeated from the reference trace:** "6 to 10 weeks". Say which phase is largest and what the estimate depends on.

## 2. Bounded change: smallest change, safe defaults

**Request:** "Add rate limiting to the shopmini API. We got hammered by a bot last week." Both models read all ten files.

**Baseline.** Four limiters, a new middleware file, an app-factory refactor, a new test dependency, an allowlist, a body-limit change. Default `trust proxy` of 1, which lets a client forge its address if there is no proxy. Ends: "Once you answer the deployment question, I'll implement steps 1-3."

**Target.**

> I have not changed anything yet. Below is the change I propose, with the code, and two questions whose answers could make a per-IP limit harmful if I guess wrong. The code has not been run.

- One source file changed, two limits, the built-in `fetch` for the test.
- "Is there a reverse proxy in front of the app? This matters more than anything else here. Default: the app is reached directly. The setting is exposed as `TRUST_PROXY` so it can be corrected without a code change."
- "Do the warehouse staff share one office IP address? Default: yes. For that reason I have not put a strict limit on the shipping and import routes."
- "Before production: log `req.ip` for one real request in the deployed environment. If it shows a proxy address, set `TRUST_PROXY` before enabling the limits."
- "The option names are from version 7 of the library as I remember it. I would check them against the installed version."
- Closing list: "The API has no authentication, including `/admin/shipments/import`. I have not touched this, but it is the larger exposure and worth its own piece of work."

**Kept from the baseline:** deploy in log-only mode for a day or two before enforcing, because the limits are guesses. Report the other findings too (order IDs can be enumerated; the import crashes on a malformed line), one line each, outside the diff.

## 3. Trivial change: no ritual

**Request:** "Rename the function `getUser` to `fetchUser` in shopmini."

**Baseline.** Correct diff, then a "Questions I would ask" section: whether to rename `getUserByEmail`, and whether to keep a deprecated alias. The second is answered by its own exploration two lines earlier ("not a published library, so there are no external callers").

**Target.** Four parts and no questions:

1. The edits: four lines in two files.
2. What was checked: no other references, no string access, "There is no existing `fetchUser` to collide with."
3. What was left alone: "`getUserByEmail` keeps its name, since you asked for `getUser` only. Say if you want it renamed to `fetchUserByEmail` too."
4. Verification: a whole-word search expecting no matches, then `npm test`. "I have not run the tests: the fixture has no installed dependencies and I could not modify it."

## 4. Incident: contain first, then prove, then gate

**Request:** "Since last Tuesday our nightly ETL job has been producing duplicate rows in the `transactions` table. Plan how to fix this."

Neither trace had all of this. The target combines them.

| Part | Source | Text |
|---|---|---|
| Date | reference | "I am reading 'last Tuesday' as 10 November 2026. If you mean 3 November, the steps are the same with a longer window." |
| Step 0, contain | baseline | "Don't run manual backfills or re-runs until the cause is known. Add a post-load check, put a dedup view in front of consumers, snapshot the affected rows before anyone cleans anything up." |
| Proof | reference | "If I cannot reproduce it, I do not have the cause yet." (Baseline: "ideally reproduced in a dev environment".) |
| Destructive gate | reference | "This step deletes production data, so it needs your sign-off on the rule before it runs." Runs "after step 4 is deployed and one clean night has passed". |
| Order | reference | "Cleanup comes after the fix on purpose: cleaning first would mean cleaning again after every night the faulty load runs." |
| What the fix hides | reference | "An alert when a run inserts zero rows, since the idempotent load will now absorb a re-sent file silently." |
| Evidence source | baseline | Ask whether the vendor files are still retrievable; reconcile cleaned totals against them. |

## 5. Shorter cases

| Task | Baseline | Target |
|---|---|---|
| Notes folder to a static site | "It's worth checking whether one of them already fits before building this" as the last risk bullet | First paragraph: existing tools do this; "If the goal is only the result, say so and I will plan that route instead." Question 1: "Custom tool, or a thin setup around an existing generator? Default: custom tool, as requested." Full plan follows. |
| "Make our app faster" | Two lists of "usual suspects" under a fix phase | A table "If the measurements show / Likely causes / Typical fix", labelled "hypotheses to confirm against the measurements, and not a list of work to do". "A change that does not move its number is reverted." Targets are proposed after the baseline, as the baseline model did. |
| Two-day offsite in three months | Save-the-date in week 1, venue signed in weeks 2-3; a dollar budget table built on an assumed per-person figure | "Sign the venue and room block by the end of week 2. This is the one deadline that matters. Send a save-the-date the day the contract is signed." Budget: "Not set. I give a percentage split below; you supply the total." Keep the baseline's contract terms (attrition clause, minimums). |
| Single-tenant to shared database | Schema-per-customer dismissed in one clause; primary-key choice left conditional | "Before committing, check one thing: what the goal is. If it is mainly to cut the cost of running 60 databases, a schema per customer inside one database gets most of that for a fraction of the work." A verdict per key option, one recommended. A "what you lose, and what replaces it" table. Keep the baseline's per-customer configuration and secrets, and ask team size before estimating. |
