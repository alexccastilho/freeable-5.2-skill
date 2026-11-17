# Changelog

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
