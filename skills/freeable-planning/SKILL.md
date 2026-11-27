---
name: freeable-planning
description: Use when about to plan or start a software feature, migration, refactor, incident fix, performance or improvement work, a new system, website or app, a vague request, a project outside software (an event, a move, a launch), or any other task with several steps or that touches production, data or other people; and when a plan must be produced without being able to ask the user clarifying questions.
---

# Freeable Planning

## Overview

Every plan keeps the basics: look before asking, attach a default to each unknown, phase the work, verify each step, plan the rollback. The steps below shape the rest.

**Core principle:** the first lines say where the work is and what you found that changes the request; left unanswered, the plan does the cheapest thing that is safe to undo; every risky step says what would stop it; phase 1 ends in steps someone can start today.

## Size the response first

| Observable condition | The response is |
|---|---|
| A handful of lines, fully specified, reversible, nothing sent, deleted or deployed | **The change itself.** No plan, no questions section. |
| A bounded change to an existing system (one feature, a few files) | **The smallest change as an exact diff**, after the facts that narrow the request, with its defaults and verification. |
| Several phases; or production, data or other people affected; or the goal is unclear | **A plan** that follows the output contract below. |

Trivial-task recipe: the change, what you checked (variants and other uses), a one-line offer for what you left alone ("Say if you want X renamed too"), the verification.

## Procedure

1. **Look, and test the premise.** Read what is available (repository, files, conversation). What you find is a fact, and stops being a question. Run four checks on what the request takes for granted:
   - the component it names exists;
   - the data the result needs is in the schema and written on every write path;
   - the access control it presumes is in place;
   - the fields it would rely on are set by every writer.

   Each check that fails is a **premise fact**: what you saw, where (file, line, table), and what it does to the request. With nothing to read, say so and name the command that would run the check.

   When you have tools, verify before you assert: search for the callers, open the file, run the tests, and report the result. A claim left unchecked carries a flag (step 8).
2. **Find where the work is.** Name the one or two facts that set most of the effort or risk. If the request stresses a number or technology ("8M rows") and the difficulty is elsewhere, the opener says so and that part gets its own phase. If the surface reading is right, say so in one sentence.
3. **Choose the default path.** When the request names a solution and a cheaper route may reach the goal, test three predicates:
   - **(a)** the requested path takes weeks of work, or has a step that a revert or a flag cannot undo (data moved or merged, an architecture replaced, a contract signed);
   - **(b)** the cheaper path can be undone and leaves the requested path open;
   - **(c)** the cheaper path delivers every outcome the request states, and you would recommend it for the most likely driver.

   | Predicates | Default, planned in full | The other path |
   |---|---|---|
   | (a), (b) and (c) all hold | **The cheaper path** | The request, as a branch of six lines or fewer: its phases, its largest cost, the answer that selects it |
   | Any one fails, or the user says the alternative was considered | **The request** | The cheaper path, in one paragraph: what it is, what it costs, when it is right |

   The choice is question 1, and the opener names the default, once. If the cheaper path is a first stage of the requested one, phase it that way, with the irreversible stage behind a decision gate.
4. **Turn unknowns into defaults, then walk each through real use.** Choose the default whose wrong guess does least damage or is noticed soonest, and state it as what the plan does. Where the work allows, make it a setting and add one observation that settles it. For a number with no basis (budget, target, duration), give a structure that works for any value. Then trace the default from whoever triggers it: which client (a browser link or form, a phone, a CLI, a scheduled job, staff on a shared machine or address), and whether that client can supply what the default requires. A default that fails the walk is replaced, and the plan says which use decided it.
5. **Rank the questions.** At most five, filled in this order:
   - **Driver.** When the reason behind the request sets how far the work goes, "What is driving this?" is question 1 or 2, with its branch.
   - **Tolerance.** How stale, how slow, how much loss or pause is acceptable. An answer that selects the design holds a place in the five.
   - **Harm or shrink.** One fact that would make the default harmful or the plan much smaller.
   - **Access and resources.** What you can see, who does the work.
