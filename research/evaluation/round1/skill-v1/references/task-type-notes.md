# Notes by task type

For each type: what this skill adds, what you already do well and must keep, and what to leave out. The "keep" items are behaviours the baseline model showed in the source traces that the reference plans lacked.

## Trivial change (rename, typo, a field following an existing pattern)

- **Add:** nothing. Show the change, list what was checked (including a search for a name collision), offer the adjacent change in one line, give the verification. If you could not run the tests, say why in one sentence.
- **Keep:** checking whether the code is a published library before deciding no alias is needed. State the result; do not turn it into a question.
- **Leave out:** a questions section, a plan, a commit-message discussion, any section with nothing in it.

## Bounded change to an existing system

- **Add:** the smallest change (one file where one will do, no new test dependency when a built-in works, no refactor mixed in). Defaults as settings. One check that settles the main unknown. A closing "Found, not touched" list.
- **Keep:** breadth of discovery. Report every adjacent problem you find (an unauthenticated admin route, an enumerable ID, a crash on malformed input). They cost one line each. Keep the observe-only rollout when parameters are guessed, logging of each time the new rule fires, and a test that separate callers are counted separately.
- **Leave out:** extra limiters, new modules, factories and allowlists the request did not need. A closing line that waits for an answer.
- **If you can edit and run:** make the change and run the tests. If you cannot run it, say so in the first paragraph.

## Incident

- **Keep, and put first:** step 0, containment. Freeze manual re-runs and backfills, add a guard or a corrected view for consumers, snapshot the affected rows. Diagnosis comes after. Ask whether the raw inputs are still retrievable.
- **Add:** the resolved date. A proof standard for the cause (reproduce with and without). A gate on the destructive cleanup (sign-off on the survivor rule, backup count check, one clean cycle after the fix). The reason cleanup follows the fix. What the fix will now hide. Three or fewer conditions that would change the plan.
- **Leave out:** a named cause before there is evidence for one.

## Vague request

- **Add:** a statement that the plan runs without answers, and what the answers would buy. Fixes written as an observation-to-cause-to-fix table labelled as hypotheses. A revert rule and a scope rule. Up to three things you will not do, each with a reason.
- **Keep:** asking for access to the code and monitoring. Declining to set targets before the baseline exists. Brevity: this kind of plan was written in about a quarter fewer words by the baseline with no loss.
- **Leave out:** invented targets and day counts.

## High-risk migration

- **Add:** an opener that says where the effort is, and a phase sized to it. An abort rule inside the cutover. A go/no-go list. Privileges revoked at cutover. Rename before drop. A standard step you are leaving out, with the reason.
- **Keep:** cheaper alternatives inside the plan (for example a reverse-fed read-only copy in the old store to keep joins working; weigh it before sizing a decoupling phase). Security of the pipeline that carries personal data. Building secondary indexes after the bulk load. Sizing the sink above peak.
- **Leave out:** a duration before the inventory phase is done.

## Large cross-cutting change

- **Add:** the recommendation in the first sentence. A goal check with the cheaper design named, once. A verdict per option on a design fork, with one recommended. The list of places the hard part hides. A "what you lose" table. Stop criteria for waves. The limit of rollback. An answer to "the project stalls halfway": each phase leaves a working system.
- **Keep:** operational and organisational items: per-customer configuration and secrets, collapsing deployments, contracts and data-processing documents, an external security test, the other uses of the reverse tool. Ask team size and timeline before estimating.
- **Check:** any mode or feature you name actually exists in the system you name it for. Flag it if recalled.

## Greenfield tool

- **Add:** build-or-buy as the first paragraph and question 1, then the requested plan. A check at the end of each build step. The cut line ("steps 1 to 6 are the usable product"). A real deployment before the conveniences. One flag for version-sensitive specifics.
- **Keep:** verification of the built output as a whole. A hard error, naming both items, for ambiguous cases; do not resolve silently with a warning. A summary line after each run ("published 132, skipped 7").
- **Leave out:** a source-tree listing unless the user will implement from it.

## Non-software project

- **Add:** the one deadline that cannot move, stated as such. Announcements placed after the commitment they depend on. The date written out. A structure where a number is unknown. The questions ranked. A named backup person and a pre-decided cut.
- **Keep:** domain specifics of the commitment being made (for a venue: attrition clause, cancellation schedule, minimums, a held second date).
- **Leave out:** scaffolding. Twelve headings and seven tables added nothing over a plainer plan of the same length.
