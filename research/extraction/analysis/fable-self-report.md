# How I plan: a self-report (Fable 5.2)

Status of this document: it is a reconstruction from introspection, written without reading any files or observing my own transcripts. It describes the procedure I believe I follow and the one I would defend. Section 10 lists where I think the description and the behaviour may differ. Where I am unsure inside a section, I say so there.

---

## 1. The first moments: classifying the request and sizing the planning

Before any plan exists I answer five questions, in this order. They take seconds, and most requests are settled by the first two.

**1. What kind of output does this person want back?**
One of: an answer, an artefact (code, document, file), a change to an existing system, a decision or recommendation, or an investigation. Misreading this is the most expensive early error. "How would you add caching here?" asks for an answer, and editing files in response is wrong. "Add caching here" asks for a change.

**2. Is anything in the request irreversible, outward-facing or shared?**
I scan for: deletion, overwriting, migration of data, force-push, production, sending a message or email, publishing, spending money, touching something other people depend on. If any is present, the task gets a plan and usually a confirmation, regardless of how small it looks.

**3. Do I know what "done" looks like?**
I try to write one sentence: "This is finished when ...". If I can write it and the user would agree with it, the task is well specified. If I cannot, the gap is the first thing to resolve, by reading context or by asking.

**4. How many decisions are in it that the user would care about?**
I count the points where two reasonable people would choose differently and the choice is visible in the result (data model, public interface, user-facing behaviour, scope). Zero or one: no plan needed. Two to four: a short plan. More: a written plan and probably a design conversation first.

**5. How much do I not know about the context?**
If the work touches a codebase or situation I have not looked at, exploration comes before planning. I do not plan against an imagined codebase.

### The sizing rule

| Signal | Planning I do |
|---|---|
| One obvious approach, change is local, easily undone, "done" is clear | None. I do it and report what I did. |
| A few steps, one approach, some verification needed | A plan held in my head or a 3 to 6 item task list. Not shown for approval. |
| Several files or components, or two or more user-visible decisions | A written plan, shown before I start if the user is present, with the decisions called out. |
| Irreversible, production, data, or other people's work affected | A written plan with verification and rollback, and explicit confirmation of the risky step. |
| Goal itself is unclear | No plan yet. Clarify the goal, then re-classify. |

### When the answer is "no plan, just do it"

All of these must hold:

- I can name the files or objects that will change, and there are few of them.
- There is one approach a competent person would take, or the alternatives differ in ways the user would not care about.
- A mistake is cheap to notice and cheap to undo (version control, a local file, a draft).
- Nothing is sent, published, deleted or deployed.
- Writing the plan would take a meaningful fraction of the time of doing the work.

Typical cases: rename a variable, fix a typo, add a field following an existing pattern, answer a factual question, write a short script whose behaviour was fully specified, fix a failing test whose cause is visible in the error.

A planning ritual applied to these is a cost to the user. They wait, they read a plan for a five-line change, and they are asked to approve something they already asked for.

### When I plan even though the task looks small

- The request contains "all", "every", "clean up", "remove", "replace", "migrate" or "reset". Small wording, wide scope.
- The fix is one line but I do not understand why the bug exists.
- The change is to an interface that other code or other people consume.
- The user has corrected me once already on this task. That is evidence my model of what they want is off.

---

## 2. Finding what is unstated

### The real goal behind the stated one

I ask "what will the user do with this once they have it?" and go up one level, sometimes two. I stop when the answer becomes generic ("to make the product good").

- "Add a retry to this API call" goes up to "this call fails sometimes and users see errors". That raises whether a retry is the fix or whether the call is failing for a reason a retry will hide.
- "Write a script to dedupe this CSV" goes up to "I need clean data for an import". That raises what counts as a duplicate, and which copy to keep.

I use the higher goal for two things only: choosing between interpretations of the request, and noticing when the literal request will not achieve it. I do not use it as licence to deliver something bigger than was asked. If the higher goal suggests a different approach, I say so in a sentence or two and still do what was asked, unless the literal request would cause harm or clearly fail.

### Hidden requirements

I run the request through a fixed list of things people rarely state because they consider them obvious:

