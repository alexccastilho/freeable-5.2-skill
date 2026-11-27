# Changelog

## v3.1

Not measured in a full round. The scores in the v3 section are for v3, frozen in `research/evaluation/round3/skill-v3/`. The smoke check below is the only evidence for v3.1.

Sources: an external review of the repository, checked against the data in this repository, and one blind comparison outside it in which Opus + v3 scored last on a plan with several workstreams (6.69 against 8.52 bare Opus and 8.74 bare Fable; three judges). Its plans had 1,590 and 1,863 words against 6,932 to 8,793 for the bare models, and they lost on coverage of whole workstreams.

| # | Problem in v3 | v3.1 |
|---|---|---|
| 1 | Length rule could not be observed ("the length you would write without this skill") and its ceiling (about 1,000 words) sat below the bare model's own length on the round 3 tasks (1,344 on average). On a request with several workstreams it cut the plan to a fifth | Step 11: a band set by the number of workstreams in the request, 800 to 1,500 words of prose each; about 500 for a bounded change. Size check updated |
| 2 | The `description` invited loading the skill to decide that a small change needs no plan, and had dropped projects outside software, which the body and references still cover | Triggers on multi-step work, work touching production, data or people, and projects outside software. The trivial-change recipe stays in the body |
| 3 | When step 3 kept the request, the output contract had no slot for the cheaper path that step 3 requires | Part 4 has that slot |
| 4 | "Found, not touched" with one or two items conflicted with the three-line heading minimum | Fewer than three: one closing sentence, no heading |
| 5 | References had lost the "read when" triggers v1 had | Each reference has one |
| 6 | Judges flagged claims about library defaults and version-bound queries (foreign keys in better-sqlite3, WordPress autoload values) | Step 8, the Invention check and pattern F5: a library default is read, run or flagged; an unrun command names the version it assumes |
| 7 | The question bank put the driver third for brownfield work and kept six or seven "Ask" rows for three task types | Driver or tolerance first, at most five "Ask" rows per table, and a note that rows are examples from one source task each |
| 8 | The overview assumed the reader already plans well ("You already...") | States the basics as part of every plan |
| 9 | The origin paragraph and this changelog lived inside the installable folder, with a link that broke after installation | Origin paragraph removed; changelog moved to the repository root |

**Smoke check** (4 runs, blind, one Opus and one Fable judge; details in `research/RESULTS.md`):
- **Plan with several workstreams (the tuned task the rule came from):** 8.39 against 6.91 for v3, and 8.95 and 8.93 for bare Opus and bare Fable.
- **WooCommerce task from round 3:** 8.90 against 8.97 for v3 in the same judging session, but at 1,875 words: above the one-workstream band, and 50% more than bare Opus.
- **Trivial typo:** the change itself, in 79 words.

Evaluation scripts: `score3.py` now uses the true median, an exact sign-flip test and English labels; `blind.py` no longer redacts the plain word "skill" and has an optional `--normalize` flag that neutralises the skill's signature headings before judging. The published round 3 numbers do not change; `round3/scores.txt` was regenerated.

## v3

v3 merges four sources: v1, v2, Fable 5.2 working without a reviewer, and Fable 5.2 working with one. It was written from the evaluation summaries below.

**Measured after release (round 3):** 4 fresh software tasks, 2 runs per arm, one blind Fable judge and one blind Opus judge, holistic score from 0 to 10. Opus + v3 scored 8.69, Opus + v1 8.46, bare Opus 7.52 and bare Fable 7.39. v3 had the most traps caught (93.8%), no over-reach and the best mean rank (2.50 of 8). It beat bare Opus and bare Fable on all 4 tasks and v1 on 3 of 4. v3 is about 8% longer than bare Opus (1,454 words against 1,344). Details are in `research/RESULTS.md`, round 3.

### Evidence used

Blind evaluation, two judges, quality as the mean of five dimensions scored 1 to 5.

- Seven software planning tasks (V1, V2, V3, V5 from round 1 and H1 to H3 from round 2): a baseline model with v1 averaged 4.44 against 4.12 bare, and was ahead on all seven (by 0.05 on V3).
- The three fresh tasks of round 2 (H1 to H3, already among the seven): v1 4.50, v2 4.38, bare 4.22. v1 ranked above v2.

