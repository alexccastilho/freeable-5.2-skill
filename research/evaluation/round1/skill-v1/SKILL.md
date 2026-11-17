---
name: freeable-planning
description: Use when about to plan or start a feature, migration, refactor, incident fix, vague request, project (software or not), or any other multi-step task before acting; when deciding how much planning a request deserves, including small changes that may need no plan at all; and when a plan must be produced without being able to ask the user clarifying questions.
---

# Freeable Planning

## Overview

You already plan competently: you look before asking, attach a default to each question, phase the work, verify, and plan rollback. Keep doing all of that. This skill changes the shape of the plan in five places: what the first sentences say, how large the change is, how defaults are stated, where the stop conditions sit, and how much ceremony a small task gets.

**Core principle:** from the first three sentences the reader knows where the work is; they can start without answering anything; and every risky step says what would stop it.

Origin: distilled from paired planning traces of Fable 5.2 and a baseline model on eight tasks, one sample each.

## Size the response first

| Observable condition | The response is |
|---|---|
| A handful of lines, fully specified, reversible, nothing sent, deleted or deployed | **The change itself.** No plan, no questions section. |
| A bounded change to an existing system (one feature, a few files) | **The smallest change**, as edits or an exact diff, with its defaults and verification. Not a phased project. |
| Several phases; or production, data or other people affected; or the goal is unclear | **A plan** that follows the output contract below. |

Trivial-task recipe: the change, what you checked, what you left alone as a one-line offer ("Say if you want X renamed too"), the verification. A question you answered by looking is not asked.

## Procedure

1. **Look.** Read what is available (repository, files, conversation) before planning. Anything you can find is not a question.
2. **Find where the work is.** Name the one or two facts that set most of the effort or risk. Test them against the surface of the request: if it stresses a number or technology ("8M rows", "zero downtime"), ask whether the difficulty is there. If it is elsewhere, say so in the opener and give that part its own phase, sized to match. If the surface reading is right, say that plainly; do not manufacture a twist.
3. **Check for a cheaper path.** If the request names a solution and a materially cheaper route reaches the likely goal, state it in one paragraph at the top: what it is, what it costs, when it is the right choice. Make it question 1 with the request as its default. Then plan what was asked, in full. Once per plan.
4. **Turn unknowns into defaults.** For each unknown choose the default whose wrong guess does least damage or is easiest to correct. State it as what the plan does about it, not why it is probable. Where the work allows, make it a setting, and add one observation that settles it without the user. If the unknown is a number you have no basis for (budget, target, duration), give a structure that works for any value and leave the number out. A near-certain default is a stated assumption, not a question.
5. **Rank the questions.** At most five. Name the two to four worth answering first and what answering buys. Next to a structure-changing question, write the branch.
6. **Cut to the smallest change.** Fewest files, limits, dependencies and refactors that satisfy the request. Everything else you found goes in a closing list: one sentence on why it matters, and that it was not touched. Keep reporting those findings. Scope restraint applies to features; it never removes rollout safety or verification for the change itself.
7. **Write the gates.** If a step touches production, data or other people, write the observable condition that halts or reverses it, with a number where one exists: a go/no-go list before an irreversible step, an abort rule inside the step, a revert rule after it. A diagnosis counts as proven when the fault reproduces with the suspected cause present and not with it absent. Destructive steps wait for sign-off whatever the default.
8. **Flag once, at the point of use.** A specific recalled from memory that may be out of date gets one sentence beside it naming the check that settles it. Code you wrote and did not run: say so in the first paragraph and point at the assertion most likely to be wrong. Convert relative dates ("last Tuesday") to a date and state your reading.
9. **Justify the order; list the losses.** Where a reader would be tempted to reorder, give the reason in one sentence. Announcements follow the commitment they depend on. If you omit a standard step, say so and why. If the plan changes architecture or process, list what the current arrangement gives for free and what replaces each item, and what the fix itself will now hide.
10. **Cut.** Delete any section with nothing in it. The moves above add sentences, not sections: the plan is no longer than the one you would have written without them.

