# Delta analysis: Fable 5.2 versus Opus 5.5 planning traces (E1–E8)

Sources: `extraction/tasks.md`, the 16 files in `extraction/traces/`, `extraction/analysis/fable-self-report.md`, and `fixtures/shopmini/`. All 16 traces were read in full. The fixture was read to check the code-level claims in E2 and E7.

## 0. Verdict and limits of this analysis

**The two models are close. Most of the difference is in emphasis, ordering and restraint, and little of it is in content.** On every task both models produced the same skeleton: a short framing, a block of clarifying questions each carrying a default, a phased plan, and a request for the two or three answers that matter most. On E3, E4 and E6 the plans would be hard to tell apart with the names removed. A skill that teaches "ask questions with defaults, explore first, phase the work, verify, plan rollback" would transfer nothing, because Opus already does all of it.

The deltas that do recur are narrow:

1. Fable opens by saying where the real work or the real decision is, including when that contradicts the surface reading of the request. Opus tends to put the same observation late or in a side section.
2. Fable proposes the smaller change and keeps adjacent findings out of the diff. Opus widens the change.
3. Fable writes stop, abort and go/no-go conditions with numbers. Opus writes exit criteria less often and more softly.
4. Fable marks what it recalled from memory and what it could not know, and declines to invent some numbers. Opus states recalled specifics flatly.
5. Fable drops ritual on the trivial task. Opus kept a questions section on a four-line rename.

Limits that weaken every claim below:

- **One sample per task per model.** No repetition, so no variance estimate. A count of "3 of 8 versus 0 of 8" is a pattern in 16 documents, and could be noise.
- **Advisor confound.** Each Fable batch of four tasks included one advisor call. Any Fable-only move may have come from the advisor and not from Fable. The traces do not record what the advisor said, so this cannot be separated. The moves most exposed to this are the top-of-plan reframings in E5 and E8.
- **Format was probably imposed by the prompt.** The header "Questions I would ask" and the "Default:" convention appear verbatim in 15 of 16 traces across both models. I treat the question-with-default format as given by the task prompt, and not as a behaviour of either model.
- **Analyst bias.** I am Fable 5.2 judging Fable 5.2. I have tried to count against myself, and section 4 is long for that reason. A blind grading by a third model would be more trustworthy than my "which is better" calls.
- **No plan was executed.** "Better for the user" is a judgement about text. Neither model's plan was tested against reality.

Size of each response, process log excluded:

| Task | Fable words | Opus words | Fable ÷ Opus |
|---|---|---|---|
| E1 greenfield tool | 1,266 | 1,010 | 1.25 |
| E2 brownfield feature | 1,240 | 1,118 | 1.11 |
| E3 incident | 1,760 | 1,368 | 1.29 |
| E4 vague request | 1,222 | 895 | 1.37 |
| E5 migration | 1,989 | 1,630 | 1.22 |
| E6 offsite | 1,154 | 1,155 | 1.00 |
| E7 trivial control | 295 | 419 | 0.70 |
| E8 multi-tenant | 1,920 | 1,631 | 1.18 |

Fable is 10 to 37% longer on every real planning task and 30% shorter on the trivial one. Fable's largest plan is 6.7 times its smallest; Opus's is 3.9 times. Fable is not the more concise model. It is the one with the wider spread.

---

## 1. Per-task pair comparison

### E1 — Markdown notes to GitHub Pages CLI

**Fable did, Opus did not**
- Opened with the build-or-buy question before anything else: "existing tools already do this (MkDocs, Quartz, Eleventy, Hugo)... If the goal is only the result, say so and I will plan the MkDocs route instead." It then planned the custom tool anyway "because that is what you asked for". Opus has the same thought as the third bullet of Risks, at the bottom: "It's worth checking whether one of them already fits before building this."
- Made that the first question, with the request as its default: "Custom tool, or a thin setup around an existing generator? Default: custom tool, as requested."
- Flagged recalled specifics: "To verify at implementation time: the current major versions of the Pages actions... I am not pinning these from memory."
- Tied a check to each build step: "Each step ends with something you can run", and marked the cut line: "Steps 1 to 6 are the usable product. Steps 7 and 8 can follow." A real deployment is step 6, ahead of `serve` and packaging.
- Gave the reason inside the privacy question: "A Pages site is readable by anyone on the internet, in most plans even when the repository is private."
- Stated what would reverse a decision: raw HTML is passed through, and "This would change if the tool ever built content from other people."

**Opus did, Fable did not**
- A link checker over the built output: "every internal `href`/`src` must resolve to a file in `dist/` under the base path". This is the best single verification idea in either E1 response.
- A source-file layout (`cli.ts`, `scan.ts`, `links.ts`...), deterministic output, sitemap, `CNAME` from config, and a build summary line ("published 132 notes, skipped 7 drafts").
- Slug collisions as "a hard error that names both files". Fable resolves to the nearest note and warns, which is the weaker choice by its own argument ("Silent guessing here would produce links that go to the wrong page").
- Raw HTML off or sanitised by default. Defensible, and the opposite of Fable's call.

**Better for the user:** Fable, narrowly. The build-or-buy question at the top can save the user the whole project, and Opus buried it. Opus's testing section is stronger and should not be lost.

### E2 — Rate limiting in shopmini

Both read all ten files of the fixture. Both found the same core facts: no authentication, so IP is the only key; no `trust proxy`; SMTP awaited inside `POST /orders`; one process with SQLite, so an in-memory store is right. I checked these against the fixture and they hold.

**Fable did, Opus did not**
- Delivered the change itself: the full `server.js`, a new test file, the `package.json` line. One source file changed, two limits, no new test dependency, no refactor. Stated plainly: "I have not changed anything yet... The code has not been run."
- Chose defaults so that a wrong guess is cheap, and turned each into a switch: "Default: the app is reached directly, with no proxy. The setting is exposed as `TRUST_PROXY` so it can be corrected without a code change." The warehouse default ("Do the warehouse staff share one office IP address? Default: yes") drove a conservative design: "For that reason I have not put a strict limit on the shipping and import routes."
- Replaced a question with a check the user can run: "log `req.ip` for one real request in the deployed environment... This check is what prevents the limit from blocking everyone."
- Marked its own uncertain points: "The option names... are from version 7 of the library as I remember it. I would check them against the installed version's documentation"; "That is the first thing I would confirm when running it"; "the numbers below are guesses".
- Verified the plan against how the tooling works: "`node --test` runs each file in a separate process, so the low limits set here do not affect `orders.test.js`."
- Verification with expected values: "the first 20 return 200, the rest return 429, and the `orders` table has 20 new rows."
- Kept adjacent problems out of the diff, under "Limits of this change": "I have not touched this, but it is the larger exposure and worth its own piece of work."

**Opus did, Fable did not**
- A log-only rollout: "Deploy first in **log-only mode**... for a day or two... so we don't lock out the warehouse at end-of-day import time." With guessed limits this is the safer way to ship, and Fable has no equivalent.
- Found more: order-ID enumeration on `GET /orders/:id`, that `bulkImport.js` "crashes on a malformed line and skips `updated_at`" (both true in the fixture), and default body-size limits.
- An IP allowlist, logging of each limit hit, and a test that separate IPs get separate buckets.
- Widened the change: four limiters, a new `src/middleware/rateLimit.js`, an app-factory refactor of `server.js`, `supertest`, a body-limit change. Limits were tighter and equally unmeasured ("10 / 15 min per IP" on orders).
- Blocked on an answer: "Once you answer the deployment question... I'll implement steps 1–3." Its default (`trust proxy` 1) fails open if there is no proxy, since a client can then spoof `X-Forwarded-For`.

