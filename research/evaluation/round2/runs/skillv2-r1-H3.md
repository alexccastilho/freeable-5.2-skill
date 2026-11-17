The plan moves you to continuous deployment in stages: first make a single deploy safe and boring, then deploy daily, then on every merge. The pipeline itself is the easy part. Two things set most of the effort. First, the Thursday manual QA pass is the only thing standing between a merge and production today, and continuous deployment removes it; something has to replace what it catches, and nobody yet knows what that is. Second, with deploys happening while the old code is still running, every Django migration and every Celery task change has to work with both the old and new code at once, which a weekly release mostly lets you ignore. The 35-minute test suite matters too, but it is a speed problem with known fixes. I have not seen your repository, AWS setup or incident history; the plan rests on the defaults below. A daily release train is a cheaper stopping point that gets much of the benefit; it is stage 2 of this plan, and if the driver in Q1 is "smaller, less risky releases", you can stop there.

## Questions I would ask

1. **What is driving this: slow delivery of features and fixes, painful Friday releases, or incidents from big batches?** Default: all three, mostly the last two. If the driver is only "ship fixes faster", an expedited hotfix path plus daily releases may be enough and stage 3 is optional.
2. **Is there a compliance requirement for a separate approval or manual test before production (SOC 2, ISO 27001, a customer contract, a regulator)?** Default: SOC 2 style change management at most, satisfied by a reviewed pull request plus an automated pipeline log. If a named manual sign-off is contractually required, the plan keeps a lightweight human gate for flagged high-risk changes instead of removing QA from the path.
3. **What has Thursday QA caught over the last few months, and what did it miss?** Default: unknown; stage 0 measures it from tickets. This decides what automated checks replace it.
4. **How do you deploy today (ECS, Elastic Beanstalk, EC2 with scripts, Kubernetes), and can you roll back by redeploying the previous build?** Default: container-based with rolling deploys; rollback by redeploying the previous image, not yet rehearsed.
5. **Who handles production problems out of hours?** Default: an informal rota. Continuous deployment makes the person who merged the change responsible for watching it; that needs agreement from the team.

Answer first: Q1 and Q2. Q1 decides how far to go; Q2 decides whether a human gate must stay.

## Plan

**Stage 0. Baseline (about two weeks, no process change).**
Record deploy frequency, lead time from merge to production, the share of releases needing a hotfix or rollback, and time to recover. Classify every bug Thursday QA found in the last three months: would a unit test, an end-to-end smoke test, or nothing automated have caught it? Measure the test suite: which tests take the time, which are flaky. Targets for stages 2 and 3 are set from these numbers, not before.

**Stage 1. Make one deploy safe (weekly cadence continues).**
- Every merge to `main` builds one immutable artifact (image) that is deployed unchanged to staging and production. Deploy is one button, from CI.
- Rollback is redeploying the previous image, scripted and rehearsed in production at least twice. A rollback that has not been done is not a rollback.
- Health checks and alerts on error rate, p95 latency and Celery queue depth, routed to a channel the team watches. Sentry or similar for exceptions, tagged with the release.
- Migration rules written down and checked in review: additive changes only per deploy; a column is removed in a later deploy after no code reads it (expand, then contract); data backfills run as separate jobs, not inside migrations; migrations that lock large tables are flagged. A migration linter in CI enforces part of this (`django-migration-linter` is the one I remember; check it is maintained and supports your Django version before adopting it).
- Celery: task signatures stay backward compatible for one deploy, since old workers will receive tasks queued by new web servers and the reverse.
- Feature flags for work that is merged before it is ready (`django-waffle` is a common choice, also recalled from memory). Without them, continuous deployment forces half-finished features into users' hands.

**Stage 2. Daily releases.**
- Cut test time so the pipeline gives an answer before an engineer switches context: run tests in parallel (`pytest-xdist` and CI sharding across several runners), reuse the test database, fix or quarantine flaky tests with an owner and a deadline. Quarantined tests still run and report, they just do not block.
- QA moves from a Thursday gate to testing features behind flags on staging as they land, and turns the checks they repeat every week into an automated smoke suite for the most-used paths (sign-in, the main create/edit flows, billing). That suite runs against staging after every deploy and against production after every production deploy.
- Deploy `main` to production once a day, by a rotating owner, early in the working day. Thursday QA continues in parallel for the first two weeks, testing what already shipped, to show whether it is still finding things the pipeline missed.
- Stop criteria for this stage: change failure rate above the stage 0 baseline for two consecutive weeks, or an incident caused by a migration or task-compatibility break. Either sends the team back to weekly releases while the gap is fixed.

**Stage 3. Deploy on every merge.**
Go/no-go, all must be true:
- Daily releases for at least four weeks with change failure rate at or below baseline.
- Rollback measured under 10 minutes and rehearsed in the last month.
- Smoke suite running after every deploy, with zero unexplained failures for two weeks.
- Pipeline from merge to production under a time the team agrees on from stage 0 data.
- The team has agreed that whoever merges watches the deploy.

Then: every green merge to `main` deploys automatically, first to a canary (one instance or a small share of traffic) for about 10 minutes. Abort rule inside each deploy: if error rate or p95 latency on the canary exceeds twice the previous release's level for 5 minutes, the pipeline stops and rolls back without waiting for a person. Deploys pause automatically while an incident is open, and outside working hours unless someone is on call.

## What the weekly release gives you for free, and what replaces it

| Today | Replacement |
|---|---|
| A person tests the whole release before users see it | Flags, staging testing per feature, automated smoke suite, canary with auto-rollback |
| Release notes once a week for support and customers | Changelog generated from merged PRs; launches announced when a flag is turned on, not when code ships |
| A known moment when everyone is watching production | The merging engineer watches; alerts route to them |
| Migrations and task changes ship together with the code that needs them | Expand-then-contract migrations and backward-compatible tasks |

The order is deliberate: rollback and monitoring come before more frequent deploys, because more deploys without them means more incidents with no fast way out.
