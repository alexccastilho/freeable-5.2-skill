# Results: can a skill make Opus 5.5 plan like Fable 5.2?

**Short answer (after round 3, skill v3).** On 4 fresh software-planning tasks, blind judges scored Opus 5.5 + skill v3 at **8.7 out of 10**, against 7.5 for bare Opus 5.5 and 7.4 for bare Fable 5.2. v3 was ahead of both bare models on every task, caught the most planted traps (93.8%) and committed no scope creep. The rounds before v3 found smaller and more mixed gains (see rounds 1 and 2 below), and the samples are still small.

Bare Fable 5.2, run without any review tool, did **not** out-plan bare Opus 5.5 on average across the 9 held-out tasks of rounds 1 and 2, and scored 7.39 against 7.52 in round 3. By mean rank in rounds 1 and 2 it was ahead on 3 of 9 (V1, V4, V6) and behind on 6. In this harness, unaided Fable is not a better target than Opus. What the skill encodes is closer to the pattern Fable shows *when it plans with a review step*.

All numbers come from blind, randomised, two-judge evaluation (one Fable 5.2 judge and one Opus 5.5 judge per task), with answer keys written before any response existed. Each task was run twice per arm. The samples are small: read the differences as directional, not significant.

## Method

```
Extraction (8 tasks E1–E8)  ─►  delta analysis (Fable vs bare Opus)  ─►  skill v1 written by Fable
        │                                                                     │
        └─ re-run 4 tasks without the advisor tool (confound check)           ▼
                                                     Round 1: 6 held-out tasks (V1–V6), 3 arms × 2 reps
                                                                              │ failures described abstractly
                                                                              ▼
                                                     skill v2 written by Fable (no access to eval files)
                                                                              ▼
                                                     Round 2: 3 fresh tasks (H1–H3), 4 arms × 2 reps
                                                                              ▼
                                                     skill v3 by Fable: v1 + v2 + unaided Fable + built-in review
                                                                              ▼
                                                     Round 3: 4 fresh software tasks (R1–R4), 4 arms × 2 reps, 0–10
```

- **Arms.** `opus` = Opus 5.5, no skill. `skill` = Opus 5.5 told to read `SKILL.md` first. `fable` = Fable 5.2, no skill. Every arm got an identical brief. Skills, plan mode, subagents and the advisor tool were forbidden, so we measured models, not plugins.
- **Blinding.** Responses were shuffled into anonymous bundles with model and skill names redacted (`research/evaluation/blind.py`). Judges never saw the mapping.
- **Scores.** Traps caught per answer key; over-reach penalties (round 2); Q1–Q5 quality from 1 to 5 (questions, grounding, risk and verification, proportionality, actionability); overall rank; move presence D1–D11 (`research/evaluation/moves.md`).
- **Answer keys.** Round 1 keys were written by the orchestrating Opus session. Round 2 keys were written by a Fable 5.2 agent that never saw the skill, to avoid keys that only list what Opus already thinks of.

## Round 1: 6 held-out tasks (V1–V6), skill v1

| Arm | Traps caught | Q mean (1–5) | Mean rank (1 = best of 6) | Words |
|---|---|---|---|---|
| Opus | 95.3% | 4.21 | 3.58 | 926 |
| **Opus + skill v1** | 93.8% | **4.53** | **3.00** | 1,140 |
| Fable | 93.4% | 4.13 | 3.92 | 921 |

- **Q dimensions, Opus → Opus + v1:** questions 4.25 → 4.92; risk and verification 3.88 → 5.00; proportionality 4.33 → 3.83 (worse); actionability 4.46 → 4.67.
- **Traps were near ceiling:** 34 of 42 were caught by every response, so this key barely discriminates.
- **Regressions:**
  - V3 ("switch sessions to JWT"): v1 made Opus default to the questionable premise.
  - V5 (caching): v1 runs dropped thundering-herd protection and the staleness question.
- **Move presence (mean of D1–D11):** Opus 0.45, Opus + v1 0.92, Fable 0.47.

## The advisor confound

The original Fable extraction runs called an external advisor (reviewer) tool once per batch; the Opus runs did not. We re-ran four extraction tasks with Fable and the advisor forbidden, then had a blind judge score move presence and quality (`research/evaluation/advisor-confound/`):