## Output contract (plans)

Parts in this order. Slots marked *if* appear only when their condition holds.

```
1. OPENER (1-3 sentences): the recommendation, or where the work is.
   *if a cheaper path exists*: one paragraph, then "I plan what you asked below."
   *if relative dates*: "I read 'last Tuesday' as <date>."
2. NOT SEEN / NOT RUN (1 line): what the plan rests on unseen.
3. QUESTIONS (max 5), each:
   Q. <question> - Default: <what the plan does>.
      *if structure-changing*: If <other answer>, <what changes>.
   Answer first: Qx, Qy - <what that buys>.
4. PLAN: steps or phases in execution order, each naming real things and its check.
   *if incident*: step 0 is containment and evidence preservation.
   *if parameters are guessed*: observe-only stage before enforcement.
   *if order is non-obvious*: one sentence of reason.
5. *if an irreversible step*: GO / NO-GO, all conditions measurable;
   abort rule inside the step.
6. *if architecture or process changes*: WHAT YOU LOSE -> what replaces it.
7. FOUND, NOT TOUCHED: adjacent problems, one line each.
8. NEED FROM YOU: the specific artefacts or answers that firm the plan up.
```

The plan is complete on its defaults. It never ends with "once you answer, I will start".

## One example (migrate `users`, 8M rows, MySQL to PostgreSQL, zero downtime)

Baseline opener: "Keep MySQL as the source of truth while a replication stream fills a Postgres copy. Prove the two match. Then move reads, then writes." The cross-table problem appears in question 1 and again in a "cross-cutting concerns" bullet near the end.

Target opener: "Two things shape the plan more than the row count. Only `users` is moving: every foreign key, join and transaction that spans `users` and a table staying in MySQL stops working. Untangling that is most of the effort, and it has to be done before any data moves. 8M rows is small: the backfill takes minutes to an hour."

The plan then gives that work its own phase ("Make the application ready (the bulk of the work)"), shipped before the new database holds data. The cutover carries an abort rule: if the write hold has not completed in 15 seconds, release it with the flag still on MySQL and try another day.

## Quick reference

| Situation | Do |
|---|---|
| Request stresses the wrong difficulty | Opener relocates the effort; that part gets its own phase |
| Request names a solution, cheaper route exists | One paragraph first, question 1, then the requested plan |
| Unknown blocks the work | Fail-safe default + setting + settling check; proceed |
| Number you cannot know | Structure (percentage split, "targets after baseline"); no invented figure |
| Step touches production or data | Go/no-go, abort rule, or revert rule with a threshold |
| Recalled option name, version, config key | One flag beside it, with the check |
| Adjacent problem found | Closing list, not the diff |
| Incident | Contain and preserve evidence before diagnosing |
| Guessed limits or thresholds | Log-only or shadow stage, then enforce |
| Large migration | Include operational items: secrets and per-customer config, personal data in the pipeline, contracts, who does the work |

## Common mistakes

- A forced "the real problem is elsewhere" opener when the request is what it appears to be.
- Second-guessing the request more than once, or withholding the requested plan.
- Dropping a staged rollout or a check in the name of a small change.
- Gates, loss tables and risk tables on local, reversible work.
- Hedges scattered through the text in place of one flag at the point of use.
- Seven or eight questions when two change the plan.
- A hedged estimate, target or budget with no basis. It gets quoted back.
- A default that fails open, or a plan that waits on an answer.
- A longer plan than you would have written without these moves.

## References

- `references/question-bank.md`: questions by task type, each with a default written as a plan action. Read when drafting part 3.
- `references/gates-and-defaults.md`: sentence patterns for gates, defaults and flags. Read when a step touches production or data, or an unknown blocks the work.
- `references/task-type-notes.md`: per task type, what to add and which existing strengths to keep.
- `references/worked-examples.md`: before and after on the eight source tasks.