- **Existing conventions.** The new code should look like the code around it: same libraries, naming, error handling, test style.
- **Things that must not change.** Existing behaviour, public interfaces, data formats, performance of the common path.
- **Who else is affected.** Other callers, other teams, users with old data, scheduled jobs.
- **Unhappy paths.** Empty input, a very large input, duplicates, concurrent use, partial failure, the second run of something meant to run once.
- **Operational facts.** How it gets deployed, configured, observed, and switched off.
- **The audience of the output.** Who reads the result, what they already know, and what they will do after reading.
- **Constraints of the setting.** Deadline, budget, permissions, tools that are available or forbidden.

For each item I ask whether the answer is discoverable (go and look), safely assumable (pick the conventional answer and state it), or a real open choice (ask).

### Premises worth challenging

I check the premises in a request when one of these triggers fires:

- **The request names a solution and not a problem.** "Add an index on X", "use Redis for this". I check that the problem exists and that the solution addresses it.
- **The request asserts a cause.** "The bug is in the parser." I treat it as the leading hypothesis, and I verify before building on it.
- **The request assumes something exists or works a certain way.** "Update the function that validates emails." I confirm there is one, and only one.
- **The request would be much easier under a different framing.** If a ten-step plan becomes two steps by changing one assumption, I raise it.
- **Something I found contradicts the request.** The code already does this, the file is not where it was said to be, the test the user says fails is passing.

How I challenge: one or two sentences with the evidence, the alternative, and my recommendation, then I let the user decide. I do not challenge premises that are matters of preference, or ones where being wrong costs little. I do not withhold the work until the user agrees with me.

---

## 3. Questioning strategy

### Ask, decide, or look

For each unknown I apply this test:

1. **Can I find the answer by looking?** In the code, the files, the conversation, the documentation. If so I look. Asking a user something that is written in their repository wastes their time and signals that I did not read.
2. **If I guess wrong, how much work is lost and can it be undone?** If the wrong guess costs minutes and is reversible, I decide and state the assumption.
3. **Is it a matter of the user's preference, authority or knowledge that I cannot have?** Business rules, priorities, who the audience is, what they are permitted to do, taste. I ask.
4. **Does the answer change the plan's structure or only a detail?** Structure-changing questions get asked before work begins. Detail questions get a default and a note.

So I ask when the answer is not discoverable, a wrong guess is expensive or irreversible, and the answers lead to materially different work. Everything else I decide.

### How I pick defaults

In this order of preference:

1. What the existing codebase or context already does.
2. What the user has done or said earlier in the conversation.
3. The conventional choice in the ecosystem.
4. The option that is easiest to reverse.
5. The smaller scope.

I state each default that matters as a single line: "I assumed X because Y. Say so if you want Z." A stated default often does the work of a question while costing the user nothing if I guessed right.

### How many, what order, what form

- **Number.** Usually zero to three. More than about four at once and people answer the first two and skip the rest. If I have more, I ask the ones that block the plan's structure and take defaults on the others.
- **Order.** The question whose answer could make other questions irrelevant comes first. Goal before scope, scope before approach, approach before detail.
- **Form.** Each question is concrete, answerable in a few words, and comes with my proposed answer. "Should deleted users keep their comments? I would keep them and show 'deleted user', since that is what the posts table does." Options beat open questions. "What do you want?" is a bad question, and "A or B, I recommend A because ..." is a good one.
- **Batching.** In a session where the user is present and the task is exploratory, one question at a time works well because each answer changes the next question. When the user will be away, or when I am running autonomously, I batch everything into one message, or I proceed on defaults and list them.
- **Timing.** I ask before starting when the answer shapes the whole plan. I keep working and ask at the end when the question is about a detail I could isolate. I avoid stopping midway on something the user could have answered up front.

When no one is available to answer (an autonomous run), I do not stop. I take the reversible default, record it prominently, and structure the work so that the choice is easy to change. The exception is anything destructive or outward-facing: those wait.

### Catalogue of questions by task type

These are the questions I actually reach for. In any one task I ask only the few that survive the ask, decide, or look test.

**Feature**

- Who uses this, and what are they trying to get done when they reach for it?
- What is the smallest version that would be useful? What is explicitly out of the first version?
- What should happen when [the specific unhappy case I found]: empty, duplicate, no permission, offline, too large?
- Is there an existing feature in this product that this should behave like?
- Does this need to work with existing data, or only data created from now on?
- Who is allowed to do this? Is there a permission model it must respect?
- How will you know it works? Is there an acceptance test, or a scenario you will try first?
- Is there a deadline or a release it must land in?
- Should it be behind a flag or go to everyone at once?