| | Mean move presence | Quality (1–10) | Words (E2/E3/E5/E8) |
|---|---|---|---|
| Fable + advisor | 0.86 | 9.0 | 1,349 / 1,860 / 2,072 / 2,009 |
| Fable, no advisor | 0.68 | 8.25 | 942 / 1,625 / 1,721 / 1,749 |
| Opus | 0.55 | 7.75 | 1,172 / 1,400 / 1,654 / 1,655 |

Unaided Fable keeps a real but smaller edge on large planning tasks. The clearest moves are offering the cheaper path, flagging recalled specifics and resolving relative dates. The review step amplifies the pattern. On the smaller held-out tasks the unaided edge disappeared.

## Round 2: 3 fresh tasks (H1–H3), skill v1 vs v2

Move presence = presence of the skill's own move set D1–D11, scored by the Opus judge only.

| Arm | Traps net of over-reach | Over-reach hits | Q mean | Mean rank (1 = best of 8) | Errors | Words | Move presence |
|---|---|---|---|---|---|---|---|
| Opus | **90.0%** | 4 | 4.22 | 3.67 | 18 | 1,300 | 0.44 |
| Opus + skill v1 | 88.8% | **0** | **4.50** | **3.42** | **15** | 1,594 | 0.93 |
| Opus + skill v2 | 87.5% | **0** | 4.38 | 4.17 | 16 | **1,188** | 0.84 |
| Fable | 85.0% | 3 | 3.77 | 6.75 | 21 | 963 | 0.40 |

| Q dimension | Opus | v1 | v2 | Fable |
|---|---|---|---|---|
| Q1 clarifying questions | 3.92 | **4.92** | 4.83 | 3.33 |
| Q2 grounding | **4.75** | 4.33 | 4.08 | 4.17 |
| Q3 risk and verification | 3.75 | **4.67** | 4.42 | 3.00 |
| Q4 proportionality | 3.83 | 4.17 | **4.42** | 4.33 |
| Q5 actionability | **4.83** | 4.42 | 4.17 | 4.00 |

Judges disagree on overall rank. The Fable judge puts bare Opus first (3.17, then v1 3.67, then v2 5.00); the Opus judge puts v1 first (3.17, then v2 3.33, then Opus 4.17). Both put bare Fable last.

**What v2 fixed:** length (−9% against bare Opus, where v1 was +23%) and proportionality (best Q4). We also re-ran v2 twice on the two round-1 tasks where v1 regressed (`research/evaluation/v2-recheck-tuned/`). These tasks informed the v2 revision, so this is a check on tuned tasks, not a held-out result.
- **V3 (JWT):** both runs now default to keeping sessions, with JWT only for an API if needed and the full switch as a branch selected by the driver question.
- **V5 (caching):** both runs include thundering-herd protection (post-import warming; one run adds a rebuild lock), and both ask the staleness tolerance as question 1.

**Why v2 shipped over v1 (superseded by v3 in round 3):** v1 scored higher on quality and rank in round 2. But it writes 23% more than bare Opus and defaulted to a costly, questionable premise in round 1. v2 is shorter than bare Opus and keeps the zero scope creep. If you prefer v1's thoroughness, it is frozen in `research/evaluation/round1/skill-v1/`. **What it did not fix, or cost:** grounding in the existing code. On the brownfield task (H1), skill runs were less likely to state premise-breaking facts found in the repository, such as "there is no admin UI" or "the schema has no line items", and the failure-mode checklist read as padding to one judge.

## Round 3: 4 fresh software tasks (R1–R4), skill v3, score 0–10

The tasks were all software development or improvement work:
- **R1:** a production-readiness review of the shopmini repository.
- **R2:** a React Native crash regression after a release.
- **R3:** adding English and Spanish to a Next.js shop.
- **R4:** speeding up a 6-second WooCommerce store.

A Fable 5.2 agent that had not seen the skill wrote the answer key and a 0–10 scoring guide before any response existed. Each task had one blind Fable judge and one blind Opus judge. The files are in `research/evaluation/round3/`.

**v3:** Fable wrote it by merging four sources:
- **v1:** its richness of questions, gates and risk content;
- **v2:** its confirmed fixes, namely the default-path rule, failure coverage inside steps, and the driver and tolerance questions;
- **unaided Fable:** its concision and its cheaper-path, flagging and date moves;
- **new in v3:** premise facts found in the code, defaults checked against the user's real workflow, concrete first steps, run-before-assert when tools exist, and a silent nine-check self-review before output.

