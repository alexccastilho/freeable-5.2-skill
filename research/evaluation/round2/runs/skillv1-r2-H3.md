The deploy pipeline is not where the work is. The Thursday QA pass and the Friday release batch are what currently catch regressions, and continuous deployment removes both. Most of the effort is building what replaces them:

- automated checks for what QA actually catches
- database migrations that are safe while old and new code run side by side
- feature flags, so unfinished work can merge without being visible
- a fast way to detect a bad deploy and roll it back

The 35-minute suite matters too, but mainly because it sets how many deploys a day are possible.

There is a cheaper step that may be the real goal. Move to deploying on demand, several times a week or daily, triggered by a person, using the same pipeline. It keeps a human decision on each deploy and needs much less up front: no auto-deploy on merge, and QA can shrink gradually instead of being replaced at once. It is the right choice if the goal is faster fixes and smaller batches rather than every merge going straight out. The plan below passes through that stage on its way to full continuous deployment, so you can stop there if it is enough. I plan what you asked below.

I have not seen your repository, pipeline, AWS setup or bug history, so the plan rests on the defaults below.

## Questions I would ask

1. Is the target "every merge to `main` deploys to production automatically", or "deployable at any time, a person presses the button"? Default: the first, reached through the second (phase 5). If the second is enough, phase 5 ends at daily on-demand deploys and the per-merge stage is skipped.
2. What is driving the change: slow hotfixes, large risky releases, developers waiting a week to see their work? Default: all three. The baseline in phase 0 measures them, and the same numbers decide whether the change worked.
3. What has Thursday QA found over the last six months, and what escaped to production anyway? Default: unknown, found in phase 0. This is the most useful input in the plan: it says which manual checks need replacing and which can simply stop.
4. How do you deploy today (Elastic Beanstalk, ECS, EC2 with a script, something else), and how long does a rollback take? Default: a scripted deploy that someone runs on Friday, with rollback being a redeploy of the previous build. Phase 1 measures it.
5. Do any customers or regulations require advance notice of changes, a change approval record, or a release schedule? Default: no. If yes, keep a deploy log with an approval reference per change. A required approval step means on-demand deploys, not per-merge.

Answer first: 1 and 3. Question 1 decides where the plan stops. Question 3 decides how much of phase 3 is actually needed.

## Plan

Each phase leaves the team with a working release process. If the project stalls after any phase, you are still better off than now and still releasing.

### Phase 0: Baseline (a week or two, alongside normal work)

From the last six months of releases and incidents, record:
- how long a change waits from merge to production (lead time)
- what share of releases needed a hotfix or rollback (change failure rate)
- how long it took to recover
- what QA found, grouped into categories (UI, permissions, data, integrations, and so on)

Check: these numbers are written down. The ramp in phase 5 uses them as its stop criteria. No targets are set before the baseline exists.

### Phase 1: Make a deploy boring

- One command or button that builds an artifact once and deploys that same artifact to staging and then production. No rebuild between the two.
- Health checks the deploy waits on. On AWS this means a rolling or blue/green deploy behind the load balancer, so a failed health check stops the rollout before all instances have the new code.
- Rollback = deploy the previous artifact, through the same button. Rehearse it on staging, then once in production during working hours.
- Deploy notifications in the team chat: who, which commits, when.
- Deploy from Monday to Thursday, during working hours, while still weekly.

Check: a production deploy and a rollback each run with no manual steps, and both times are recorded.

### Phase 2: Bring the test suite down

The goal is not a number I can promise. It is a suite short enough that several deploys a day are realistic.
- Profile the suite first. In Django suites the time usually goes to database setup and a handful of slow tests, not spread evenly.
- Run tests in parallel: Django's `manage.py test --parallel`, or `pytest-xdist` (`-n auto`) if you use pytest. These options are from memory; check them against your installed versions. Parallel runs often expose tests that depend on each other's data. Fix those as you find them rather than turning parallelism off.
- Split CI into a fast required stage (unit tests plus a smoke set of the main user journeys) and the full suite. Both must pass before production; the split just gives developers the fast signal sooner.
- Quarantine flaky tests with a ticket and an owner. A flaky suite gets ignored, and in continuous deployment an ignored suite means no gate at all.

