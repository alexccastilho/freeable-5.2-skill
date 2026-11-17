---
name: freeable-planning
description: Use when about to plan or start a feature, migration, refactor, incident fix, vague request, project (software or not), or any other multi-step task before acting; when deciding how much planning a request deserves, including small changes that may need no plan at all; and when a plan must be produced without being able to ask the user clarifying questions.
---

# Freeable Planning

## Overview

You already look before asking, attach defaults to questions, phase the work, verify, and plan rollback. Keep that. This skill sets the opener, the path taken when nobody answers, the form of defaults, the stop conditions, and the length.

**Core principle:** the first three sentences say where the work is; left unanswered, the plan does the cheapest thing that is safe to undo; every risky step says what would stop it.

Origin: the planning pattern observed in Fable 5.2 traces produced with a review step, plus fixes from a blind evaluation of v1. It is not that model's unaided default behaviour; `CHANGELOG.md` has the comparison.

## Size the response first

| Observable condition | The response is |
|---|---|
| A handful of lines, fully specified, reversible, nothing sent, deleted or deployed | **The change itself.** No plan, no questions section. |
| A bounded change to an existing system (one feature, a few files) | **The smallest change**, as edits or an exact diff, with its defaults, failure modes and verification. |
| Several phases; or production, data or other people affected; or the goal is unclear | **A plan** that follows the output contract below. |

Trivial-task recipe: the change, what you checked (including a search for variants and other uses), a one-line offer for what you left alone ("Say if you want X renamed too"), the verification.

## Procedure

1. **Look.** Read what is available (repository, files, conversation). What you find is a fact, and stops being a question.
2. **Find where the work is.** Name the one or two facts that set most of the effort or risk. If the request stresses a number or technology ("8M rows") and the difficulty is elsewhere, say so in the opener and give that part its own phase. If the surface reading is right, say so in one sentence.
3. **Choose the default path.** When the request names a solution and a cheaper route may reach the goal, test three predicates:
   - **(a)** the requested path takes weeks of work, or has a step that a revert or a flag cannot undo (data moved or merged, an architecture replaced, a contract signed);
   - **(b)** the cheaper path can be undone and leaves the requested path open;
   - **(c)** the cheaper path delivers every outcome the request states, and you would recommend it for the most likely driver.

   | Predicates | Default, planned in full | The other path |
   |---|---|---|
   | (a), (b) and (c) all hold | **The cheaper path** | The request, as a branch of six lines or fewer: its phases, its largest cost, the answer that selects it |
   | Any one fails, or the user says the alternative was considered | **The request** | The cheaper path, in one paragraph: what it is, what it costs, when it is right |

   The choice is question 1, and the opener names the default. If the cheaper path is a first stage of the requested one, phase it that way, with the irreversible stage behind a decision gate. A plan that says the cheaper path is usually right has it as the default.
4. **Turn unknowns into defaults.** Choose the default whose wrong guess does least damage or is noticed soonest, and state it as what the plan does. Where the work allows, make it a setting and add one observation that settles it without the user. For a number with no basis (budget, target, duration), give a structure that works for any value. A near-certain, cheap-to-correct default is a one-line assumption.
5. **Rank the questions.** At most five, filled in this order:
   - **Driver.** When the reason behind the request sets how far the work goes (which design, how much is migrated or deleted, where it stops), "What is driving this?" is question 1 or 2, with its branch.
   - **Tolerance.** How stale, how slow, how much loss or pause is acceptable. An answer that selects the design holds a place in the five.
   - **Harm or shrink.** One fact that would make the default harmful or the plan much smaller.
   - **Access and resources.** What you can see, who does the work.
6. **Smallest change, full failure coverage.** Use the fewest files, limits, dependencies and refactors that satisfy the request; adjacent findings go in a closing list. Then run the standard failures of this kind of change: many callers at the same moment, expiry and retry, partial failure, stale or lost data, overload, a dependency down, an unknown caller. Each one that applies gets one line in its step: the protection, or why it does not apply. "Smallest" limits features; failure coverage, staged rollout and verification of the change itself stay whole.
7. **Write the gates.** When a step touches production, data or other people, write the observable condition that halts or reverses it, with a number where one exists: a go/no-go list before an irreversible step, an abort rule inside it, a revert rule after it. A diagnosis is proven when the fault reproduces with the suspected cause present and not without it. Destructive steps wait for sign-off.
8. **Flag once, at the point of use.** A specific recalled from memory (option name, version, config key) gets one sentence beside it naming the check that settles it. Unrun code is declared in the opener, with the assertion most likely to be wrong. Relative dates become dates, with your reading stated.
9. **One line each, when the condition holds.** The reason for an order a reader would want to change. A standard step you left out, and why. For a change of architecture or process: what the current arrangement gives for free and what replaces it.
10. **Apply the length rule.**
    - No longer than the plan you would write without this skill. Ceiling: about 1,000 words for a multi-phase plan, 500 for a bounded change, code excluded.
    - Each conditional part is one line; the one that holds the main risk may run longer.
    - A heading has at least three lines under it, or folds into its neighbour. A table stays when the reader will look something up in it.
    - Each risk appears once, in its gate or its step.
    - Delete any paragraph the reader could act without.

## Output contract (plans)

Three parts, and a fourth when there are findings. *If* slots appear only when their condition holds.

```
1. OPENER (one paragraph): the default path and where the work is;
   what the plan rests on unseen or unrun.
   *if a cheaper path exists*: the answer that selects the other path.
   *if relative dates*: "I read 'last Tuesday' as <date>."
2. QUESTIONS (max 5), each:
   Q. <question> - Default: <what the plan does>.
      *if structure-changing*: If <other answer>, <what changes>.
   Answer first: Qx, Qy - <what that buys>.
3. PLAN: steps or phases in execution order. Each names real things,
   its check, and the failure modes it covers.
   *if incident*: step 0 is containment and evidence preservation.
   *if parameters are guessed*: observe-only stage before enforcement.
   *if an irreversible step*: go/no-go list; abort rule inside the step.
   *if step 3 chose the cheaper path*: the request as a branch.
4. *if findings*: FOUND, NOT TOUCHED, one line each.
```

## One example (migrate `users`, 8M rows, MySQL to PostgreSQL, zero downtime)

The baseline opened with the replication approach and left the cross-table problem to a late bullet. Target opener: "Two things shape the plan more than the row count. Only `users` is moving: every foreign key, join and transaction that spans `users` and a table staying in MySQL stops working. Untangling that is most of the effort, and it has to be done before any data moves. 8M rows is small."

That work gets its own phase. The tolerance question holds its place: "What does 'zero downtime' allow? Default: one hold of about 10 seconds. If no pause at all, the cutover changes to application dual-writes." The cutover carries an abort rule: if the hold has not completed in 15 seconds, release it with the flag still on MySQL.

## References

- `references/question-bank.md`: the filter, the cap, questions by task type.
- `references/gates-and-defaults.md`: patterns for default path, failure coverage, gates, defaults, flags.
- `references/task-type-notes.md`: what to add and keep per task type.
- `references/worked-examples.md`: the eight source tasks, before and after.