**Better for the user:** Fable, moderately. The user was attacked last week and asked for a change. Fable hands over a small reviewable diff that can ship while the questions are open. Opus hands over a five-step project that waits for an answer. Opus's log-only rollout and wider findings are real advantages.

### E3 — Duplicate rows from the nightly ETL

The two plans share a structure: characterise the duplicates with a query and a pattern-to-cause table, find what changed, make the load idempotent (staging table, processed-files table, `ON CONFLICT`), clean up with a survivor rule and a foreign-key check, add detection.

**Fable did, Opus did not**
- Resolved the date: "I am reading 'last Tuesday' as 10 November 2026. If you mean 3 November, the steps are the same with a longer window." Opus left `'<last Monday>'` placeholders.
- A hard standard of proof for the diagnosis: "Step 2 ends with a cause I can demonstrate: re-running the load for one affected night in a staging copy reproduces the duplicates, and the same run with the suspected change reverted does not. If I cannot reproduce it, I do not have the cause yet." Opus: "ideally reproduced in a dev environment".
- Gated the destructive step: "This step deletes production data, so it has its own safeguards and needs your sign-off on the rule before it runs"; "check that the number of deleted rows equals the backup count" before committing; cleanup only "after step 4 is deployed and one clean night has passed".
- Gave the reason for the order: "Cleanup comes after the fix on purpose: cleaning first would mean cleaning again after every night the faulty load runs."
- Saw a side effect of its own fix: "An alert when a run inserts zero rows or skips every file, since the idempotent load will now absorb a re-sent file silently."
- A section "What would change this plan" with three conditions.

**Opus did, Fable did not**
- **Contained first.** "Step 0: Contain (today)": no manual backfills or cleared tasks until the cause is known, a post-load check, a dedup view for consumers, and a snapshot of affected rows "before anyone cleans anything up". Its opening line carries the reason: "deleting rows first destroys the evidence." Fable's stop step is step 3, after diagnosis, and Fable never tells the user to hold off on re-runs.
- Asked whether the vendor files are still retrievable ("Check retention before relying on that"), and reconciled cleaned totals "against vendor file totals".
- `max_active_runs=1`; delete-and-insert by partition as an alternative; a pattern row for duplicates inside a single file.

**Better for the user:** a tie. Opus is better for the first hour of an incident (contain, preserve evidence). Fable is better at the two points where the plan could do harm (declaring a cause without proof, deleting rows).

### E4 — "Make our app faster"

The plans are nearly the same: seven questions, then measure, choose targets, fix, re-measure, add regression guards. Both say the fix list is conditional on measurement.

**Fable did, Opus did not**
- Said the plan runs without answers: "a plan that starts with measurement and will work even if nobody answers them."
- Said what the answers buy: "If you can answer questions 1 to 3 now, I can skip most of the broad measurement and go straight to profiling the screens you name, which would bring the first fix forward by several days."
- Wrote the fixes as an observation-to-cause-to-fix table, labelled "hypotheses to confirm against the measurements, and not a list of work to do". Opus wrote two lists of "usual suspects" under Phase 2, with a one-line caveat.
- A revert rule and a scope rule: "A change that does not move its number is reverted"; "Anything not on the list is left alone."
- A section "What I would not do" with three items and a reason each.
- Segmented measurement by customer account, so "an improvement in the average that leaves the largest customers behind is visible".

**Opus did, Fable did not**
- Asked for the repository ("Can I see the repo(s)? I don't have the code here").
- Declined to invent targets: "I'll propose targets after the baseline." Fable supplied default targets (2.5 s at p75, 300 ms at p95, 200 ms) with no basis in this app. Opus's position is the more honest one.
- Named tools throughout, flagged tenant isolation in cache keys, and proposed feature flags for rollout.
- 27% shorter for the same plan.

**Better for the user:** Fable, slightly. The difference is the conditional table and the revert rule. It is small.

### E5 — `users` table from MySQL 5.7 to PostgreSQL 16, zero downtime

Both chose snapshot plus binlog change capture, verification by range checksums and shadow reads, a held-write cutover of a few seconds, and reverse replication for rollback. Both offered dual-writes only if no pause is allowed.

**Fable did, Opus did not**
- Relocated the effort at the top: "Two things shape the plan more than the row count: **Only `users` is moving.** Every foreign key, join and transaction that spans `users` and a table staying in MySQL stops working... Untangling that is most of the effort, and it has to be done before any data moves... **8M rows is small.**" This became a whole phase ("Phase 1: Make the application ready (the bulk of the work)"), shipped "against MySQL, with no behaviour change, before PostgreSQL holds any data". Opus raised the same issue in question 1 and then handled it in a "Cross-cutting concerns" bullet near the end. Opus never addressed transactions that write `users` and another table together.
- Refused a standard step with a reason: "I would not move all reads to PostgreSQL ahead of writes. With heavy writes, any replication lag means a user updates their profile and then reads the old value." Opus has a gradual read-migration phase, with a caveat.
- An abort condition on the cutover: "Put a hard timeout on the hold: if step 2 has not completed in, say, 15 seconds, release the hold with the flag still on MySQL and try another day."
- A go/no-go list of seven measurable conditions ("Zero unexplained checksum differences for 7 consecutive days... Cutover and rollback each rehearsed in staging at least twice").
- A mechanism to surface unknown writers at cutover: "Revoke write privileges on `users` in MySQL for everything except the reverse-replication user, so a missed writer fails loudly." Opus revokes at decommission, weeks later.
- "rename it (do not drop yet)" before the final drop.

**Opus did, Fable did not**
- A cheaper answer to the cross-engine joins: "keep a read-only replica of `users` in MySQL fed by the reverse stream (which also keeps the JOINs working)". This could remove much of Fable's phase 1 for read paths. Fable did not consider it.
- Security of the pipeline: "`users` almost certainly holds PII. Encrypt the Kafka topics or DMS channel".
- Build secondary indexes after the bulk load; drop stale events by source position; size the sink for three times peak; a week-by-week timeline.
- Held writes are "reject or queue... with client retries", which is looser than Fable's "held (not failed)".

**Better for the user:** Fable, clearly. This is the largest gap in the set. Fable's plan puts most of the calendar where most of the work is. Opus's read-only replica idea is good and Fable missed it.

### E6 — Two-day offsite for 40 people

Near-identical: same questions, same week-by-week timeline, same agenda shape, same after-event steps.