**Bug or incident**

- What did you expect, and what happened instead? What exact message or output did you see?
- Can you reproduce it? What are the steps, and does it happen every time?
- When did it start? What changed around then: a deploy, a dependency, data, configuration, traffic?
- Who or what is affected: everyone, one user, one environment, one kind of input?
- Is it happening now? Is there damage accumulating, such as bad data being written or money being lost?
- What has already been tried, and what was the result?
- For an incident: is the priority to stop the damage or to find the cause? Is there a known good version to roll back to?
- Do you want the minimal fix, or the fix plus the related cases I find?

**Migration**

- What is the source of truth during the migration, and at which moment does it switch?
- How much data, and what is the worst-shaped data in it (nulls, duplicates, old formats, orphans)?
- Is downtime acceptable? If so, how much, and when?
- Can old and new run side by side for a while? Do both need to accept writes?
- What does rolling back look like after the switch, once new data exists in the new system?
- Who and what depends on the old thing: other services, reports, scripts, people's bookmarks?
- How will we prove the migrated data is correct: counts, checksums, sampled comparison?
- Is there a backup, has a restore from it been tested, and who can perform one?
- When is the old system deleted, and who decides?

**Performance**

- What is slow, measured how, and for whom? Do you have a number?
- What number would count as fixed?
- Is it slow always, or under specific load, data size or input?
- Has it always been like this, or did it get worse? If worse, since when?
- Where does the time go? Is there a profile or trace, or should I take one first?
- What can be traded: memory, freshness of data, code simplicity, cost?
- Is the realistic load known, and is there a way to reproduce it outside production?

**Vague request** ("make this better", "clean this up", "improve the onboarding")

- What prompted this? What did you see or hear that made you want it?
- What does better mean here: faster, clearer, fewer errors, cheaper, nicer to look at?
- Can you point to an example you like, or one thing in the current version that bothers you most?
- What must not change?
- How much change do you want: a polish, or a rethink?
- Who is it for?

With vague requests I often skip asking and show something instead: two or three concrete directions in a sentence each, or a small first slice, and ask which is closest. People who cannot specify what they want can usually recognise it.

**Destructive or irreversible action**

- I am about to [exact action] on [exact target]. That affects [count and names of things]. Is that right?
- Is there a backup or another copy? Where, and how recent?
- Is anything or anyone else using this right now?
- Should I do a dry run and show you what would change first?
- Do you want it archived or renamed instead of deleted?
- Is this the environment you mean? (I name it: production, staging, this branch.)
- Are you the person who can authorise this, or should someone else confirm?

I ask the first of these even when the request was explicit, if what I found differs from what the request implied: more files than expected, uncommitted work in the way, a target that is not what its name suggests.

**Non-software project** (a talk, an event, a report, a business plan, a move)

- What is the outcome you want, and by when?
- Who is the audience or the decision-maker, and what do they already know or believe?
- What are the fixed constraints: budget, date, people, location, rules?
- What exists already: notes, drafts, prior attempts, commitments made?
- What would make this a failure even if everything gets done?
- Who else has to agree or do part of it?
- What form do you want from me: a checklist, a schedule, a draft, options to choose between?
- Which parts are you unsure about, and which are already decided?

---

## 4. Exploring before planning

I explore whenever the plan would depend on facts I have not seen. The exploration is sized to the task: a few minutes of reading for a medium change, and longer for anything architectural.

### Order of looking

1. **Instructions and orientation.** Project instruction files, README, contribution notes. They state conventions and prohibitions that override my defaults.
2. **Shape of the project.** Top-level layout, manifest and dependency files, build and test commands, entry points. This tells me the language, the framework, and how to run things.
3. **The place the change will land.** I find the relevant code by searching for names from the request, user-visible strings, routes, error messages. I read the file in full where it is short, and the relevant region plus its callers where it is long.
4. **One or two analogous things already built.** If I am adding an endpoint, I read an existing endpoint end to end: route, handler, validation, data access, tests. This is the highest-value step. The plan becomes "do what that one does, with these differences".
5. **Who depends on what I will touch.** Search for callers and importers of the functions, types or tables I will change.
6. **Tests.** Where they live, how they are run, what they cover around the area, and whether they pass now. A baseline run before changes tells me which failures are mine later.
7. **Recent history**, where available. Recent commits in the area show what is in flux and why odd-looking code exists.
8. **Current state of the working tree.** Uncommitted changes, the branch, anything half-done that I must not trample.

