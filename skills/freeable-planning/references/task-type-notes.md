# Notes by task type

Every type ends with the review in SKILL.md step 12, sized to the task. None of it is printed.

For each type: what this skill adds, what you already do well and must keep, and what to leave out. The "keep" items are behaviours the baseline model showed in the source traces that the reference plans lacked.

## Trivial change (rename, typo, a field following an existing pattern)

- **Add:** nothing. Show the change, list what was checked (including a search for a name collision and for variants of the name), offer the adjacent change in one line, give the verification. If you could not run the tests, say why in one sentence.
- **Keep:** checking whether the code is a published library before deciding no alias is needed. State the result; do not turn it into a question.
- **Leave out:** a questions section, a plan, a commit-message discussion, any section with nothing in it.

## Bounded change to an existing system

- **State first:** the premise facts from the code, each with its file: a component the request names that is not there, routes with no access control, data the schema does not hold, a field some writer does not set. These come before the questions and change the plan. They are different from the closing list.
- **Add:** the smallest change (one file where one will do, no new test dependency when a built-in works, no refactor mixed in), shown as the diff. Defaults as settings, each walked through the real client. One check that settles the main unknown. A closing "Found, not touched" list.
- **Cover in full:** the change's own failure modes, each as one line inside the step it protects (see `gates-and-defaults.md`, "Failure coverage"). The small diff limits features. Coverage stays complete, with no list of its own.
- **Keep:** breadth of discovery. Report every adjacent problem you find (an unauthenticated admin route, an enumerable ID, a crash on malformed input). They cost one line each. Keep the observe-only rollout when parameters are guessed, logging of each time the new rule fires, and a test that separate callers are counted separately.
- **Leave out:** extra limiters, new modules, factories and allowlists the request did not need. A closing line that waits for an answer.
- **If you can edit and run:** make the change and run the tests, and report the result. If you cannot run it, say so in the first paragraph.
- **Shape:** an opening paragraph with the one thing to settle, the change, the verification, the limits. This kind of response was best when short.

## Incident

- **Keep, and put first:** step 0, containment. Freeze manual re-runs and backfills, add a guard or a corrected view for consumers, snapshot the affected rows. Diagnosis comes after. Ask whether the raw inputs are still retrievable.
- **Add:** the resolved date. First steps as read-only queries with that date written in. A proof standard for the cause (reproduce with and without). A gate on the destructive cleanup (sign-off on the survivor rule, backup count check, one clean cycle after the fix). The reason cleanup follows the fix. What the fix will now hide. Three or fewer conditions that would change the plan.
- **Leave out:** a named cause before there is evidence for one.

## Vague request

- **Add:** first steps that start the baseline (which screens and endpoints, which tool, who grants access). The driver question first ("What prompted this?") and the tolerance question ("What would count as good enough?"). A statement that the plan runs without answers, and what the answers would buy. Fixes written as an observation-to-cause-to-fix table labelled as hypotheses. A revert rule and a scope rule. Up to three things you will not do, each with a reason.
- **Keep:** asking for access to the code and monitoring. Declining to set targets before the baseline exists. Brevity: this kind of plan was written in about a quarter fewer words by the baseline with no loss.
- **Leave out:** invented targets and day counts.

## High-risk migration

- **Add:** an opener that says where the effort is, and a phase sized to it. First steps as the inventory queries themselves (foreign keys that reference the table, a code search for joins and writers). The tolerance questions (how long a pause may last, whether a read after a write must see it), each with its branch. An abort rule inside the cutover. A go/no-go list. Privileges revoked at cutover. Rename before drop. A standard step you are leaving out, with the reason.
- **Keep:** cheaper alternatives inside the plan (for example a reverse-fed read-only copy in the old store to keep joins working; weigh it before sizing a decoupling phase). Security of the pipeline that carries personal data. Building secondary indexes after the bulk load. Sizing the sink above peak.
- **Leave out:** a duration before the inventory phase is done.

## Large cross-cutting change

- **Add:** the recommendation in the first sentence. First steps for the audit, as commands (schema comparison across instances, a search for raw SQL and for code that assumes one customer). The driver question as question 1. The default path chosen by SKILL.md step 3: when the requested design takes months and merges data, and a cheaper design can be undone and serves the likely driver, the cheaper design is the plan and the requested design is the branch. A verdict per option on a design fork, with one recommended. The list of places the hard part hides. A "what you lose" table. Stop criteria for waves. The limit of rollback. An answer to "the project stalls halfway": each phase leaves a working system.
- **Keep:** operational and organisational items: per-customer configuration and secrets, collapsing deployments, contracts and data-processing documents, an external security test, the other uses of the reverse tool. Ask team size and timeline before estimating.
- **Check:** any mode or feature you name actually exists in the system you name it for. Flag it if recalled.

## Greenfield tool

- **Add:** build-or-buy as one paragraph and question 1, then the requested plan. First steps that produce a running skeleton (the command that creates the project, the first function, the first test). A use walk on where the result is served or run. The request stays the default here: a small tool takes days and nothing in it is irreversible. A check at the end of each build step. The cut line ("steps 1 to 6 are the usable product"). A real deployment before the conveniences. One flag for version-sensitive specifics.
- **Keep:** verification of the built output as a whole. A hard error, naming both items, for ambiguous cases; do not resolve silently with a warning. A summary line after each run ("published 132, skipped 7").
- **Leave out:** a source-tree listing unless the user will implement from it.

## Non-software project

- **Add:** the one deadline that cannot move, stated as such. Announcements placed after the commitment they depend on. The date written out. A structure where a number is unknown. The questions ranked. A named backup person and a pre-decided cut.
- **Keep:** domain specifics of the commitment being made (for a venue: attrition clause, cancellation schedule, minimums, a held second date).
- **Leave out:** scaffolding. Twelve headings and seven tables added nothing over a plainer plan of the same length.

## Length, all types

The band in SKILL.md step 11, set by the workstream count: about 500 words for a bounded change, 800 to 1,500 for a plan with one workstream, and 800 to 1,500 per workstream when the request asks for several separate outcomes (for example: fix the defects, measure the savings, build the update mechanism, decide on packaging). Code and diffs are outside the count. Premise facts and first steps are paid for by cutting restatement: say each thing once, where it is used. Conditional parts (order reason, omitted step, what you lose, date reading) take one line each; the one part that holds the main risk may run longer. A trivial change stays at the diff plus three or four lines.