**Fable did, Opus did not**
- One fixed deadline, stated as such: "**Sign the venue and room block by the end of week 2.** This is the one deadline that matters."
- Ordered by dependency: "Send a save-the-date the day the contract is signed." Opus sends the save-the-date with dates in week 1 and signs the venue in weeks 2–3, so dates are announced before the venue confirms them.
- Declined to invent a budget: "Not set. I give a percentage split below; you supply the total." Opus assumed "USD 600 to 900 per person" and built a dollar table on it, with no information on currency, country or seniority.
- Ranked the questions: "The first four questions change the plan the most, so answer those first if you can."
- Resolved the date: "mid-February 2027".
- Contingency items: a date poll before signing, "Name a second person who can run the event if the organiser is ill", "decide in advance which session is cut first".

**Opus did, Fable did not**
- Venue contract terms: "watch the **attrition clause**... the cancellation schedule, the food-and-beverage minimum"; "Negotiate the guaranteed number at about 85% of 40"; "Hold a second-choice date if you can."
- An hour-by-hour agenda and a request-for-proposal process.
- Asked about sharing rooms: "Ask; many people prefer single rooms."

**Better for the user:** Fable, slightly, for the ordering and the refusal to invent the budget. Opus knows more about venue contracts. A user who wanted a rough cost figure would prefer Opus.

### E7 — Rename `getUser` to `fetchUser` (control)

Both did the right thing: searched, found the same four occurrences in two files, showed the diff, noted `getUserByEmail` was left alone, and gave a grep plus `npm test` as verification. I confirmed the four occurrences in the fixture.

**Fable did, Opus did not**
- No questions section. The one open point is a note: "That leaves the module with one `fetch` and one `get` name. Say if you want it renamed."
- Checked for a name collision: "There is no existing `fetchUser` to collide with" (the log shows a case-insensitive search for `get_?user|fetch_?user`).
- Gave the reason tests were not run: "the fixture has no installed dependencies and I could not modify it."

**Opus did, Fable did not**
- Kept a "Questions I would ask" section with two questions. The second ("Keep a deprecated `getUser` alias for compatibility?") is answered by its own exploration two lines earlier ("not a published library, so there are no external callers").
- Checked the package is an application and not a library. Fable did not state this.
- Warned against blind find-and-replace, added a module-load smoke test, and mentioned a commit message.

**Better for the user:** Fable, slightly, and the difference is mostly style: 295 words and no ritual against 419 words and two questions nobody needed. Opus did not over-plan to a harmful degree. Both read all ten files for a rename; for Fable that was shared with the batch.

### E8 — Single-tenant Rails to shared multi-tenant database

Both chose row-level tenancy with `acts_as_tenant` or `Current.tenant` plus PostgreSQL row-level security, both ship the tenant-aware code to the 60 separate databases first, both migrate in waves starting with internal tenants, and both keep a dedicated-database option. Opus calls the code-first step "the most important trick"; Fable calls it "the key sequencing decision". **This is not a delta.**

**Fable did, Opus did not**
- A summary with the recommendation in the first sentence.
- Questioned the goal before the plan: "Before committing, check one thing: **what the goal is.** If it is mainly to cut the cost of running 60 databases, a schema per customer inside one database gets most of that for a fraction of the work." Opus dismissed that option in one clause ("doesn't scale well and the Apartment gem is effectively abandoned") and added "as you asked".
- Committed on primary keys, with an option Opus did not list: a per-tenant ID offset, "**Recommended.**", composite keys "Too invasive." Opus's answer is conditional: option (a) "*unless* public URLs and APIs expose IDs widely. In that case go with (b)."
- Named where the ID work hides: "polymorphic `*_id` columns, IDs inside JSON or serialised columns, audit and version tables, Active Storage attachments, queued job arguments, search indexes, caches, and external systems such as a billing provider's metadata."
- A table "What you lose, and what replaces it": single-customer restore, deletion by dropping a database, noisy-neighbour isolation, outage blast radius. Opus mentions three of these in different places.
- Stop criteria for waves: "a verification mismatch, a cross-tenant result in any log or test, or shared-database latency above the agreed threshold."
- Honest about the limit of rollback: "After the tenant has taken writes on the shared database, rollback needs a reverse export, so build and test that before wave 2."
- A risk Opus did not list: "The project stalls halfway", answered with "Each phase leaves a working system."

**Opus did, Fable did not**
- Per-customer configuration and secrets: "Move per-customer config (env vars) into a `tenant_settings` table". Sixty deployments certainly have per-customer SSO, SMTP and API keys. Fable missed this entirely.
- Collapsing 60 deployments into one, an external penetration test, updating the DPA and security documents.
- Asked team size and timeline. Fable gave "4 to 6 months for a small team" without asking.
- The reverse tool's other uses: dedicated hosting later, offboarding, data export.
- One doubtful statement: "Enable RLS policies in **permissive/log mode first**". PostgreSQL has no log-only mode for row-level security, and "permissive" in PostgreSQL means something else. Stated without a flag.

**Better for the user:** Fable, moderately. The goal check, the committed key strategy and the loss table are worth more than the items Fable missed. The per-customer configuration gap is a real omission in Fable's plan.

### Scoreboard

| Task | Better | Margin | What decided it |
|---|---|---|---|
| E1 | Fable | narrow | Build-or-buy at the top |
| E2 | Fable | moderate | Smaller, shippable change; safe defaults |
| E3 | tie | — | Opus contains first; Fable gates proof and deletion |
| E4 | Fable | slight | Conditional fix table, revert rule |
| E5 | Fable | clear | Put the effort where the work is |
| E6 | Fable | slight | Dependency order; no invented budget |
| E7 | Fable | slight, stylistic | No ritual |
| E8 | Fable | moderate | Goal check, committed decision, loss table |

Read this table with the limits in section 0 in mind, especially analyst bias. Only E5 is a margin I would expect an independent grader to reproduce reliably.

---

## 2. Catalogue of delta moves

Counts are "number of the 8 tasks in which the move appears". Where Opus does a weaker form, both the strong and weak counts are given. A move is listed only if Fable's count exceeds Opus's by at least two, or the difference changed the outcome of a task.

### D1. Say where the work is

**Do:** Before the questions, write one to three sentences that name the one or two facts that determine most of the effort or risk. Test them against the request's surface: if the request emphasises a number or a technology ("8M rows", "zero downtime", "multi-tenant"), ask whether that is where the difficulty is. If it is elsewhere, say so and give that part of the plan its own phase, sized to match.

**Evidence:** E5 "Two things shape the plan more than the row count... Untangling that is most of the effort"; E6 "only if the venue and dates are fixed in the first two weeks. Everything else can be adjusted later"; E8 "The key sequencing decision is to make the application tenant-aware while each customer still has its own database"; E3 "The duplicates started on a specific day, which means something changed on or just before that day."

**Count:** Fable 4 (E3, E5, E6, E8). Opus 2 as an opener (E3 "deleting rows first destroys the evidence", E6 venue on the critical path); in E5 Opus has the observation ("The hard part is the change stream and the cutover, not the volume") inside question 6 and does not restructure the plan around the cross-table problem.

**Apply when:** the plan has more than one phase. **Do not apply** to small changes, and do not manufacture a contrarian insight when the surface reading is correct.

### D2. Offer the cheaper path first, then plan what was asked

**Do:** If a materially cheaper way reaches the likely goal (an existing tool, a less invasive architecture), put it in the first paragraph: what it is, what it costs, when it is the right choice, and the one condition under which you would switch. Make it question 1 with the user's request as the default. Then write the full plan for what was asked. Do not wait for an answer.

