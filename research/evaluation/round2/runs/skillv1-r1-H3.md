The 35-minute test suite is not what stands between you and continuous deployment. Thirty-five minutes from merge to production is already far faster than a week, and the suite can be sped up alongside everything else. The hard part is the Thursday QA pass. Today it is the only check that a person looks at the product before customers do, so it has to be replaced, check by check, before it is removed. Close behind it are two habits that weekly releases let you skip: database migrations that old and new code can both run against, and a way to ship unfinished work without exposing it. I would move in steps (an automated, rollback-ready deploy first, then daily deploys, then deploy on every merge), each with a measurable condition for moving on and for stepping back.

If the main pain is that fixes wait up to a week, the first two phases alone (automated deploys of `main` on demand, any day) remove most of it at a fraction of the cost, and you can stop there. I plan the whole move as you asked below. Every phase leaves a working process, so stopping partway is safe.

I have not seen your repository, CI, AWS setup or QA checklist. The plan rests on the defaults below.

## Questions I would ask

1. **What is driving the change: fixes waiting a week, risk from large Friday batches, developer frustration, or something else?** Default: all three, roughly equally, so the full plan applies. If it is mainly fixes waiting, phases 1 and 2 are enough, and phase 5 becomes optional.
2. **What has Thursday QA actually caught over the last few months?** Default: mostly regressions in a handful of critical flows (sign-up, login, checkout or the core workflow) plus some visual issues. You can settle this without me: go through the bugs QA filed in the last quarter and tag each as "automatable", "needs a human eye" or "would have been caught in review". That list sizes phase 3.
3. **How do you deploy on AWS today, and can two versions of the app run at once during a deploy?** Default: containers or instances behind a load balancer, with a rolling deploy, so old and new code briefly serve traffic together. That is what makes the migration rules in phase 4 necessary. If deploys take the site down briefly instead, phase 1 also has to make them zero-downtime, and that becomes the largest phase.
4. **Does any audit or customer contract require sign-off on each production change (SOC 2, ISO 27001, a bank customer)?** Default: no formal requirement beyond code review. If yes, approval of the pull request plus the automated checks in the pipeline usually serves as the change record. Confirm that with your auditor before phase 5, not after.

Answer first: 2 and 3. Question 2 decides how much of the QA pass is automated work and how much becomes a different human step. Question 3 decides whether phase 1 is a few days of pipeline work or a deployment rebuild.

## Plan

### Phase 0: Measure the current process

Record, for the last few months of weekly releases: how often a release caused an incident or a hotfix (the change failure rate), how long a fix took from merge to production, how long recovery took, and the QA tagging from question 2. These are the baseline that every later go/no-go compares against. No target is set before this exists.

### Phase 1: Make a deploy automatic and reversible

- Build one artefact per commit on `main` (for example a container image tagged with the commit SHA) and promote that same artefact through staging to production. No rebuilds per environment.
- Deploy with one command or button, run by the pipeline, not from a laptop. Keep the last several artefacts so that rollback is "deploy the previous SHA".
- Health checks on the load balancer, error tracking tagged with the release SHA, and a deploy notification in the team channel naming the commits it contains. With continuous deployment, "which deploy broke it" becomes the first question, and the release tag answers it.
- Rehearse rollback in production during a quiet period. Measure how long it takes.
- Check: a deploy and a rollback each run end to end with no manual steps, and both durations are written down.

### Phase 2: Deploy on demand, alongside the weekly release

- Any engineer may deploy `main` on any working day, during staffed hours. The Friday release continues and still carries the QA-checked batch.
- Change working agreements: `main` is always deployable, branches are short-lived, and anything unfinished hides behind a feature flag. A flag library suits a Django app. `django-waffle` is the one I would reach for; check that it is still maintained and fits your Django version before adopting it.
- Check: two weeks of on-demand deploys with no deploy-caused incident that the weekly process would have prevented.

### Phase 3: Replace the Thursday QA pass, check by check (the bulk of the work)

