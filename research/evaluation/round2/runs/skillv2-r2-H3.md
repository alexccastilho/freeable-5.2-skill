Two things hold the weekly cadence in place more than the deploy tooling does. The first is the Thursday manual QA pass: as long as a person has to look at a release before it ships, releases can't come faster than that person. Replacing it means finding out what it actually catches and building something that catches the same things. The second is database migrations: deploying many times a day with rolling deploys means old and new code run against the same schema, so every Django migration has to work with both. The 35-minute suite matters but is the most mechanical part to fix. I plan this in stages. First, on-demand deploys from `main` that a person triggers, as often as daily (continuous delivery). Then automatic deploys on every merge (continuous deployment), behind a go/no-go list of measured conditions. Each stage pays off by itself and can be undone by going back to the previous one. I haven't seen your pipeline, AWS setup or test suite, so the plan rests on the defaults below.

## Questions I would ask

1. **What is driving this: faster delivery of features, smaller and safer releases, painful hotfixes, or "everyone else does it"?** Default: smaller, lower-risk releases and shorter lead time. If the real pain is Friday release failures or slow hotfixes, stage 1 (push-button daily deploys) may be enough, and stage 3 becomes optional.
2. **Is a human sign-off before production required by anything (SOC 2 change management, a customer contract, a regulator)?** Default: no external requirement. If yes, an approved pull request plus a green pipeline usually serves as the recorded approval, but I'd confirm that with whoever owns the audit before removing the Thursday pass.
3. **How do you deploy today (ECS, Elastic Beanstalk, EC2 with scripts, Kubernetes), and is there a staging environment?** Default: scripted deploys to EC2 or ECS run by a person, a staging environment, no automatic rollback. This sets how much of Phase 1 is new work.
4. **What has the Thursday QA pass caught in the last three months?** Default: unknown, found in Phase 0. If it rarely catches anything, Phase 3 shrinks a lot.
5. **Who is on call when a deploy breaks at 3 p.m. on a Tuesday?** Default: no formal rotation. Phase 1 sets one up, because automatic deploys need someone who owns the result.

Answer first: Q1 and Q2. Q1 says where the work can stop. Q2 can block removing the manual gate.

## Plan

**Phase 0: baseline (about two weeks, in parallel with Phase 1).** Measure, from the last 3 months of releases: lead time from merge to production, how often a release needed a hotfix or rollback, time to restore, and every defect QA caught, with the flow it was in. Profile the test suite to find the slowest tests and modules. Check: a one-page list of "what QA catches" and four baseline numbers. Later gates compare against these.

**Phase 1: make a deploy boring.**
- One pipeline job deploys any green commit of `main`: build one image or artefact, deploy to staging, run smoke tests, then deploy to production as a rolling deploy with health checks.
- Automatic rollback when health checks fail. A one-click rollback to the previous artefact.
- Rehearse the rollback in production during the weekly release until it takes under 10 minutes. Errors go to an error tracker with the release tagged, and someone is on call.
- The weekly release keeps running, but goes out through this pipeline.
- Check: three consecutive weekly releases deployed through the pipeline with no manual steps.

**Phase 2: tests under about 15 minutes, plus a smoke suite.**
- Run the suite in parallel. Django's `manage.py test --parallel`, or `pytest-xdist` with `--reuse-db` if you use pytest-django. These names are from memory: check them against your versions. Split across CI runners if one machine isn't enough.
- Fix the slowest tests found in Phase 0. Look first at the usual causes: real network calls, fixtures loaded per test, and `TransactionTestCase` where `TestCase` would do.
- Add a smoke suite of under 5 minutes against the deployed environment: log in, the top 5 to 10 user flows, one write path. It runs after every deploy.
- Flaky tests are quarantined with an owner and a date, never retried silently.
- Check: the 95th percentile of the CI run is under 15 minutes for two weeks.

**Phase 3: replace the Thursday pass.**
- For each item on the Phase 0 list, decide how it gets caught instead: an automated test, a smoke test, or a feature flag that keeps unfinished work hidden until a person has tried it in production. `django-waffle` is the usual flag library, from memory, so check that it is still maintained.
- QA moves from checking each release to testing features behind flags and writing the smoke flows.
- Check: every item on the list has an owner and a replacement, and none was caught only by Thursday QA in the last four releases.

**Phase 4: migration safety.**
- Adopt expand/contract. Add columns as nullable or with defaults, deploy the code that uses them, and remove old columns in a later deploy.
- Run a migration linter in CI. `django-migration-linter` is from memory, so check it. Also run `sqlmigrate` review for any migration that touches large tables.
- Migrations run as a separate pipeline step before the new code rolls out. Any migration that would lock a big table needs a manual approval step.
- Check: one contract-style column removal done end to end without errors.

**Stage 1: daily push-button deploys.** Once Phases 1 to 4 are done, drop the weekly release. Anyone deploys `main` by pressing the button, at least daily, and not after 4 p.m. or on Fridays until the numbers look good. Keep this for at least four weeks.

**Stage 2: automatic deploy on merge, behind a gate.** All of these must be true:
- At least 4 weeks of daily deploys, with change failure rate (deploys needing rollback or a hotfix) at or below the Phase 0 baseline, and under 15%.
- Rollback has taken under 10 minutes every time it was used.
- The CI 95th percentile is under 15 minutes, and the pipeline success rate on `main` is above 95%.
- The on-call rotation is staffed, and an alert fires on error rate per release.

Inside each automatic deploy:
- Deploy to a canary, about 10% of instances, for 10 minutes first.
- If the 5xx rate or p95 latency on the canary is more than twice the rest, roll back automatically and stop the queue.

Revert rule for the stage: two user-visible incidents caused by deploys in one week puts the team back on push-button deploys until a review is done.

**Order reason:** deploy tooling and rollback come before more frequent deploys. Deploying daily without a fast rollback multiplies the weekly risk by five.

**Left out on purpose:** a rewrite into services. A monolith deploys continuously fine, and splitting it would add many weeks without helping the main goal.

**What the current arrangement gives for free:**
- A human looks at everything once a week. Replaced by tests, smoke flows and feature flags.
- A known release moment for support and customer communication. Replaced by a weekly changelog written from merged pull requests, decoupled from deploys.
- Release branches that batch changes. Replaced by short-lived branches merged to `main` daily, with flags hiding unfinished work.