**Evidence:** E1 "If the goal is only the result, say so and I will plan the MkDocs route instead" plus question 1 "Default: custom tool, as requested"; E8 "If it is mainly to cut the cost of running 60 databases, a schema per customer inside one database gets most of that for a fraction of the work... I assume below that you want real shared tables."

**Count:** Fable 2 at the top (E1, E8). Opus 0 at the top; 1 buried in a risk list (E1), 1 dismissed in a clause (E8).

**Apply when:** the request names a solution, and a cheaper one exists that a reasonable user might not have considered. **Do not apply** when the user has already shown they chose deliberately, when the alternative is only marginally cheaper, or more than once per plan. Never withhold the requested plan.

### D3. Smallest change; findings go in a list, not in the diff

**Do:** Propose the fewest files, limits, dependencies and refactors that satisfy the request. Problems found during exploration that the request does not cover go in a short closing section, each with one sentence on why it matters and the statement that it was not touched. If a default makes one part of the change risky, leave that part out and say why.

**Evidence:** E2: one source file, two limits, built-in `fetch` for the test ("No new test dependency is needed"), "For that reason I have not put a strict limit on the shipping and import routes", "I have not touched this, but it is the larger exposure and worth its own piece of work". Opus E2: four limiters, a new middleware file, an app factory, `supertest`, an allowlist, a body-limit change. E7: no alias, no commit discussion. E1: no sitemap, no `CNAME` handling, no source tree; "A plugin system is out of scope."

**Count:** Fable 3 (E1, E2, E7). Opus widened the change in 2 (E1 mildly, E2 clearly), and added ritual in 1 (E7).