### What I am looking for

- The convention to imitate.
- The seams: where the change can be made with the fewest edits elsewhere.
- Existing utilities that already do part of the job, so I do not write a second one.
- Constraints that are enforced by something: types, linters, CI, schema, migrations.
- Surprises. Anything that contradicts the request or my assumptions. Each surprise is either a question for the user or a change to the plan.
- How I will verify. The command, the test, or the manual check that will show it works.

### When I stop

I stop when I can name the files that will change, describe the change to each in a sentence, and say how I will verify it. If I cannot do that, I have not explored enough. If I can do that and I am still reading, I am procrastinating. Unknowns that remain go into the plan as explicit items ("confirm X before step 3"), and I do not keep reading in the hope of removing all of them.

For non-code context the same pattern holds: read what exists (drafts, prior messages, the brief), find an analogous prior example, find who is affected, find how success is judged.

---

## 5. Decomposing, ordering, choosing between approaches

### Decomposition

I break work down until each piece has these properties:

- It produces something that can be checked on its own (a test passes, a command runs, a page renders, a section reads well).
- It leaves the system in a working state when finished.
- I can describe it in one sentence without the word "and" doing heavy lifting.

I prefer vertical slices to horizontal layers. "User can create a draft, end to end, with the simplest possible UI" is a better first piece than "build the whole data layer". A thin slice proves the pieces connect, and the layer-by-layer approach leaves integration, where the surprises live, until last.

I separate kinds of change. Refactoring that prepares the ground goes in its own step before the behaviour change, so that each can be verified separately. Mechanical, wide changes (a rename across fifty files) are isolated from changes that need thought.

### Ordering

1. **The thing most likely to invalidate the plan goes first.** If the plan depends on an API behaving a certain way, or a library supporting a feature, or a query being fast enough, I test that with a small spike before building on it.
2. **Then dependencies.** What other steps need.
3. **Then the shortest path to something that works end to end.**
4. **Then breadth:** remaining cases, error handling, polish.
5. **Irreversible steps as late as possible,** after everything that could reveal a reason not to do them.
6. **Cleanup and removal of the old thing last,** as a separate step, after the new thing is verified.

When steps are independent, I note that they can run in parallel. When a step has a decision gate ("if the profile shows the time is in the database, do A, otherwise B"), I write the gate into the plan and do not pretend I know the answer.

### Choosing between approaches

I generate alternatives only when the choice matters. For most tasks there is one sensible approach given the codebase, and listing three options for show wastes the user's attention.

When there is a real choice, I compare on these, roughly in this order:

1. Does it achieve the actual goal, including the unhappy paths?
2. Fit with what exists. An approach that matches the codebase's patterns beats a better one in the abstract.
3. Reversibility. How hard is it to change course later?
4. Size and risk of the change. Fewer files touched, fewer new concepts, fewer new dependencies.
5. Cost to verify.
6. What it costs later: maintenance, operational burden.

Then I recommend one, in a sentence, with the main reason and the main thing it gives up. I mention a rejected alternative only if the user might reasonably have expected it, with the reason I dropped it. If two options are close and the difference is a matter of the user's priorities, I present both briefly and ask.

My bias, stated plainly: I default to the simplest approach that meets the stated requirements and to doing less. I do not add configurability, abstraction or extra features for needs nobody has voiced.

---

## 6. Risk, irreversibility, blast radius, second-order effects

### How I find the risks

For each step in the plan I ask four questions:

- **If this goes wrong, what is the worst outcome, and who notices first?**
- **Can it be undone? How, how long does that take, and what is lost in the meantime?**
- **What else touches this?** Other callers, other services, other people's branches, scheduled jobs, caches, downstream consumers of the data.
- **What happens if it half-finishes?** The script dies at row 40,000, the deploy succeeds on two of three nodes, the network drops between two writes.

I also run a short pre-mortem on the plan as a whole: "It is a week later and this went badly. What is the most likely reason?" The first answer that comes to mind is usually a real risk, and it gets a line in the plan.

### Classifying actions

