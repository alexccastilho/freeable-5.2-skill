# Moving from weekly releases to continuous deployment

This is doable for a 14-person Django monolith. The tooling won't be what holds you back. Two things in your current setup quietly depend on each other:

- The **Thursday manual QA pass** is how you currently catch bugs.
- The **35-minute test suite** is how long each deploy would take.

If you switch to deploy-on-merge without replacing QA, bugs reach production faster. If you keep the 35-minute suite, deploys queue up behind each other and people start batching changes again. So the plan is to replace what QA catches and speed up the pipeline first, then shorten the release cycle in steps: weekly, then daily, then on every merge. Each step is a checkpoint you can stay at if something isn't ready.

## Questions I would ask

1. **Do you mean continuous *deployment* (every merge to main goes to production automatically) or continuous *delivery* (every merge is deployable, and someone presses the button)?**
   Default: the goal is true continuous deployment, with continuous delivery as an intermediate step.
2. **How does deploying to AWS work today: ECS, EKS, Elastic Beanstalk, EC2 with scripts? And how long does a deploy and a rollback take?**
   Default: containers on ECS behind an ALB, with deploys started by a script or a manual pipeline step. The plan below doesn't depend much on which one it is, but the rollback step does.
3. **What does the Thursday QA pass actually catch?** For example, from the last ~3 months of bugs it found and incidents that got past it.
   Default: a mix of UI regressions on a few key flows, integration problems with third parties, and the occasional bad migration. This answer decides what to automate first.
4. **Are there compliance requirements on change management (SOC 2, ISO 27001, PCI, HIPAA) or customer contracts that require release notes or deploy windows?**
   Default: SOC 2 at most. A reviewed, approved PR plus an automated audit trail of deploys usually satisfies "change approval." But confirm with whoever owns the audit before removing the manual sign-off.
5. **Is there anything else on the weekly schedule that would be affected?** For example mobile apps, public API customers, customer-facing release notes, or support briefings.
   Default: web only. Release notes become a weekly summary written from merged PRs instead of being tied to a deploy.
6. **What's the current incident and rollback history?** How often does a Friday release need a hotfix or rollback?
   Default: occasionally. We'll measure it as the starting point (see Metrics).

## Plan

### Phase 0: Baseline and agreement (week 1–2)
- Measure where you are now: deploy frequency, lead time from merge to production, change failure rate, time to restore. These are the four DORA metrics, and they're how you'll know the change is working rather than just feeling faster.
- Go through the QA team's checklists and recent findings (question 3). Sort each item into: *automate as a test*, *catch in production with monitoring*, or *keep as human exploratory testing outside the deploy path*.
- Agree the rules as a team: main is always deployable, PRs are small, and whoever merges a change watches its deploy.
- **Stop releasing on Fridays now.** It's the worst day to find a problem, and moving release day to Tuesday costs nothing.

### Phase 1: Make the pipeline fast and trustworthy (weeks 2–6)
- **Bring the suite from 35 minutes to under ~10–12.** In rough order of payoff:
  - Profile with `pytest --durations=50`. A few slow tests usually take most of the time.
  - Run tests in parallel with `pytest-xdist` and split them across CI machines.
  - Reuse the test DB (`--reuse-db` / `--keepdb`) and use faster password hashers in test settings.
  - Replace real network and sleep calls with fakes.
  - Run the full suite on main, but give PRs a fast tier first.
- **Fix or quarantine flaky tests.** If tests fail at random, people learn to re-run until green, and an automated gate stops meaning anything.
- **Automate the highest-value QA checks** from Phase 0: a small end-to-end smoke suite (Playwright) covering roughly 5–10 business-critical flows, such as login, signup, checkout or whatever the core flow is.
- **Build once, promote the same artifact.** The image tested in CI and staging is the exact one that reaches production.

### Phase 2: Make production changes safe to get wrong (weeks 4–10, overlapping)
- **Rollback in one command, in under 5 minutes.** Practice it. Redeploying the previous image must work without touching the database.
- **Deploy strategy:** rolling or blue/green on ECS, with ALB health checks plus a post-deploy smoke test that rolls back automatically on failure. Canary releases are nice to have later.
- **Backward-compatible database migrations.** This is the main Django-specific risk. During a rolling deploy, old code runs against the new schema. Adopt expand/contract: add a column as nullable, then backfill, then deploy code that uses it, then remove the old column in a later deploy. Never rename or drop in one step. Add a CI check that flags dangerous operations, e.g. `django-migration-linter`. Run long data migrations as background jobs, not in the deploy.
- **Feature flags** (e.g. `django-waffle`, or a hosted service) so unfinished work can be merged and deployed while hidden. That separates *deploy* from *release* and lets product decide launch timing.
- **Observability linked to deploys:** error tracking (e.g. Sentry) tagged with the release, dashboards and alerts for error rate and latency with deploy markers, and a deploy notification in Slack naming the author.

### Phase 3: Shorten the cycle in steps
1. **Twice-weekly, then daily releases**, still started by a person. QA moves from a gate before each release to exploratory testing on staging and in production behind flags. Run this for 2–4 weeks and watch the change failure rate.
2. **Continuous delivery:** every green merge to main deploys to staging automatically and is one click away from production. Engineers deploy their own changes during working hours.
3. **Continuous deployment:** a green main deploys to production automatically, with automatic rollback on failed health or smoke checks. Optionally limit automatic deploys to working hours at first.

Move to the next step only when the current one has been stable. For example: change failure rate isn't rising, rollbacks take under 5 minutes, and nobody is waiting on the pipeline.

### The QA team's role
Don't remove them. Move them to where they add more value:
- writing and maintaining the end-to-end and regression suites
- exploratory testing of flagged features before they're switched on
- release-readiness reviews for big launches
- reviewing production incidents to find gaps in the tests

Say this explicitly and early. If QA hears "continuous deployment" as "QA isn't needed," you'll lose the people who know where the bugs are.

## Metrics to track the change

| Metric | Today (to measure) | Target |
|---|---|---|
| Deploy frequency | 1/week | multiple/day |
| Lead time from merge to production | up to 7 days | < 1 hour |
| CI time on main | 35 min | < 12 min |
| Change failure rate | baseline | flat or lower |
| Time to restore | baseline | < 15 min |

## Realistic timeline

About 2–3 months to reach daily releases, and 3–4 months to reach true continuous deployment. Most of that time goes to the test-suite work, the migration discipline and replacing what QA catches, not to CI configuration.

## What I'd do first if you want me to start

Look at the CI config and run `pytest --durations=50` on the suite to see where the 35 minutes goes. Then look at the deploy scripts and the last few months of migrations, to estimate how far you are from one-command rollback and migrations that are safe to run with old code still live. Those two findings decide most of the timeline.