- From the question 2 tagging, turn each "automatable" check into a test: unit or integration tests in the existing suite where possible, and a short end-to-end smoke suite (Playwright or similar) for the critical flows. The smoke suite runs against staging before every production deploy, and against production right after it.
- Move "needs a human eye" checks to the feature level. QA tests a feature in production behind its flag, before the flag is turned on for customers. The QA role shifts from checking a weekly batch to exploratory testing of each feature before release. That is a change to the QA job, so plan it with the QA staff, not around them.
- Speed up the suite in parallel. Run it across several CI workers (pytest-xdist, or splitting by test file across runners), reuse the test database between runs, use a fast password hasher in test settings, and profile the slowest tests. Set the target after profiling. The number that matters is merge-to-production time.
- Check: every item on the current QA checklist is marked "automated", "moved to flag-level testing" or "dropped, with a reason". The Thursday pass is removed only when the list is complete.

### Phase 4: Make every migration safe to run beside the previous version

With frequent deploys, the new schema always runs, at least briefly, with the old code. Rules:

- Expand, then contract: add the column or table, deploy code that writes both and reads the new one, backfill, and remove the old one in a later deploy. Never rename or drop in the same deploy as the code that stops using it.
- Migrations run as a separate pipeline step before the new code goes live. Large backfills run as background jobs, not inside a migration.
- Add a CI check that flags backward-incompatible migrations: column drops, renames, NOT NULL without a default. `django-migration-linter` does this as I remember it; check that it still exists and supports your Django version before relying on it.
- Check: the CI check runs on every pull request, and the team has done one expand-and-contract change end to end.

### Phase 5: Step up the cadence

Move in steps: daily deploys of `main`, then several a day, then automatic deploy of every merge that passes the pipeline.

- **Go/no-go before each step up (all must be true):**
  - The change failure rate over the last 20 deploys is no worse than the phase 0 weekly baseline.
  - Rollback has been used or rehearsed in the last month, and finished within the time measured in phase 1.
  - The production smoke suite has run after every deploy in the current step.
  - No open incident review action concerns the pipeline.
- **Abort rule inside each deploy:** if the post-deploy smoke suite fails, or the error rate tagged to the new release exceeds the previous release's rate over the first 15 minutes, the pipeline rolls back automatically and blocks further deploys until someone looks.
- **Step-back rule:** if the change failure rate over any rolling 20 deploys rises above the baseline, return to the previous cadence until the cause is fixed.
- Initially, deploy only during staffed hours, so someone is around to watch. Widen that once rollbacks have been routine for a while.

## What the weekly release gives you today, and what replaces it

| Free today | Replacement |
|---|---|
| A person checks the product before customers see it | Automated smoke tests before and after deploy, plus flag-level exploratory testing before release |
| A release day when everyone is watching | Release-tagged error tracking and automatic rollback; the deployer watches their own deploy |
| An obvious "last good version" (last Friday) | Every deploy is a rollback point; the previous artefacts are kept |
| Weekly release notes for support and customers | A weekly summary generated from merged pull requests and flags turned on |
| Schema changes made in one go, with old code gone | Expand-and-contract and the migration lint |
| Bugs traceable to "this week's release" | The release SHA on every error and log line |

The change will also hide some things. A bug introduced in one small deploy may surface only after five more have shipped. The release tag on errors and the deploy log in the team channel are what let you trace it back, so set both up in phase 1, not later.

## Found, not touched

- Who runs the pipeline work: with 14 engineers, I would name one or two owners for phases 1 and 4 rather than spreading it across the team. I have not estimated a duration, because that depends on question 3 and on who is assigned.
- On-call: deploying on weekdays during staffed hours does not require a new rota, but once deploys run around the clock it will. That decision belongs to phase 5.

## Need from you

- The QA checklist and the last quarter's QA-filed bugs (question 2).
- A description or read access for the CI configuration and the AWS deployment setup (question 3).
- Phase 0's numbers, or access to the incident and hotfix history so they can be computed.