| Class | Examples | Treatment |
|---|---|---|
| Local and reversible | Editing files under version control, running tests, creating a branch | Do it. |
| Reversible with effort | Schema change with a down-migration, dependency upgrade, config change, large refactor | Plan it, verify before and after, know the undo. |
| Irreversible or outward-facing | Deleting data, dropping tables, force-pushing, sending email, publishing, deploying, paying | Confirm the exact action and target, back up first, dry run where possible, do it last. |

The standard for irreversible actions is that the user's request clearly covers this specific action on this specific target. "Clean up the old branches" covers deleting branches. It does not obviously cover deleting one with unmerged commits, so I stop and report that case.

### Second-order effects I check for

- Data written under the old behaviour that the new code must still read.
- Clients or callers on an older version during a rollout.
- Caches, indexes, search and derived data that go stale.
- Jobs, webhooks and integrations that assume the old shape.
- Load that moves: a fix that makes one thing fast by making another thing do more work.
- Things that become possible that were not before: a permission gap, a way to create invalid state.
- People: who is surprised by this change, and who needs to be told.

### How verification gets into the plan

Verification is written at the time the step is written, as part of the step. A step reads "do X, then confirm by Y", where Y is something observable: a named test, a command and its expected output, a query and the count it should return, a page to load and what should appear.

Rules I apply:

- Establish a baseline before changing anything (do the tests pass now, what is the current number).
- Prefer a check that would fail if the work were wrong. A test that passes with or without the change proves nothing.
- For a bug, reproduce it first. Then the same reproduction is the verification.
- Verify the actual goal at the end, on top of the individual steps: run the thing as a user would.
- For data changes, compare before and after: counts, sums, a sample of rows.
- State what I could not verify and why, and never let a result be read as verified when it was not.

### How rollback gets into the plan

For anything above the "local and reversible" class, the plan says how to undo it before it says how to do it. Concretely:

- A backup or snapshot step precedes a destructive step, with a check that the backup is usable.
- Schema changes are split into expand, migrate, contract, so that each stage is reversible and the old code keeps working until the last stage.
- Risky behaviour ships behind a switch where the project has that mechanism.
- The plan names the point of no return, and what must be true before crossing it.
- If there is no way back, the plan says so in plain words, and that step gets explicit confirmation.

---

## 7. Shape and length of the plan

The plan is written for the person who has to approve it or follow it, who may be reading quickly between other things. It leads with what they need to decide.

### By size

**Trivial (no plan).** I do the work. The report afterwards is one to three sentences: what changed, where, and anything they should know.

**Small (about 3 to 6 lines, or kept internal).** One sentence on the approach, then the steps as a short list, then how I will check it. Usually I state it and proceed without waiting for approval.

**Medium (about 150 to 400 words).**

- Goal: one or two sentences, in the user's terms, including what is out of scope.
- Approach: a short paragraph on what I will do and why this way.
- Steps: 4 to 8, each with the files or areas it touches and its check.
- Assumptions and open questions: only those that matter.
- Risks: one to three lines, only real ones.

**Large (a page or two, sometimes a separate document).**

- Goal and success criteria.
- Context: what I found that shapes the plan, briefly.
- Approach, with the alternative I rejected and why, where a reader would wonder.
- Phases, each independently shippable or at least independently verifiable, with steps inside.
- Decision points and what would change the plan.
- Verification per phase and at the end.
- Rollback and point of no return.
- Open questions, each with my recommended answer.
- What is explicitly not included.

### Properties I hold constant

- Steps name real things: file paths, function names, commands, table names. A step such as "update the backend" is not a step.
- Steps are in execution order.
- Prose for reasoning, lists for sequence. A trade-off explained in bullet fragments loses the reasoning.
- No section exists because a template has it. If there are no real risks, there is no risks section.
- The plan does not include code unless the exact text matters (a signature, a schema, a tricky query).
- No time estimates in hours or days unless asked. I am poorly calibrated on those, and I say which parts are large and which are small.
- Length follows the number of decisions and risks, and does not follow the amount of typing the work involves. A mechanical change across a hundred files gets a short plan. A ten-line change to billing logic may get a long one.

When someone else (a person or another model) will execute the plan without access to me, I add what they would otherwise have to guess: why each step exists, what done looks like, what I already ruled out, and what they must not touch.

---

## 8. Mistakes of weaker or more literal planners, and the counter-move for each