| Arm | Score 0–10 | Fable judge | Opus judge | Traps net | Scope creep | Rank (1 = best of 8) | Words |
|---|---|---|---|---|---|---|---|
| **Opus 5.5 + skill v3** | **8.69** | **8.86** | **8.51** | **93.8%** | **0** | **2.50** | 1,454 |
| Opus 5.5 + skill v1 | 8.46 | 8.61 | 8.31 | 91.2% | 0 | 3.00 | 1,358 |
| Opus 5.5 | 7.52 | 7.70 | 7.34 | 87.2% | 3 | 5.88 | 1,344 |
| Fable 5.2 | 7.39 | 7.50 | 7.28 | 84.4% | 0 | 6.62 | 1,013 |

| Task | Opus | Fable | Opus + v1 | Opus + v3 |
|---|---|---|---|---|
| R1 shopmini readiness | 7.35 | 7.53 | 8.23 | **8.57** |
| R2 mobile crash regression | 8.00 | 7.28 | **8.35** | 8.18 |
| R3 i18n of a Next.js shop | 7.38 | 7.67 | 8.97 | **9.08** |
| R4 WooCommerce speed | 7.35 | 7.08 | 8.30 | **8.93** |

- **v3 against bare Opus:** +1.17 on average, ahead on 4 of 4 tasks (+0.18 to +1.70).
- **v3 against bare Fable:** +1.30, ahead on 4 of 4.
- **v3 against v1:** +0.23, ahead on 3 of 4.
- **Spread:** the lowest v3 response scored 7.6, while the median bare-Opus response scored 7.6.
- **Significance:** with only 4 tasks, a sign-flip test cannot go below p = 0.125 even when every task favours one arm. "4 of 4" is the honest statement, not "significant".
- **Judges agree on the order:** v3 > v1 > Opus > Fable, for both the Fable judge and the Opus judge.
- **Errors flagged by judges:** similar in kind across arms. The most common one is the claim that SQLite will not enforce a foreign key, when better-sqlite3 enables foreign keys by default; it appears in bare-Opus and v3 runs alike. v3 has the most flagged items (18, against 15 for bare Opus, 13 for v1 and 12 for bare Fable). About half are omissions of the "also check X" kind. The rest are technical errors (the foreign-key claim, flagged by both judges on one run; backups scheduled after the schema changes they should protect; a JSON body said to crash the process; a wrong date; a WordPress autoload query that misses values added in 6.6; a content freeze that does not stop orders splitting between hosts) and risks left unflagged (rolling an OTA bundle or a whole build back over data or native modules changed by 4.2). The other arms' errors were not classified the same way, so no comparison of error kinds is made.
- **Length:** v3 is about 8% longer than bare Opus on average, inside its own target of +10%. Per task it is not: +7.8% on R1, +14.2% on R2, +0.1% on R3 and +11.8% on R4. No v3 plan was under 1,243 words, against a stated ceiling of about 1,000. v3.1 replaces that rule (see below).

## v3.1 smoke check (not a round)

v3.1 replaces v3's length ceiling with a band per workstream and applies the fixes in `CHANGELOG.md`. It was checked on three shapes v3 was not, with Opus 5.5 generating and the skill delivered by a forced read. One judging session per bundle, with old and new runs judged together, blind and shuffled; one Opus 5.5 judge and one Fable 5.2 judge.

| Shape | Runs | Result |
|---|---|---|
| Trivial (V4, typo in a README) | 1 | The change, the searches run, a one-line offer; 79 words, no plan |
| One workstream (R4, WooCommerce speed), against the 8 round 3 runs | 1 | 8.90 (judges 8.8 and 9.0), against v3 9.15 and 8.80 (two runs), v1 8.35, bare Opus 7.10, bare Fable 6.95. Traps 90%. 1,875 words, above the band's 1,500 |
| Several workstreams (a plan for the next version of another skill, outside this repository), against 6 earlier plans | 2 | 8.45 (judges 8.50 and 8.39), against v3 6.94, bare Opus 8.98 and bare Fable 8.93. 5,636 and 4,327 words, against 1,590 and 1,863 for v3 and 6,932 to 8,793 for the bare models |