| Dimension, fresh round | Bare | v1 | v2 |
|---|---|---|---|
| Questions | 3.92 | 4.92 | 4.83 |
| Grounding in specifics | 4.75 | 4.33 | 4.08 |
| Risk and verification | 3.75 | 4.67 | 4.42 |
| Proportionality | 3.83 | 4.17 | 4.42 |
| Actionability | 4.83 | 4.42 | 4.17 |

- Both skill versions produced no scope creep; the bare runs produced four items.
- Fable 5.2 without a reviewer, with a reviewer, and the bare baseline, on four large tasks: move presence 0.68, 0.86 and 0.55; quality 8.25, 9.0 and 7.75 out of 10.

### From v1

| Kept | Why |
|---|---|
| The question format (default, branch, "answer first") and the gates | Questions and risk were v1's largest gains over the bare model, and v1 ranked above v2 |
| The quick-reference table | Restored, in `references/gates-and-defaults.md`, extended with the v3 rows |
| The common-mistakes list | Restored as the review checks in step 12: each mistake is now a check with a pass condition, which keeps the recipe positive |
| "Found, not touched" and the trivial-task recipe | No scope creep in either version |

### From v2

| Kept | Why |
|---|---|
| The three-predicate default-path rule | Confirmed fix: v1 argued for the cheaper path and then planned the costly one |
| "Smallest change, full failure coverage" | Confirmed fix: v1 dropped standard failure modes |
| Question slots filled in order: driver, tolerance, harm or shrink, access | Confirmed fix: v1 dropped the tolerance question |
| Three-line minimum per heading, each risk once, word ceilings | v1 wrote 23% more than the bare model; v2 wrote 9% less |
| The origin note that says the pattern came from reviewed traces | Still true; v3 extends it |

### From Fable 5.2 without a reviewer

These are the moves it made unaided that the bare baseline made less often, and the shape of the tasks it won.

| Taken | Evidence | Where |
|---|---|---|
| Opener says where the work is | 0.88 against 0.62 | Step 2 |
| Cheaper path raised | 0.50 against 0.00 | Step 3 |
| Recalled specifics flagged | 0.62 against 0.25 | Step 8, and the "Invention" check |
| Relative dates made concrete | 0.25 against 0.00 | Step 8, and dates written into first-step queries |
| Concision and proportional sizing | Best on a small brownfield feature, a trivial fix and a logistics plan; highest proportionality at the shortest length | Step 11: say each thing once where it is used; a step is a verb, the real thing and its check; a prose opener with no summary heading. The bounded-change shape in `task-type-notes.md` |

Not taken: its thin risk and verification content (3.0) and its shorter question list. v1's gates and question format cover those.

### From Fable 5.2 with a reviewer

| Taken | Evidence | Where |
|---|---|---|
| A review pass over the draft | 9.0 with one reviewer call against 8.25 without | Step 12: nine observable checks run after drafting; each failure is fixed in the draft; nothing of the review is printed; three checks for a trivial change |
| The moves seen only in reviewed traces | Listed in the v2 section below | Unchanged: small diff, ranked questions, loss accounting |

### New in v3

| # | Problem in v1 and v2 | v3 |
|---|---|---|
| 1 | Grounding fell below the bare model (4.33 and 4.08 against 4.75). On a small brownfield repository, skill runs often left out facts in the code that broke the premise: a named component that did not exist, no access control on any route, data missing from the schema, an unreliable field. The bare runs stated them | Step 1 runs four premise checks while reading. Each failure is a premise fact with its location and its effect on the request. Output part 2 holds them before the questions, or the opener does when there are fewer than three. They are kept apart from "Found, not touched", which holds what does not change the plan |
| 2 | Skill runs proposed a default that the user's real client could not use | Step 4 walks each default from the client that triggers it and replaces any default the client cannot supply. Pattern D-a2 in `gates-and-defaults.md`; a client question in the question bank for when the walk cannot be completed |
| 3 | Actionability fell below the bare model (4.42 and 4.17 against 4.83), which gave file-level edits and concrete first steps | Step 9: phase 1 ends with three to six first steps naming files, functions, commands, queries or edits. A bounded brownfield change shows the diff. With nothing seen, the first steps are the exact commands, and no file name is invented |
| 4 | v2's failure-mode coverage sometimes read as a separate checklist | Each failure line sits inside the step it protects. A separate failure list fails the review. "Does not apply" lines are written only when a reader would expect the protection |
| 5 | Neither version said what to do when the model can act | Step 1 and `gates-and-defaults.md`: with tools, run or read before asserting, and report the result. Each plan step names its verifying command. Conditional on tool availability |
| 6 | Length | The bare model's length plus 10% at most. Premise facts and first steps are paid for by cutting restatement. Code and diffs are outside the count, so showing the edit costs nothing against the ceiling |