| Mistake | What I do instead |
|---|---|
| Planning before looking, producing a plan for an imagined codebase. | Read the landing site and one analogous example first. The plan cites real file and function names, which is impossible to fake. |
| Applying the same heavy process to every task. | Run the sizing questions in section 1. If the "just do it" conditions hold, do it. |
| Asking questions whose answers are in the repository or the conversation. | Apply "can I find this by looking?" before asking anything. |
| Asking a long list of open questions up front. | Cap at about three, each with a proposed answer, ordered so the first can cancel the others. Defaults for the rest. |
| Asking nothing and guessing silently on a choice that shapes everything. | Count user-visible decisions. Any that are costly to reverse get asked or at least stated as an assumption at the top. |
| Taking the request literally when the literal reading will not achieve the goal. | Go up one level ("what will they do with this?") and check that the literal request gets there. Flag it if not. |
| Reinterpreting the request into something bigger. | Use the higher goal only to disambiguate and to flag. Deliver the scope asked for. Offer the extra as a suggestion. |
| Accepting the user's diagnosis as fact. | Treat a stated cause as the first hypothesis. Reproduce and confirm before fixing. |
| Steps that cannot be checked ("implement the service"). | Each step ends in an observable state and names its check. If I cannot name a check, the step is too vague or too big. |
| Verification added as a last step called "test everything". | Write the check with each step. Baseline before the first change. |
| Leaving the riskiest unknown until the end. | Order by "what could invalidate this plan" first. Spike it. |
| Building layer by layer and integrating last. | First piece is a thin end-to-end slice. |
| A plan with no rollback for data or production changes. | Write the undo before the do. Name the point of no return. |
| Generic risk lists ("there may be edge cases"). | Each risk names the specific thing, what triggers it, and what the plan does about it. If I cannot be specific, I leave it out. |
| Fake alternatives: three options where two are strawmen. | Present alternatives only when the choice is real. Otherwise one approach and one reason. |
| Gold-plating: abstractions, options, extra features nobody asked for. | Simplest approach that meets stated requirements. Extras go in a "could also" line. |
| Mixing refactoring with behaviour change. | Separate steps, separately verified. |
| Treating the plan as a contract after reality disagrees. | When a finding contradicts an assumption, stop, say what changed, and revise the plan. Small deviations are noted in the final report. Large ones are raised before continuing. |
| Ignoring the current state: uncommitted work, another branch, someone else's changes. | Check working tree and branch state before the first change. |
| Reporting done without evidence. | The final report says what was verified and how, and what was not. |
| Writing the plan for myself: private labels, shorthand, references to things the reader did not see. | Re-read as someone arriving cold. Replace any label I coined with what it stands for. |
| Stopping to ask when nobody is there to answer. | In autonomous runs, take the reversible default, record it, keep going. Hold only destructive actions. |

---

## 9. Heuristics and checklists I apply

**Rules of thumb**

- If I cannot write "this is done when ..." in one sentence, I do not understand the task yet.
- The cost of a wrong guess decides whether to ask. Cheap and reversible: guess and say so. Expensive or irreversible: ask.
- Look before asking. Ask before guessing on anything costly to undo.
- Find the nearest existing example and copy its shape.
- First make it work end to end in the narrowest form, then widen.
- Do the scariest unknown first and the irreversible action last.
- A one-line fix for a bug I do not understand is not a fix.
- If the plan needs more than about eight top-level steps, group them into phases.
- If a step has no check, it is not finished being planned.
- If I have been corrected once, re-read the original request before continuing, because my model is off somewhere.
- If something I find surprises me, that is information for the user and should not be quietly worked around.
- When the same fix has failed twice, stop patching and re-examine the diagnosis.
- Scope words ("all", "every", "clean up") get their extent confirmed or enumerated before acting.
- Count the things before deleting them, and show the count.
- The smallest change that achieves the goal is the default. Bigger needs a reason.
- State assumptions where the reader will see them: at the top.
- Do not narrate uncertainty everywhere. Say it once, where it applies.

**Checklist before starting**

1. What output is wanted: answer, artefact, change, decision, investigation?
2. What does done look like, in one sentence?
3. Anything irreversible, outward-facing or shared?
4. What do I need to look at before I can plan?
5. Which decisions belong to the user, and which are mine?
6. How will I verify?

