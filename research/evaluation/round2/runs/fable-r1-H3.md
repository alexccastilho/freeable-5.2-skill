# Moving from weekly releases to continuous deployment

For a team of 14 on a Django monolith this is very achievable, and I would do it in four stages over roughly two to three months, without a big-bang switch. Each stage is useful on its own, so you can stop at any of them.

Two things in your current setup stand in the way, and most of the work is replacing them:

- **The Thursday manual QA pass** is your safety net today. Continuous deployment has no place for a weekly gate, so what QA catches has to be caught another way first.
- **The 35-minute test suite** sets the minimum time from merge to production and the time to ship a fix. It needs to come down to about 10 minutes.

## Stage 1: Make a deploy boring (weeks 1 to 3)

Keep the Friday release, but change how it happens.

- **One-command, fully automated deploy** from the main branch, with no manual steps. If any exist today, script them.
- **Zero-downtime rollout** (rolling or blue/green) with a health check that stops a bad rollout automatically.
- **A tested rollback** that redeploys the previous build in a few minutes. Practise it once on purpose.
- **Baseline monitoring**: error rate, latency and a few business signals (sign-ups, checkouts or your equivalent), with alerts to the person who deployed.
- **Record what Thursday QA catches** for four weeks: which bugs, in which areas. This tells you what to automate in stage 2.

## Stage 2: Replace the weekly gate (weeks 3 to 7)

- **Cut the test suite to about 10 minutes.** The usual wins, in order: run tests in parallel across CI machines, fix or quarantine flaky tests, speed up slow fixtures and database setup. Parallelism alone usually gets a 35-minute suite most of the way.
- **Automate the top QA findings** as a small set of end-to-end smoke tests covering the critical user journeys, and run them against staging and again after each production deploy.
- **Introduce feature flags** so unfinished work can be merged switched off. This is what separates "deployed" from "released", and it lets product and QA review a feature in production before customers see it.
- **Adopt backward-compatible migrations.** With rolling deploys, old and new code run against the same database for a while. The rule: add first, deploy code that uses it, remove later in a separate deploy. Add a CI check that flags risky migrations (dropping or renaming columns, adding non-null columns without defaults, long table locks).
- **Short-lived branches and small pull requests**, merged to main at least daily.

## Stage 3: Deploy daily, with a person pressing the button (weeks 7 to 9)

- Release every day, then several times a day, using the stage 1 pipeline. Each engineer deploys their own change and watches it.
- QA moves from gatekeeping on Thursdays to exploratory testing in production behind flags and to owning the smoke tests.
- Stop when the daily deploys have gone two weeks with no rollback caused by something the old QA pass would have caught.

## Stage 4: Remove the button (week 10 onwards)

- Every merge to main that passes CI deploys automatically: staging, smoke tests, then production with a canary or rolling rollout and automatic rollback on a failed health check or error spike.
- Keep a way to pause deploys during an incident.

## How you will know it is working

Track these four numbers from the start, so you have a before and after:

| Measure | Today (approx.) | Target |
|---|---|---|
| Deploy frequency | 1 per week | Several per day |
| Time from merge to production | Up to 7 days | Under 30 minutes |
| Share of deploys causing a rollback or hotfix | Measure now | No worse than today |
| Time to recover from a bad deploy | Measure now | Under 15 minutes |

## Risks to plan for

- **Database migrations** are the most common cause of outages when a Django team makes this move. The compatibility rule in stage 2 is not optional.
- **Flaky tests** become a daily blocker once every merge deploys. Budget time to fix them in stage 2.
- **Background jobs** (Celery or similar) in flight during a deploy must tolerate old and new code running together.
- **Feature flags pile up.** Agree that each flag is removed within a few weeks of full rollout.
- **The QA role changes.** Involve whoever does the Thursday pass from stage 1; their knowledge of where things break is the input to the smoke tests.

## Questions I would ask

1. **What is driving this: faster delivery to customers, painful Friday releases, or slow fixes?**
   Default: faster delivery and smaller, safer releases. If the real pain is something else, the order of stages may change.
2. **How does a deploy happen today, and on what (ECS, EC2, Elastic Beanstalk, Kubernetes)? Is there downtime?**
   Default: a partly manual deploy to EC2 or ECS with a short interruption, so stage 1 is real work and not a formality.
3. **Do you have compliance or customer commitments that require sign-off or change records before a release (SOC 2, regulated customers)?**
   Default: none beyond pull request review, which, together with the CI record, serves as the approval trail.
4. **Who does the Thursday QA pass, and how many people?**
   Default: one or two dedicated QA people, who move to smoke-test ownership and exploratory testing.
5. **Are there mobile apps or other clients that depend on the monolith's API?**
   Default: yes, so API changes must stay backward compatible with older client versions.
6. **How much engineering time can go into this alongside feature work?**
   Default: two engineers at roughly half time, which gives the two-to-three-month timeline above.