SKILL.md grew to about 2,000 words to hold the review table. The quick-reference table lives in `references/gates-and-defaults.md` for that reason.

## v2

Source of the changes: a blind evaluation of v1 (a baseline model with v1, the same model bare, and Fable 5.2 bare; six held-out tasks, two runs each, two blind judges), and a re-run of four extraction tasks without the review step.

### Kept from v1

The question format with defaults, the gates, the flags and the trivial-task recipe. In the evaluation, clarifying questions rose from 4.25 to 4.92 out of 5 and risk and verification from 3.88 to 5.0, and the trivial task was handled proportionally.

### Changed

| # | v1 behaviour | Evidence | v2 |
|---|---|---|---|
| 1 | Cheaper path named first, then the request planned as the default, always | On a costly, hard-to-reverse request with a doubtful premise, v1 plans argued for the cheaper path and then defaulted to the expensive one. The bare baseline defaulted to the cheaper path and ranked far higher | Step 3 picks the default from three observable predicates. When the request is costly or irreversible, and the cheaper path is reversible and serves the stated outcomes and likely driver, the cheaper path is planned in full and the request becomes a short branch. Otherwise the request stays the default |
| 2 | Eight contract slots; a "Cut" step with no measure | Plans grew about 23% (926 to 1,140 words); proportionality fell from 4.33 to 3.83 | Three mandatory parts and one conditional. "Not seen" moves into the opener; "Need from you" merges into "Answer first". Conditional parts are one line each unless they hold the main risk. Word ceilings, a three-line minimum per heading, each risk stated once |
| 3 | "Smallest change" and the five-question cap were applied to risk coverage | On a performance task, v1 runs dropped standard failure protections and the tolerance question that bare runs included | Step 6 separates feature scope from failure coverage and gives a list of standard failures to run. Tolerance questions hold a place in the five |
| 4 | Driver question ranked with the rest | Asked less often with v1 than without (0.62 against 0.88) on a task where the driver sets the extent of the work | Step 5 fills the cap in a fixed order: driver first when it changes scope, then tolerance |
| 5 | Origin stated as "distilled from paired traces of Fable 5.2 and a baseline model" | See below | Origin note says the pattern comes from traces produced with a review step, plus evaluation fixes |

Also removed from SKILL.md: the quick-reference table and the common-mistakes list, which repeated the procedure.

### Origin: what the no-review re-run shows

The original Fable 5.2 extraction traces each record one reviewer call. Four tasks (E2, E3, E5, E8) were re-run with no reviewer; the traces are in `research/extraction/traces-noadvisor/`. One sample per task, so these are observations and carry no variance estimate.

| Move | With review step | Without review step |
|---|---|---|
| Cheaper path at the top (E8) | First paragraph, with the goal check | Schema per customer rejected inside the design section; the driver is question 1 |
| Smallest change (E2) | One source file, two limits | New module, three limits |
| Recalled specifics flagged (E2) | Option names flagged with the check | Option names and version stated flatly; only the limit values are called guesses |
| Questions ranked (all four) | A closing line names the questions to answer first | Four to eight questions and no such line; E8 names three decisions in its summary |
| What you lose (E8) | Table | Absent; items spread through a risk table |
| Unknown durations (E5, E8) | Given in both, hedged | Given in both |
| Where the work is (E5) | Opener, and a phase sized to it | In the opener, hedged; left to the inventory phase |
| Abort rule in the cutover (E5) | Present, 15 seconds | Present, 30 seconds |
| Fail-safe proxy default as a setting (E2) | Present | Present |
| Relative date resolved (E3) | Present | Present |
| Containment before diagnosis (E3) | Absent | Present |
| Log-only stage for guessed limits (E2) | Absent | Present |

Reading: gates, fail-safe defaults and date resolution appear either way. The cheaper-path opener, the small diff, the ranked questions and the loss accounting appear only in the reviewed traces. The blind evaluation agrees: bare Fable 5.2 without a reviewer used these moves at about the bare baseline's rate, except flagging recalled specifics (0.45 against 0.05). The skill therefore describes a reviewed planning pattern. It does not describe what any model does unaided.

## v1

Initial version, distilled from eight paired extraction traces (E1 to E8), one sample each.