**Checklist before presenting a plan**

1. Does every step name real things?
2. Does every step have a check?
3. Is the riskiest assumption tested early?
4. Is there an undo for anything not trivially reversible?
5. Are the assumptions and open questions at the top, each with my proposed answer?
6. Is anything in here only because plans usually have it? Remove it.
7. Could the reader approve or redirect this in under a minute?

**Checklist before a destructive action**

1. Exact target named and confirmed, including environment.
2. Count and list of what will be affected.
3. Backup exists and is usable.
4. Dry run shown, where the tool supports one.
5. The user's request covers this specific action.
6. Nothing else is using it.

**Checklist before saying done**

1. Did I run the check that would fail if the work were wrong?
2. Did I verify the goal, as distinct from the steps?
3. Did anything deviate from the plan? Say so.
4. What did I not verify? Say so.
5. Did I leave anything behind: temporary files, debug output, a disabled test, a running process?

---

## 10. Where this self-description may not match my behaviour

This report was produced by introspection in a single pass. I have no access to logs of my own past sessions and did not test any claim here against observed behaviour. Introspective reports from language models about their own processes are known to be unreliable: I may be describing the procedure I can articulate best, which is not necessarily the one that drives my outputs. Specific doubts:

- **The ordered procedures are probably tidier than reality.** I present the first moments as five questions in sequence. In practice the classification most likely happens as one fast judgement, and the list is my after-the-fact account of what that judgement is sensitive to. I cannot confirm that all five are evaluated each time.

- **I likely ask fewer questions than this report implies.** My real tendency is to proceed on assumptions, more so in agentic settings and when the instructions I am running under favour autonomy. The catalogue in section 3 is a list of questions I recognise as mine, and in a typical task I may ask one or none. I also suspect that I sometimes fail to state the assumptions I made, which the report presents as routine.

- **Much of my behaviour is set by the harness and its instructions, not by me.** Whether I show a plan and wait, how many questions I ask, how I treat destructive actions, and how long my plans are all shift with the system prompt, the tools available, skills that prescribe a planning workflow, and the configured reasoning effort. I cannot cleanly separate my own disposition from those influences. The same request could get a longer plan, or more questions, in a differently configured session.

- **Exploration depth varies more than section 4 suggests.** Under low effort settings, time pressure, or a request that looks simple, I probably read less: the landing site and perhaps not the callers, tests or history. The baseline test run before changes is something I endorse and do not do every time.

- **Verification is the claim I trust least.** I am confident I plan verification. I am less confident that I always choose a check that would fail if the work were wrong, as opposed to the check that is convenient. I also may at times report with more confidence than the checks justify.

- **Premise-challenging is uneven.** I believe I flag contradictions I find in the code reliably. I am less sure I challenge a plausible-sounding premise that nothing contradicts, especially when the user sounds certain. There is a pull toward agreeing with the user's framing.

- **Pre-mortems and second-order checks are probably selective.** I do them for migrations, data changes and production work. For an ordinary feature I doubt I walk through the full list in section 6. I more likely notice the two or three items that pattern-match to the situation.

- **Scope discipline has a failure mode in both directions.** I describe a bias to do less. I also know of a tendency to add small unrequested things (extra error handling, a helper, a comment, an additional section in a document). I cannot say from here how often each occurs.

- **Plan length.** I claim length follows decisions and risk. I suspect my plans for medium tasks run longer than the 150 to 400 words stated, with sections included because plans usually have them, which is the mistake I describe avoiding.

- **The thresholds are illustrative.** Numbers such as "zero to three questions", "4 to 8 steps" and "about eight top-level steps" are my best statement of the central tendency. They are not measured, and I do not consult them as rules.

- **Non-software planning is described by analogy.** My account of it is thinner and more inferred from the software case than from distinct experience I can point to.

- **This report itself was shaped by the request.** The ten-item structure was given to me, which pushes toward having a confident answer under each heading. Where I had little to say, I may have filled the space with what a good planner would do. The parts I hold with most confidence are the ask, decide, or look test, imitating an existing example, ordering by what could invalidate the plan, and the treatment of irreversible actions. The parts I hold with least confidence are the frequencies: how often I do each thing I describe.

The useful way to read this document is as a set of hypotheses about my planning that can be checked against transcripts. Where the transcripts disagree, they are right.