**Apply when:** changing an existing system. **Do not apply** as a reason to omit safety measures for the change itself (see section 4: Opus's log-only rollout is in scope, and Fable should have had it).

### D4. Stop, abort and go/no-go conditions with thresholds

**Do:** For each risky step write the observable condition that halts or reverses it, with a number where one exists. Three forms: (a) a go/no-go list before an irreversible step, all conditions measurable; (b) an abort rule inside the step ("if X has not happened in N seconds, back out and leave the system on the old path"); (c) a revert rule after it ("a change that does not move its number is reverted"). For a diagnosis, the condition is a reproduction with the suspected cause present and absent.

**Evidence:** E5 "if step 2 has not completed in, say, 15 seconds, release the hold with the flag still on MySQL and try another day" and the seven-item go/no-go list; E8 "Stop criteria for any wave: a verification mismatch, a cross-tenant result in any log or test, or shared-database latency above the agreed threshold"; E4 "A change that does not move its number is reverted"; E3 "If I cannot reproduce it, I do not have the cause yet" and "one clean night has passed"; E2 "If it shows a proxy address instead of the client's, set `TRUST_PROXY` before enabling the limits."

**Count:** Fable 5 (E2, E3, E4, E5, E8). Opus 2 with a threshold (E5 "zero unexplained mismatches for 7 consecutive days", E2 log-only then enforce), 1 soft (E3 "ideally reproduced"). Opus has no abort-inside-the-step rule in any trace.

**Apply when:** a step touches production, data, or other people. **Do not apply** to local, reversible work; a rename does not need a go/no-go list.

### D5. Defaults that fail safe, exposed as a switch, with a check that settles them

**Do:** For each unknown, choose the default whose wrong guess does the least damage or is easiest to correct. Make the assumption a configuration value where the work allows. Where possible, add one concrete observation that settles the question without the user ("log `req.ip` for one request"). Design the rest so work can begin before the answer arrives. If you cannot know a number, give a structure that works for any value and do not invent the value.

**Evidence:** E2 `TRUST_PROXY`, the `req.ip` check, env-var limits; E6 "Not set. I give a percentage split below; you supply the total"; E4 "will work even if nobody answers them"; E3 "Default: the vendor supplies a stable ID per transaction. Step 1 tests this before anything relies on it"; E5 "The flag must change without a deploy."

**Count:** Fable 5 (E2, E3, E4, E5, E6). Opus 2 (E5 "Default: unknown. Phase 0 checks it"; E4 "What I'd do first if you just say 'go'"). Opus counter-examples: E2 blocks on the answer and picks a default that fails open; E6 invents a currency and a per-person budget.

**Apply when:** an unknown would otherwise block the work. **Do not apply** to destructive actions, which wait for confirmation whatever the default (Fable E3 step 5). Fable broke its own rule in E4 by inventing performance targets.

### D6. Mark what was recalled, not run, or not seen, at the point it applies

**Do:** When a specific comes from memory and could be out of date (a library option name, an action version, a configuration key), say so once, next to it, and name the check that settles it. When code was written and not run, say that in the first paragraph and point at the assertion most likely to be wrong. When an estimate rests on unseen facts, say which facts.

**Evidence:** E1 "I am not pinning these from memory"; E2 "from version 7 of the library as I remember it... older versions used `max` instead of `limit`", "That is the first thing I would confirm when running it"; E5 "treat that as a guess until the phase 0 inventory is done"; E7 "I have not run the tests: the fixture has no installed dependencies"; E8 "I have not seen the codebase."

**Count:** general "I have not seen your system" statements: Fable 6 (E2, E3, E5, E7, E8, and E1 for versions), Opus 4 (E2, E3, E4, E7). The specific sub-move of flagging a recalled technical detail: Fable 2 (E1, E2), Opus 0. Opus states `standardHeaders: 'draft-7'`, `snapshot.mode=initial` and an RLS "log mode" without qualification; the last appears to be wrong.

**Apply when:** the plan contains version-sensitive specifics or unrun code. **Do not apply** to common knowledge, and do not scatter hedges; one sentence at the point of use.

### D7. Rank the questions and say what each answer changes

**Do:** Keep the question list, and add two things. Next to a question whose answer changes the structure, write the branch ("If the answer is no, the cutover changes to dual-writes, which costs more"). At the top or the end, name the two to four questions worth answering first and what answering them buys.

**Evidence:** E2 "This matters more than anything else here"; E4 "If you can answer questions 1 to 3 now, I can skip most of the broad measurement"; E5 "If the answer to question 2 is 'no pause at all', the cutover changes to application dual-writes" and "answers to questions 1, 2 and 4"; E6 "The first four questions change the plan the most"; E8 "the answers to questions 1, 2 and 4"; E3 "If corrections exist... the fix becomes an update on conflict instead of a skip."

**Count:** Fable 6 (E2, E3, E4, E5, E6, E8). Opus 3 (E2 "Once you answer the deployment question", E5 "questions 1, 2 and 4", E8 "the decision I would most want to settle with you early").

**Apply when:** more than three questions are asked. This is a moderate delta; Opus does it half as often.

### D8. Zero ritual on trivial tasks

**Do:** If the change is a handful of lines, fully specified, and reversible: no questions section, no plan. Show the change, list what was checked, note anything deliberately left alone as a one-line offer, give the verification. Any section the template suggests is dropped if it has nothing in it. A question whose answer you already found by looking is not asked.

**Evidence:** E7 Fable has no questions; "Say if you want it renamed to `fetchUserByEmail` too." Opus E7 keeps "Questions I would ask" and asks about a deprecated alias after establishing there are no external callers.

**Count:** 1 task tests this. Fable 1, Opus 0. The spread in length (section 0) supports it: Fable is the only one that got shorter than Opus as the task got smaller.

**Apply when:** the "just do it" conditions hold. This is one data point, and Opus's failure was mild.

### D9. Put concrete values where the user gave relative ones

**Do:** Convert "last Tuesday", "in three months" and similar into a date, state the reading, and give the other reading in one clause if it is plausible.

**Evidence:** E3 "I am reading 'last Tuesday' as 10 November 2026. If you mean 3 November, the steps are the same with a longer window"; E6 "mid-February 2027".

**Count:** Fable 2 (E3, E6; the only two tasks with relative dates). Opus 0 ("<last Monday>", "about 12 weeks from now").

**Apply when:** the request has a relative date or quantity and today's date is known. Small, cheap, mechanical.

### D10. Give the reason for the order

**Do:** Where the sequence is not obvious, or where a reader would be tempted to reorder, write one sentence with the reason. Place communication and announcements after the commitment they depend on. Say explicitly when a standard step is being left out and why.

**Evidence:** E3 "Cleanup comes after the fix on purpose"; E6 "Send a save-the-date the day the contract is signed"; E5 "I would not move all reads to PostgreSQL ahead of writes" and "Why change capture rather than application dual-writes"; E1 "built for every note before anything is rendered, because link rewriting depends on it".

**Count:** Fable 4 (E1, E3, E5, E6). Opus 2 (E3 opening; E1 "Links need the second pass because..."). Opus has one ordering error (E6 save-the-date before the venue is signed).

**Apply when:** the plan has dependent steps. Weak-to-moderate delta.

### D11. Account for what the end state takes away

**Do:** For a change of architecture or process, list what the current arrangement gives for free that the new one will not, and what must be built to replace each item. Also ask what the fix itself will now hide.

**Evidence:** E8 the table "What you lose, and what replaces it"; E3 "the idempotent load will now absorb a re-sent file silently"; E5 "PostgreSQL connections are costly compared with MySQL's, and an application sized for MySQL can exhaust them" and integrity moving to the application with "a periodic orphan check to replace what the constraint gave you".

**Count:** Fable 3 as an explicit accounting (E3, E5, E8). Opus 1 gathered in one place (E8, in the risk table and Phase 4), with the same items mentioned individually in E5.

**Apply when:** migrations and architectural changes. **Do not apply** to features and small changes.

### Considered and rejected as deltas

These appear in Fable's traces and equally in Opus's. A skill should not spend words on them.

| Move | Fable | Opus | Note |
|---|---|---|---|
| Questions each with a default | 7 of 8 | 8 of 8 | Probably imposed by the prompt |
| Explore the repository before planning | 2 of 2 | 2 of 2 | Both read every file |
| Measure before optimising | E4 | E4 | Identical |
| Characterise before diagnosing; pattern-to-cause table | E3 | E3 | Identical |
| Make the code tenant-aware before moving data | E8 | E8 | Opus calls it "the most important trick" |
| Reverse replication for rollback | E5 | E5 | Identical |
| Idempotent load plus unique constraint after cleanup | E3 | E3 | Identical |
| Explicit out-of-scope list | E1, E2, E7 | E1, E2, E7 | Identical |
| Loud failure for unknown cases (`--strict`, raise without tenant) | E1, E3, E5, E8 | E1, E3, E8 | Near-identical |
| Human sign-off on business decisions | E3, E4 | E2, E3, E4 | Identical |
| Risk table at the end of large plans | E1, E5, E6, E8 | E1, E5, E6, E8 | Same four tasks |
| Verification section | 8 of 8 | 8 of 8 | Fable puts checks inside steps in E1 only |
| Closing ask for specific artefacts | E5, E8 | E3, E5, E8 | Opus slightly more often |

---

## 3. Shape differences

**Length.** See the table in section 0. Fable is longer on seven of eight tasks. The extra length is mostly tables and a few extra sections ("What would change this plan", "What I would not do", "What you lose", "Go / no-go"). Any skill that says "be more concise like Fable" would be teaching something false.

**Structure.** Fable uses more headings on large tasks (E8: 17 against 9) and more tables (E8: 36 table rows against 15; E4: 14 against 0). Fable puts questions in a two-column table, "Question | Default I am assuming", on E5, E6 and E8. Opus uses numbered lists with bold defaults throughout. Fable uses a "Summary" section on the two largest tasks (E5, E8); Opus uses an opening paragraph.

**Ordering.** Fable's order on large tasks: verdict or key insight, then what it has not seen, then questions, then design decisions, then phases, then gates, then risks, then what it needs. Opus's order: framing, questions, decisions, phases, timeline, risks, next step. The difference is the first item and the gates. Opus includes a timeline table on E3, E5, E6 and E8; Fable on E3, E4 and E6.

**Where the questions go.** Both put them immediately after the opening, before the plan, in every task that has them. In E2 both put them after "what I found". Neither model stopped to wait for answers; both planned on defaults. Fable additionally refers back to question numbers inside the plan and at the end (E3, E4, E5, E8). Opus does so in E5 only.

**Number of questions.** Fable: 7, 5, 6, 7, 7, 8, 0, 8. Opus: 7, 5, 6, 7, 7, 7, 2, 8. Identical apart from E6 and E7. Neither model is restrained here.

**How defaults are stated.** Fable: "Default: X", often followed by the design consequence ("so the tool must handle a base path", "For that reason I have not put a strict limit on..."). Opus: "Default: **X**" in bold, more often followed by a justification of why X is likely ("That's the most common pattern for a B2B SPA"). Fable's defaults more often say what the plan does about them; Opus's more often say why they are probable. Fable admits ignorance as a default three times ("Default: unknown, to be found in step 2"; "Not set"; "Default: unknown, so I measure..."); Opus twice.

**Proportionality.** Covered under D8 and section 0. Fable's spread is wider. On the middle task (E2) Fable changed the form of the answer, delivering code and a test where Opus delivered a five-step plan.

**Tone.** Fable is plainer and flatter: declarative sentences, almost no bold inside prose, no greetings. "This is the one deadline that matters." "8M rows is small." Opus is warmer and more emphatic: "Happy to help, but...", "This is the most important trick", bold on key phrases, arrows ("measure → pick → fix"), parenthetical asides. Opus addresses the user's situation a little more ("B2B customers dislike regressions more than slowness"). Neither tone is better for plan quality. This is style and should not be a skill target.

**First-person commitments.** Fable more often states what it will and will not do ("I would not move all reads...", "I have not touched this", "I would bring the table to you for this choice"). Opus more often states what should be done ("Use Rails multi-database...", "Negotiate the guaranteed number...").

---

## 4. What Opus did better, and where Fable over-did it

A skill must not remove these Opus behaviours.

**Opus better**

1. **Containment before diagnosis (E3).** Step 0 with a freeze on re-runs, a snapshot for evidence and a dedup view for consumers. Fable had no equivalent and placed "stop new duplicates" third. For incidents, Opus's order is the right one.
2. **Staged rollout for guessed parameters (E2).** Log-only mode before enforcement. Fable shipped guessed limits straight to enforcement with a manual check.
3. **Breadth of discovery in the code (E2).** Order enumeration, the `bulkImport.js` crash on malformed lines and missing `updated_at`, body limits. Fable found fewer adjacent problems. Reporting them costs little as long as they stay out of the diff.
4. **Verification of the built artefact (E1).** The output link checker. Fable's per-step checks are good; this is better than any one of them.
5. **Operational and organisational items (E5, E8).** PII in the replication pipeline, per-customer secrets and configuration, collapsing deployments, the DPA, an external penetration test. Fable's plans are more technical and missed these.
6. **Cheaper alternatives inside the plan (E5).** A reverse-fed read-only copy of `users` in MySQL to keep joins working. Fable's phase 1 may be larger than necessary.
7. **Domain specifics in non-software work (E6).** Attrition clause, food-and-beverage minimum, holding a second date.
8. **Asking about resources (E4, E8).** "Can I see the repo(s)?" and "Team size and timeline?" Fable gave an estimate in E8 without asking who would do the work.
9. **Declining to invent targets (E4).** "I'll propose targets after the baseline."
10. **Length.** The same plan in 10 to 37% fewer words on seven tasks.

**Fable over-did or got wrong**

1. **Too many questions.** Seven or eight on most tasks, against a self-reported norm of zero to three. E1 question 7 ("How large is the folder?") has an almost certain default and should have been a stated assumption. E6 has eight.
2. **Invented numbers where it had no basis.** E4 performance targets; E2 "300 per minute" and "20 per minute" (flagged as guesses, still unmeasured); E8 "4 to 6 months for a small team"; E5 "6 to 10 weeks". The hedges are present, and the numbers will still be quoted back.
3. **Unrun code presented in full (E2).** About 60 lines of code and test that were never executed, with a test assertion that depends on middleware behaviour Fable says it "expects". Flagged honestly, and still a risk if a reader pastes it.
4. **More structure than content needs.** E6 has twelve headings and seven tables for a plan that Opus delivered at the same length with less scaffolding. Risk tables appear on the same four tasks as Opus's, which suggests template habit in both.
5. **A weaker choice than its own argument (E1).** Resolving an ambiguous wikilink to the nearest note with a warning, after arguing against silent guessing. Opus's hard error is cleaner.
6. **Gaps in its own area of strength.** E3 never says "do not re-run or backfill until the cause is known". E8 never mentions per-customer configuration.

**Risks if the delta moves are taught carelessly**

- D2 over-applied turns into second-guessing every request. Limit it to one paragraph, once, with the requested plan still delivered.
- D3 over-applied drops safety measures. Scope restraint applies to features, never to rollout safety or verification.
- D4 and D11 over-applied add gates and tables to small tasks. They belong to production and data work only.
- D6 over-applied produces hedging everywhere. One flag at the point of use.
- D1 over-applied produces a forced "the real problem is elsewhere" opener when the request is what it appears to be.

---

## 5. Self-report check

Status meanings: CONFIRMED means seen in Fable's traces. "Not a delta" means Opus does it equally. UNOBSERVED means these tasks could not show it or the traces do not record it.

| # | Claim in `fable-self-report.md` | Status | Evidence |
|---|---|---|---|
| 1 | §1: Trivial, local, reversible change gets no plan; do it and report | CONFIRMED, weak delta | E7: no questions, 295 words. Opus also did it, with two unneeded questions |
| 2 | §1: Five classifying questions run in order before planning | UNOBSERVED | Internal; the traces show outputs only. The report itself doubts this in §10 |
| 3 | §1: Irreversible or shared work gets a written plan with rollback and explicit confirmation | CONFIRMED, not a delta | E3 step 5 "needs your sign-off"; E5; E8. Opus: E3 "after a backup/snapshot", E5, E8 |
| 4 | §1: Scope words ("all", "clean up") trigger planning; one correction triggers a re-read | UNOBSERVED | No task contains these conditions |
| 5 | §2: Go up one level to the real goal; use it to disambiguate and flag, not to enlarge scope | CONFIRMED, delta in placement | E1 opening, E8 "what the goal is", E4 question 1. Opus does it later or more briefly |
| 6 | §2: Deliver the scope asked for even when a different approach looks better | CONFIRMED, delta | E1 "because that is what you asked for"; E2 "I have not touched this" |
| 7 | §2: Fixed list of hidden requirements (conventions, unhappy paths, operations, audience) | PARTLY CONFIRMED, not a delta | E2 follows the existing test style; E1 covers unhappy paths. Opus equally (E1 slug collision, E2 separate-IP test) |
| 8 | §2: Challenge a premise when the request names a solution | CONFIRMED, delta | E1, E8. See D2 |
| 9 | §2: Treat an asserted cause as a hypothesis | UNOBSERVED | No task asserts a cause. E3 "this plan does not name a cause" is consistent with it |
| 10 | §2: Challenge in one or two sentences and do not withhold the work | CONFIRMED | E1, E8: one paragraph each, full plan follows |
| 11 | §3: Look before asking | CONFIRMED, not a delta | E2 and E7: both models read the repository and asked nothing answerable from it, except Opus E7 question 2 |
| 12 | §3: Ask only when not discoverable, costly if wrong, and plan-changing; decide the rest | CONTRADICTED in number, partly confirmed in kind | 5 to 8 questions on seven tasks. Some are low-stakes (E1 Q7, E6 Q7). The format may have been imposed |
| 13 | §3: "Usually zero to three" questions | CONTRADICTED | 7, 5, 6, 7, 7, 8, 0, 8 |
| 14 | §3: Each question concrete, with a proposed answer | CONFIRMED, not a delta | Identical convention in Opus |
| 15 | §3: The question that can cancel others comes first; goal before scope before detail | CONFIRMED, weak delta | Fable E1 Q1, E4 Q1 "What prompted this?", E5 Q1, E6 Q1, E8 Q1. Opus E5, E6, E8 also; Opus E1 starts with language, E4 with symptoms |
| 16 | §3: Defaults chosen by: existing code, earlier conversation, ecosystem convention, easiest to reverse, smaller scope | PARTLY CONFIRMED, delta on the last two | E2 `express-rate-limit` (convention), `TRUST_PROXY` (reversible), no strict admin limit (smaller). See D5 |
| 17 | §3: Default stated as "I assumed X because Y. Say so if you want Z" | CONFIRMED in substance | E7 "Say if you want it renamed"; E1 "say so and I will plan the MkDocs route". The exact wording is not used |
| 18 | §3: Vague requests: often skip asking and show two or three directions | CONTRADICTED | E4 asks seven questions and offers one plan. The plan is built to work unanswered, which is a different move |
| 19 | §3: In autonomous runs, take the reversible default and continue | CONFIRMED | Every task was planned on defaults without stopping. Opus the same, except E2's closing line |
| 20 | §3: Catalogue of questions by task type | PARTLY CONFIRMED | Several appear nearly verbatim ("What prompted this?", "Who reads `transactions`?", downtime tolerance, "Who decides"). Many catalogue items never appear. See section 7 for what was asked |
| 21 | §4: Exploration order (instructions, layout, landing site, analogous example, callers, tests, history, working tree) | PARTLY CONFIRMED, not a delta | E2/E7: file listing, then every file, `git status`, a caller search. The repository is ten files, so order and stopping cannot be judged. Opus ran `git log` |
| 22 | §4: Read an analogous existing feature and copy its shape | UNOBSERVED | The fixture has no analogous middleware. The new test does copy the existing test's setup lines |
| 23 | §4: Baseline test run before changes | CONTRADICTED / not done | E7 "I have not run the tests"; E2 "The code has not been run". The fixture was read-only, so this is not a fair test |
| 24 | §4: Stop exploring when files, changes and verification can be named | UNOBSERVED | Repository too small to tell. Fable read all files for a rename |
| 25 | §5: Each piece checkable alone and leaving a working system | CONFIRMED, weak delta | E1 "Each step ends with something you can run"; E8 "Each phase leaves a working system". Opus E1 has a separate testing section |
| 26 | §5: Thin end-to-end slice first | CONFIRMED, not a delta | E1 step 1 "Skeleton and happy path". Opus E1 step 1 is the same |
| 27 | §5: Refactoring separated from behaviour change | CONFIRMED, weak delta | E5 phase 1 "with no behaviour change"; E8 phase 1 "no visible change". Opus E8 the same; Opus E2 mixes an app-factory refactor into the feature |
| 28 | §5: The thing most likely to invalidate the plan goes first; spike it | WEAKLY CONFIRMED, not a delta | Phase 0 inventories in E5 and E8 (Opus too). No spike appears. In E1 the real deployment is step 6 |
| 29 | §5: Irreversible steps late; removal of the old thing last and separate | CONFIRMED, not a delta | E3 cleanup after fix; E5 "rename it (do not drop yet)"; E8 phase 5. Opus the same |
| 30 | §5: Decision gates written into the plan | CONFIRMED, delta | E4 table, E5 go/no-go, E8 stop criteria. See D4 |
| 31 | §5: Alternatives only when the choice is real; recommend one with the main trade-off | CONFIRMED, weak delta | E8 key table with verdicts; E5 change capture against dual-writes. Opus presents alternatives too, and is conditional on the E8 key choice |
| 32 | §5: Bias to the simplest approach and to doing less | CONFIRMED, delta | E2. See D3 |
| 33 | §6: Four risk questions per step, including "what if it half-finishes" | PARTLY CONFIRMED | Half-finish cases: E3 "a failure midway followed by a retry", E5 hold timeout. A per-step pass is not visible |
| 34 | §6: Pre-mortem on the whole plan | UNOBSERVED | Not stated. E8 "The project stalls halfway" reads like one |
| 35 | §6: Second-order effects checked | CONFIRMED, weak delta | E3, E5, E8. See D11. Opus does a scattered version |
| 36 | §6: Verification written inside each step | PARTLY CONFIRMED | E1 and E3 yes. E2, E4, E7 use a separate verification section, as Opus does |
| 37 | §6: Reproduce a bug first; the reproduction is the verification | CONFIRMED, delta in strictness | E3 "If I cannot reproduce it, I do not have the cause yet". Opus "ideally reproduced" |
| 38 | §6: State what could not be verified | CONFIRMED, weak delta | 6 of 8 for Fable, 4 of 8 for Opus. See D6 |
| 39 | §6: Backup before a destructive step, with a check that it is usable | CONFIRMED, not a delta | E3 "confirm its count matches"; E5 "Test a restore". Opus E3 snapshot and dry run |
| 40 | §6: Name the point of no return; say plainly if there is no way back | PARTLY CONFIRMED | E8 "After the tenant has taken writes... rollback needs a reverse export". The phrase is not used; E5 avoids the point by reverse replication |
| 41 | §7: The plan leads with what the reader must decide | CONFIRMED, delta | D1, D2 |
| 42 | §7: Medium plans are 150 to 400 words | CONTRADICTED | E2 is 1,240 words. No Fable plan other than E7 is under 1,100 |
| 43 | §7: No section exists because a template has it | PARTLY CONTRADICTED, not a delta | Risk tables on E1, E5, E6, E8, the same tasks as Opus. E3 and E4 have none, which supports the claim |
| 44 | §7: No code unless the exact text matters | CONTRADICTED on E2 | Full file and full test. Arguably correct, since E2 asked for a change |
| 45 | §7: No time estimates unless asked | CONTRADICTED | E3 days, E4 days, E5 "6 to 10 weeks", E8 "4 to 6 months". Hedged each time |
| 46 | §7: Steps name real things | CONFIRMED, not a delta | E2 and E7 cite files and lines in both models |
| 47 | §7: Length follows decisions and risk, not typing | CONFIRMED, weak delta | Wider spread than Opus (section 0) |
| 48 | §8: Counter-move table | Mixed | The rows on scope, premises, gates and proportionality are confirmed as deltas. The rows on looking first, rollback, baseline and thin slices are confirmed and not deltas |
| 49 | §9: "State assumptions where the reader will see them: at the top" | CONFIRMED, not a delta | Both put questions and defaults before the plan |
| 50 | §9: "Count the things before deleting them, and show the count" | CONFIRMED | E3 step 5. Opus has a dry-run count too |
| 51 | §10: "I likely ask fewer questions than this report implies" | CONTRADICTED by these traces | It asked more. Probably the prompt |
| 52 | §10: "my plans for medium tasks run longer than the 150 to 400 words stated" | CONFIRMED | See row 42 |
| 53 | §10: Verification is planned, with less certainty about its quality | CONFIRMED | Planned everywhere; nothing was run |

**Summary of the check.** The self-report is accurate about dispositions (scope restraint, premise checks, gates, proportionality) and inaccurate about quantities (question count, plan length, time estimates). About two thirds of its confirmed claims are generic good practice that Opus shows equally. Several real deltas found in the traces are absent from the self-report or only implied: D1 (say where the work is), D7 (rank the questions and state the branch), D9 (concrete dates), D11 (what the end state takes away), and the fail-safe half of D5. A skill written from the self-report alone would be long, mostly redundant for Opus, and would miss these.

---

## 6. Ranked list of moves to teach

Ranked by expected effect on plan quality, discounted by how sure the evidence is.

1. **D1 Say where the work is.** Decided E5, the only clear win; changes the structure of the plan and not only its wording.
2. **D3 Smallest change; findings in a list.** Decided E2; directly prevents the widened diff Opus produced.
3. **D4 Stop, abort and go/no-go conditions.** Fable 5, Opus 2; the abort-inside-the-step form is absent from Opus entirely.
4. **D5 Fail-safe defaults, a switch, and a settling check; never block on an answer.** Fable 5, Opus 2; Opus's E2 default fails open and its plan waits.
5. **D2 Cheaper path first, then the requested plan.** Can save the whole project; only two instances, so rank below the better-evidenced moves.
6. **D8 Zero ritual on trivial tasks.** One data point, but the cost of the opposite behaviour is paid on the most frequent kind of request.
7. **D7 Rank the questions and state what each answer changes.** Fable 6, Opus 3; cheap to add to what Opus already writes.
8. **D6 Flag recalled specifics and unrun code at the point of use.** Opus stated one apparently wrong fact flatly; small text cost.
9. **Do not invent numbers you cannot know; give a structure instead (part of D5).** E6 budget; must be taught with the caveat that Fable broke it in E4.
10. **D10 Give the reason for the order; announce after commitment.** Caught one real ordering error in Opus's E6.
11. **D11 Account for what the end state takes away.** High value on migrations, irrelevant elsewhere.
12. **Strict proof for a diagnosis (part of D4).** "Reproduce with and without the suspected cause" against "ideally reproduced".
13. **D9 Concrete dates for relative ones.** Trivial to do, removes a class of misunderstanding.
14. **Commit to one recommendation on a design fork, with a verdict per option.** E8 keys only; weak evidence, low cost.

Guards the skill should carry alongside these, taken from section 4: contain before diagnosing in incidents; stage the rollout when parameters are guessed; keep reporting adjacent findings; keep operational and organisational items in large migrations; do not add length.

---

## 7. Question catalogue: what Fable asked, with the default each carried

Wording is quoted or lightly shortened from the traces. Questions marked † also appear in Opus's trace for the same task in substantially the same form.

### Greenfield tool (E1)

| Question | Default |
|---|---|
| Custom tool, or a thin setup around an existing generator? | Custom tool, as requested |
| What do the notes look like: plain Markdown or Obsidian-style? † | CommonMark plus tables and fenced code, with `[[wikilinks]]`; embeds and callouts left out of version 1 |
| Are all notes meant to be public? † | Every note published unless front matter says `draft: true` or `publish: false`; an ignore list is accepted |
| Language? † | Python 3.11+, installed with `pipx`; design unchanged for other runtimes |
| Where will the site live: user site or project repository? † | Project repository, so a base path must be handled |
| Do you need search, tags, or backlinks? | None in version 1; folder tree and index page |
| How large is the folder? | Under a few thousand notes; full rebuild each time |

### Brownfield feature (E2)

| Question | Default |
|---|---|
| Is there a reverse proxy, load balancer, or CDN in front of the app? † | No proxy; exposed as `TRUST_PROXY` so it can be corrected without a code change |
| Who calls `POST /orders`: end customers directly, or one storefront backend? † | Callers have their own addresses |
| Which route did the bot hit, at what rate, from how many addresses? † | `POST /orders`, from a small number of addresses |
| Do the warehouse staff share one office IP address? | Yes; so no strict limit on shipping and import routes, and a high general limit |
| What is normal peak traffic? | Unknown; 300 per minute overall and 20 orders per minute per address, both environment variables |

### Incident (E3)

| Question | Default |
|---|---|
| What identifies a transaction uniquely? † | A stable vendor ID; step 1 tests this before anything relies on it |
| Does `transactions` have a primary key or unique constraint on that identifier? † | No |
| What changed around 10 November? † | Unknown, to be found in step 2 |
| Who reads `transactions`? † | Downstream consumers exist and have already read duplicated data |
| Can I query production read-only and read the Airflow logs? | Yes; otherwise someone with access runs step 1 |
| Is the load append-only, or can the vendor send corrections? | Append-only; if not, the fix becomes update-on-conflict |

### Vague request / performance (E4)

| Question | Default |
|---|---|
| What prompted this? † | Customer complaints about specific screens, with no measurements yet |
| Which part is slow? † | Unknown; measure the five most-used screens and twenty most-called endpoints |
| Slow for whom? † | Worst for the largest accounts |
| What would count as fast enough? † | 2.5 s at p75 for main screens, 300 ms at p95 for API reads, 200 ms to visible feedback; to be replaced by the user's |
| What do you already measure? † | Server logs and little else |
| What is the stack below "React and Node"? † | Postgres, single region, static files without a CDN |
| How much time is this worth, and is anything off limits? † | About two weeks; no rewrites, framework changes or infrastructure migration |

### High-risk migration (E5)

| Question | Default |
|---|---|
| Are the other tables moving later, or is `users` moving alone for good? † | First table of a wider migration; tooling should be reusable |
| Does "zero downtime" allow writes to be held for a few seconds at cutover, as long as none fail? † | Yes, up to about 10 seconds of added latency, once |
| Which tables have foreign keys to `users`, and which queries join to it or write to it inside a larger transaction? | Several of each; they must be decoupled first |
| Managed or self-hosted? † | Binlog access available; row-based binlog can be enabled |
| What writes to `users` besides the main application? † | One main application plus a few jobs, all changeable |
| Which language and ORM, and is there a single data-access layer for users? † | Mainstream ORM; access is spread around and needs consolidating |
| What is the write rate, and how much replication lag can reads tolerate? † | Hundreds of writes per second at peak; reads after a write must see it |

### Non-software project (E6)

| Question | Default |
|---|---|
| What is the offsite for? † | About half working sessions, half time together |
| What is the total budget, or the per-person figure? † | Not set; a percentage split is given and the user supplies the total |
| Where are the 40 people based? † | Mostly one city, a few travelling in |
| Are the dates fixed or flexible? † | Flexible within two weeks around mid-February 2027; midweek |
| Overnight stay, or two day-trips? † | One night away, within about two hours of the office |
| Who decides, and who does the work? † | One executive sponsor; one organiser with a helper |
| Is attendance expected of everyone? | Yes, during paid working days |
| Any constraints: alcohol policy, travel policy, people who cannot stay overnight? † | Standard company policy; some will need adjustments for caring duties, diet or access |

### Trivial change (E7)

No questions. One offer: "Say if you want it renamed to `fetchUserByEmail` too", with the default of leaving it.

### Large cross-cutting change (E8)

| Question | Default |
|---|---|
| What is driving this: cost, onboarding speed, growth, cross-customer features? † | Cost and onboarding speed, with growth expected; row-level tenancy |
| Do any contracts promise a dedicated database, data residency, or customer-managed encryption? † | A few do; routing must keep supporting dedicated databases |
| Do all 60 run the same code version and schema? † | Same code; small schema drift |
| Are integer record IDs visible outside the app? | Yes; changing them is a breaking change to manage |
| Can each customer accept a short read-only window for its own cutover? † | Yes, up to about 30 minutes, scheduled |
| How big is the largest customer compared with the rest, and what is the total size? † | One or two far larger than the median; total fits on one primary |
| How are customers identified on a request today? † | Subdomain or domain per customer, mapped by configuration |
| Rails and PostgreSQL versions; job system, cache, search, file storage? † | Rails 7.x, PostgreSQL 14+, Sidekiq, Redis, Active Storage |

### What the catalogue shows

- Of Fable's 48 questions, 38 (those marked †) also appear in Opus's trace for the same task. The questions are not the delta.
- The Fable-only questions share a type: they ask about a fact that would make the default design harmful or the plan much smaller. Examples: "Custom tool, or... an existing generator?", "Do the warehouse staff share one office IP address?", "Is the load append-only, or can the vendor send corrections?", "Which tables have foreign keys to `users`...?", "Are integer record IDs visible outside the app?", "Can I query production read-only...?".
- The Opus-only questions also share a type: resources and access. "Can I see the repo(s)?", "Team size and timeline?", "Is there a staging/raw table or an archive of the vendor files?", "Is adding a dependency OK?", "Can I add authentication to `/admin/*` in the same change?".
- Fable's defaults are stated as what the plan does. Three of them are an admission ("unknown", "not set") paired with the step that finds the answer.