6. **Smallest change, full failure coverage, inside the steps.** Use the fewest files, limits, dependencies and refactors that satisfy the request; adjacent findings go in the closing list. Run the standard failures of this kind of change: many callers at the same moment, expiry and retry, partial failure, stale or lost data, overload, a dependency down, an unknown caller. Each one that applies becomes one line in the step it protects, naming the protection. "Smallest" limits features; failure coverage, staged rollout and verification stay whole. Each step names the exact command, query or observation that verifies it.
7. **Write the gates.** When a step touches production, data or other people, write the observable condition that halts or reverses it, with a number where one exists: a go/no-go list before an irreversible step, an abort rule inside it, a revert rule after it. A diagnosis is proven when the fault reproduces with the suspected cause present and not without it. Destructive steps wait for sign-off.
8. **Flag once, at the point of use.** A specific recalled from memory (option name, version, config key, a library's default behaviour) gets one sentence beside it naming the check that settles it. A command or query you did not run names the version it assumes. Unrun code is declared in the opener, with the assertion most likely to be wrong. Relative dates become dates, with your reading stated.
9. **Write the first steps.** Phase 1 closes with three to six actions that need no answer, each naming a real file and function, a command, a query or an edit. For a bounded change to code you have read, this is the diff. For a system you have not seen, it is the exact command or query that produces the first artefact; invent no file names.
10. **One line each, when the condition holds.** The reason for an order a reader would want to change. A standard step you left out, and why. For a change of architecture or process: what the current arrangement gives for free and what replaces it.
11. **Apply the length rule.**
    - Count the workstreams: the separate outcomes the request asks for. Phases of one outcome are one workstream. Prose, with code and diffs outside the count:

      | Response | Prose |
      |---|---|
      | Bounded change | about 500 words |
      | Plan, one workstream | 800 to 1,500 words |
      | Plan, several workstreams | 800 to 1,500 words per workstream, plus the opener, the questions and one first-steps block |

    - Words go to decisions, checks and gates. Premise facts and first steps are paid for by cutting restatement.
    - Say each thing once, where it is used. A step is a verb, the real thing it changes, and its check.
    - A heading has at least three lines under it, or folds into its neighbour. The opener is prose, with no "Summary" heading above it.
    - Each risk appears once, in its gate or its step.
12. **Review the draft, then send it.** Re-read it as a senior reviewer who expects it to fail in production and has the repository open. Fix every failed check in the draft. The output is the corrected plan; the review leaves no section or mention in it.

    | Check | Passes when |
    |---|---|
    | Premise | Every fact you read that contradicts or narrows the request is in the opener or part 2, with its location |
    | Use | Each default was traced from the real client and can be supplied by it |
    | Path | The three predicates, re-tested on the finished draft, select the path that is planned in full |
    | Stops | Each step touching production, data or people has a check, a gate or a rollback |
    | Failures | Each standard failure that applies is one line inside its step; no separate failure list exists |
    | Questions | Five or fewer; driver, then tolerance, first; each has a default; the plan is complete without answers |
    | First steps | Phase 1 ends in files, commands, queries or edits; none says only "audit" or "investigate" |
    | Invention | Every number, version, option name, file name and library default was read, was run, or carries a flag; every unrun command or query names the version it assumes |
    | Size | Inside the band for its workstream count; no heading under three lines; no risk stated twice |

    For a trivial change, one pass over three checks: the edit is complete (variants and other uses searched), nothing was invented, nothing was added.

## Output contract (plans)

*If* slots appear only when their condition holds.

```
1. OPENER (one paragraph): the default path and where the work is;
   what the plan rests on unseen or unrun.
   *if a cheaper path exists*: the answer that selects the other path.
   *if relative dates*: "I read 'last Tuesday' as <date>."
2. *if you read code or material*: WHAT I FOUND THAT CHANGES THE REQUEST
   (what does not change it goes in part 5).
   One line per premise fact: <fact> (<where>) -> <effect on the request>.
   Fewer than three: fold them into the opener. None: "The request
   matches what I read" in the opener.
3. QUESTIONS (max 5), each:
   Q. <question> - Default: <what the plan does>.
      *if structure-changing*: If <other answer>, <what changes>.
   Answer first: Qx, Qy - <what that buys>.
4. PLAN: phases in execution order. Each step names the real thing it
   changes, its check, and in the same step the failure it covers.
   Phase 1 ends with FIRST STEPS.
   *if incident*: step 0 is containment and evidence preservation.
   *if parameters are guessed*: observe-only stage before enforcement.
   *if an irreversible step*: go/no-go list; abort rule inside the step.
   *if step 3 chose the cheaper path*: the request as a branch.
   *if step 3 kept the request and a cheaper path exists*: the cheaper
   path, one paragraph: what it is, what it costs, when it is right.
5. *if findings*: FOUND, NOT TOUCHED, one line each.
   Fewer than three: one closing sentence, no heading.
```

## Two examples

**Migrate `users`, 8M rows, MySQL to PostgreSQL, zero downtime.** Opener: "Only `users` is moving: every foreign key, join and transaction that spans `users` and a table staying in MySQL stops working. Untangling that is most of the effort. 8M rows is small." Tolerance question: "What does 'zero downtime' allow? Default: one hold of about 10 seconds. If no pause at all, the cutover changes to application dual-writes." The cutover step holds its own abort rule: hold not complete in 15 seconds, release with the flag still on MySQL. First steps, no schema seen: the `information_schema.KEY_COLUMN_USAGE` query for foreign keys that reference `users`, and a code search for joins and writers.

**Add rate limiting to a small Express API.** Premise facts: "No route has authentication (`src/server.js`), and `userId` comes from the request body -> the client address is the only key a limit can use." "No deployment configuration in the repository -> I cannot see whether a proxy sits in front." Use walk: warehouse staff upload the end-of-day file from one office address, so a strict per-address limit there blocks them; those routes stay on the loose limit. First steps: the diff to `src/server.js`.

## References

- `references/question-bank.md`: the filter, the cap, example questions by task type. Read when drafting part 3.
- `references/gates-and-defaults.md`: a quick-reference table, then patterns for premise facts, default path, use walk, failure lines, gates, flags, first steps. Read when a step touches production, data or people, or an unknown blocks the work.
- `references/task-type-notes.md`: what to add and keep per task type. Read once the task type is known, before drafting.
- `references/worked-examples.md`: the eight source tasks, before and after. Read when unsure what a slot looks like in a finished plan.