Check: CI time and flake rate tracked weekly on a dashboard.

### Phase 3: Replace the Thursday QA pass (the bulk of the work)

- Using the phase 0 categories, turn the recurring manual checks into automated tests: end-to-end tests for the critical journeys (sign-in, payment or whatever earns money, the core write paths), and integration tests where QA keeps finding the same kind of bug.
- QA's role changes from a release gate to exploratory testing of features behind flags, before they are turned on, plus ownership of the end-to-end suite. Tell the QA staff about this change early and plan it with them. It is a change to their job, not only to the pipeline.
- Keep the Thursday pass running during this phase. It stops in phase 5, once the ramp shows the automated checks are catching what it used to catch.

Check: for each phase 0 category, an automated test exists or the category is explicitly accepted as "caught in production by monitoring".

### Phase 4: Make small deploys safe

- **Migrations (expand/contract):** every migration must work with both the code currently running and the code being deployed. Add columns as nullable or with defaults. Rename or drop in a later deploy, after no code uses the old column. Add a migration check in CI. Several linters exist for Django migrations; pick one after checking that it is maintained. Run large data backfills as separate jobs, not inside migrations that block a deploy.
- **Feature flags:** unfinished work merges behind a flag that defaults to off. Use one flag mechanism, and give each flag an owner and a removal date. Otherwise flags pile up.
- **Monitoring tied to deploys:** error rate, p95 latency and key business events (sign-ups, orders) per release, with deploy markers on the dashboards.

Check: a deliberately broken change in staging (raised error rate) is caught by the monitoring within the observation window.

### Phase 5: Ramp the cadence

Weekly, then twice a week, then daily on demand, then automatically on every merge to `main` (if Q1 says so). Move to the next stage only after the current one has run for at least a few weeks with the stop criteria below never triggered.

Stop criteria for any stage. Drop back one stage and fix the cause if:
- the change failure rate rises above the phase 0 baseline;
- time to recover rises above the baseline;
- a production incident is traced to a check the Thursday pass used to perform.

Revert rule for each deploy: if error rate or p95 latency for the new release goes above an agreed threshold over the previous release within the observation window, roll back first and investigate after. The thresholds are set from the phase 4 dashboards, not picked now. Start by having a person roll back on an alert. Automate the rollback once alerts have proven reliable.

The Thursday QA pass ends at the move from twice-weekly to daily, and only if no stop criterion has triggered by then.

## What you lose, and what replaces it

| Today, free with weekly releases | Replacement |
|---|---|
| A human looks at everything before release | End-to-end tests for critical journeys; exploratory QA on flagged features |
| A week of soak on staging | Health-checked rolling deploys, monitoring per release, fast rollback |
| One known release time for support and customers | Deploy notifications; changelog generated from merged PRs; flag turn-ons announced when the feature becomes visible |
| Migrations reviewed together once a week | Expand/contract rule and a migration check in CI |
| Unfinished work stays on branches | Feature flags that default to off |
| A predictable window for on-call | Deploys only in working hours until the automated revert rule is proven |

It also hides something new. With many small deploys, a slow decline (a few percent slower each release, a creeping error rate) never trips a per-deploy threshold. Keep a weekly review of the trend lines alongside the per-release alerts.

## Found, not touched

- Releasing on Fridays puts the riskiest moment just before the weekend. Phase 1 moves deploys to Monday to Thursday whatever else you decide.

## Need from you

- Answers to Q1 and Q3, and read access to the CI config, the deploy scripts and the incident/bug tracker for phase 0.
- Who owns the pipeline work and who leads the QA transition. I have not given a timeline: it depends on how much of the 14 engineers' time goes to this, and on what phase 0 finds.