Reading:
- **Several workstreams:** the band closed most of v3's gap (from about 2.0 points to about 0.5). v3.1 is still below both bare models, and weakest on the design of the dynamic-update mechanism, one of the request's workstreams.
- **One workstream:** v3.1 matched v3 on quality. It wrote about a third more, and above its own band.
- **Weight of the evidence:** these are 4 runs, one per shape at most two, and directional only. A full round is still owed (see "Known gaps").

## Verdict on the user's question

> "Would Opus 5.5 with the skill deliver similarly to Fable 5.2?"

- **Like unaided Fable: no.** On move presence, Opus with the skill (0.84–0.93) is further from unaided Fable (0.40–0.47) than bare Opus is (0.44–0.45).
- **Like Fable with a reviewer: closer.** Reviewed Fable scored 0.86 on extraction tasks. That anchor is weak and partly circular: D1–D11 were catalogued from those same traces, and it rests on 4 tasks, one run and one judge.
- **On outcome quality, rounds 1 and 2 (v1, v2):**
  - **Better:** blind judges rate the skill's plans higher on questions, risk handling and (v2) proportionality, with no scope creep.
  - **Worse:** they do not catch more planted traps than bare Opus. Grounding drops (4.75 → 4.08 for v2), and so does actionability (4.83 → 4.17).
  - **Mixed:** overall rank. One judge ranks bare Opus above both skill versions.
- **Caveats:**
  - **Sample:** rounds 1 and 2 had 9 held-out tasks, 2 runs each, 2 judges; round 3 adds 4 tasks.
  - **Recognisable format:** judges can recognise the skill's output format. In round 3, "Answer first" appears in 8 of 8 v1 and v3 runs and in none of the bare runs; "First steps" in 8 of 8 v3 runs only. `blind.py --normalize` neutralises these phrases for future rounds.
  - **Same-family rubric:** the round 3 key and scoring guide were written by a Fable 5.2 agent that had not seen the skill, but they reward the same planning traits the skill was built from (a default with each question, a first step that can start today, explicit deferrals). Part of v1's jump in round 3 may come from the change of rubric.
  - **Untested shapes in round 3:** no trivial task, no bounded change, no project outside software, and no plan with several workstreams.
  - **Unrecorded effort:** subagent reasoning effort was not recorded.
  - **Shared context:** each arm planned 2–4 tasks in one context.
  - **Forced read:** the skill was delivered by a forced read, so triggering from its `description` is untested.
- **On outcome quality, round 3 (v3):** Opus + v3 scored 8.69 out of 10, against 7.52 for bare Opus and 7.39 for bare Fable, and was ahead of both on all 4 tasks. That includes the brownfield code-review task (R1: 8.57 against 7.35), where v1 and v2 had lost grounding. v3 also caught the most traps. For software planning, v3 is the strongest result in this study.
- **Where it helps:** most on multi-phase, risky or ambiguous work. With v3, the brownfield gap of v1 and v2 closed on the one brownfield task measured.

## Known gaps and next steps

1. **Grounding and first steps.** These were the gaps of v1 and v2. v3 addresses them with premise facts, a check of each default against the real workflow, and concrete first steps. On R1, the brownfield task, it improved, but that is a single task.
2. **Fact checks.** Judges still flag claims stated as fact that the code contradicts, such as the foreign-key behaviour in better-sqlite3. v3's run-before-assert rule only helps when the model actually runs or reads the code.
3. **Sample size.** Re-measure with more tasks and runs, and use judges blind to output format (`blind.py --normalize`). Also test triggering from the `description`, without a forced read.
4. **A full round for v3.1.** Include a trivial task, a bounded change, a project outside software and a request with several workstreams, and one judge from another model family.

## Where everything is

- `research/extraction/`: tasks, raw traces (with and without the advisor), Fable's self-report, delta analysis.
- `research/evaluation/round1/`, `round2/`, `round3/`: tasks, answer keys, all runs, judge JSON, mapping, `scores.txt`, frozen skill snapshots (v1, v2, v3).
- `research/evaluation/*.py`: blinding and scoring scripts.
- `research/fixtures/shopmini/`: the small repository used by brownfield tasks.
