# Results: can a skill make Opus 5.5 plan like Fable 5.2?

**Short answer.** The skill reliably installs a distinctive set of planning moves in Opus 5.5. Blind judges rate the resulting plans higher on clarifying questions and risk handling, and (in v2) on proportionality, with zero scope creep. It does **not** raise the trap-catch rate, it costs grounding and actionability, and overall rank is mixed.

Bare Fable 5.2, run without any review tool, did **not** out-plan bare Opus 5.5 on average across our 9 held-out tasks. By mean rank it was ahead on 3 of 9 (V1, V4, V6) and behind on 6. In this harness, unaided Fable is not a better target than Opus. What the skill encodes is closer to the pattern Fable shows *when it plans with a review step*.

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

**Why v2 ships over v1:** v1 scored higher on quality and rank in round 2. But it writes 23% more than bare Opus and defaulted to a costly, questionable premise in round 1. v2 is shorter than bare Opus and keeps the zero scope creep. If you prefer v1's thoroughness, it is frozen in `research/evaluation/round1/skill-v1/`. **What it did not fix, or cost:** grounding in the existing code. On the brownfield task (H1), skill runs were less likely to state premise-breaking facts found in the repository, such as "there is no admin UI" or "the schema has no line items", and the failure-mode checklist read as padding to one judge.

## Verdict on the user's question

> "Would Opus 5.5 with the skill deliver similarly to Fable 5.2?"

- **Like unaided Fable: no.** On move presence, Opus with the skill (0.84–0.93) is further from unaided Fable (0.40–0.47) than bare Opus is (0.44–0.45).
- **Like Fable with a reviewer: closer.** Reviewed Fable scored 0.86 on extraction tasks. That anchor is weak and partly circular: D1–D11 were catalogued from those same traces, and it rests on 4 tasks, one run and one judge.
- **On outcome quality:**
  - **Better:** blind judges rate the skill's plans higher on questions, risk handling and (v2) proportionality, with no scope creep.
  - **Worse:** they do not catch more planted traps than bare Opus. Grounding drops (4.75 → 4.08 for v2), and so does actionability (4.83 → 4.17).
  - **Mixed:** overall rank. One judge ranks bare Opus above both skill versions.
- **Caveats:**
  - **Sample:** 9 held-out tasks, 2 runs each, 2 judges.
  - **Recognisable format:** judges can recognise the skill's output format.
  - **Unrecorded effort:** subagent reasoning effort was not recorded.
  - **Shared context:** each arm planned 2–4 tasks in one context.
  - **Forced read:** the skill was delivered by a forced read, so triggering from its `description` is untested.
- **Where it helps:** most on multi-phase, risky or ambiguous work, and least on code-reading-heavy brownfield tasks.

## Known gaps and next steps

1. **Grounding.** Add an opener slot for "facts found that contradict or narrow the request" (missing component, missing data, absent auth), and keep failure-mode lines inside steps only.
2. **Coverage of the first step.** Check that the chosen default works for the user's actual workflow. For example, a header token cannot be sent by a browser download link.
3. **Sample size.** Re-measure with more tasks and runs, and use judges blind to output format (for example, normalise headings before judging).

## Where everything is

- `research/extraction/`: tasks, raw traces (with and without the advisor), Fable's self-report, delta analysis.
- `research/evaluation/round1/`, `round2/`: tasks, answer keys, all runs, judge JSON, mapping, `scores.txt`, frozen skill snapshots (v1, v2).
- `research/evaluation/*.py`: blinding and scoring scripts.
- `research/fixtures/shopmini/`: the small repository used by brownfield tasks.
