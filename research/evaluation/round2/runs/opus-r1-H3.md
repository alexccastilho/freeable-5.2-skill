# Moving from weekly releases to continuous deployment

This is doable for a 14-person Django monolith, but it's a transition and not a switch. Today the weekly cadence is propping up two things: a **35-minute test suite** and a **manual QA pass on Thursdays**. If you deploy on every merge without replacing them, you either queue merges behind a slow pipeline or ship untested changes. So the plan works on those two first, then increases deploy frequency in steps.

## Questions I would ask

1. **What does Thursday QA actually catch?** Look at the last 2–3 months of bugs found in QA versus bugs found in production.
   *Default:* QA mostly re-checks a handful of critical flows (signup/login, payments, core workflows) plus whatever changed that week. That's automatable, mostly with E2E smoke tests.
2. **Are there compliance or contractual constraints** (SOC 2 change management, customer-notified release windows, regulated data)?
   *Default:* SOC 2-style change control at most. A PR review plus an automated pipeline record satisfies it.
3. **How do you deploy today?** (ECS, EC2 with Ansible, Elastic Beanstalk, Kubernetes) And how long does a deploy and a rollback take?
   *Default:* a scripted but manually triggered deploy to EC2 or ECS that takes about 15–30 minutes. Rollback is "redeploy the previous tag".
4. **How are database migrations handled?**
   *Default:* `manage.py migrate` runs during the Friday deploy, sometimes with downtime, and nobody enforces backward compatibility.
5. **What does "continuous deployment" mean to the team?** Every merge to main goes to production automatically, or deploy-on-demand many times a day?
   *Default:* the goal is automatic deploy on merge, reached through an intermediate stage of "anyone can deploy main with one click, several times a day".
6. **Is there a staging environment that resembles production?**
   *Default:* yes, but it's only used for Thursday QA.

## The real blockers, and how to remove them

### 1. The 35-minute suite
Target: **under about 10 minutes from push to green.**
- **Measure first.** Run with `pytest --durations=50` (or the Django runner's timing) to find where the time actually goes. Usually a small fraction of tests account for most of the runtime.
- **Parallelise:** `pytest-xdist -n auto` on one large runner, or shard across CI jobs (`pytest-split` using stored durations). With 4–8 shards, a 35-minute suite typically lands at 6–10 minutes, assuming the tests are isolated.
- **Cheap Django wins:**
  - `--reuse-db` / `--nomigrations` (or a pre-built test DB image).
  - A fast password hasher (`MD5PasswordHasher`) in test settings.
  - In-memory email/cache backends.
  - Avoiding `TransactionTestCase` where `TestCase` would do.
  - Factory instead of fixtures for large data sets.
- **Fix the order dependence and flakiness that parallelising will expose.** Quarantine flaky tests with an owner and a deadline, rather than letting retries hide them.
- Optionally, run the full suite on main and a targeted subset on PRs. I'd only do that after sharding, because it adds complexity.

### 2. Thursday manual QA
- Turn the QA checklist into **automated smoke/E2E tests** (Playwright) for the critical flows. Run them against staging before production promotion, and against production right after deploy.
- Change QA's role from gatekeeper of the release to **exploratory testing of features behind flags** before they're turned on. QA effort moves to the point of feature release, not code deploy.
- Keep a short manual check only for things that are really hard to automate. Don't let it block deploys.

### 3. Decouple deploy from release: feature flags
- Adopt a flag system (`django-waffle` is enough, or LaunchDarkly/Unleash if you want targeting and an audit trail).
- Incomplete work merges dark. Product and QA turn features on for internal users, then for a percentage, then for everyone.
- Add a rule for removing flags (an expiry date or a ticket), or they pile up.

### 4. Make migrations safe to run on every deploy
- **Expand/contract**: add a column as nullable, deploy code that writes to both, backfill, switch reads, then drop the old column in a later deploy. Never rename or drop in the same deploy as the code change.
- Add a CI check (`django-migration-linter` or `squawk` if on Postgres) that flags backward-incompatible or table-locking migrations.
- Run long data migrations as background jobs, not inside `migrate`.
- This matters because during a rolling deploy old and new code run against the same schema at the same time.

### 5. Deploy mechanics and safety net
- **Build once, promote the same artifact:** a Docker image tagged with the commit SHA goes to staging and then to production.
- **Rolling or blue/green deploys** (ECS rolling with health checks, or CodeDeploy blue/green), with **automatic rollback** on failed health checks or an alarm.
- **Canary** if possible: send 5–10% of traffic to the new version for about 10 minutes, compare error rate and p95 latency, then proceed.
- **Observability:** error tracking (Sentry) tagged with the release SHA, plus CloudWatch or Datadog alarms on 5xx rate and latency. A deploy marker on dashboards.
- **One-command rollback** that takes under 5 minutes, and is practised.
- Keep **small PRs** and trunk-based development: short-lived branches, merges at least daily.

## Phased rollout

| Phase | Duration (rough) | Change | Exit criteria |
|---|---|---|---|
| 0. Baseline | 1–2 wks | Measure deploy lead time, change-failure rate, MTTR, test durations; inventory what QA catches | Numbers on a dashboard |
| 1. Fast and safe pipeline | 3–6 wks | Shard tests, build immutable images, automated deploy to staging on every merge, smoke tests, one-click prod deploy plus rollback, migration linting | CI under about 10 minutes; staging always running main; rollback tested |
| 2. Release more often | 4–6 wks | Deploy to prod **daily** (still with a human clicking), then several times a day. Introduce feature flags. Thursday QA becomes exploratory testing on flagged features | Deploys are boring; change-failure rate not worse than baseline |
| 3. Continuous deployment | ongoing | Merge to main auto-deploys to staging, then smoke tests, then canary, then prod, with auto-rollback. Humans only intervene on failure | Several deploys per day with no manual step |

Each phase stands on its own. If the team stops after Phase 2, it's still a big improvement over weekly releases.

## Team and process changes
- **"You merge it, you watch it":** the author keeps an eye on dashboards for about 30 minutes after their change reaches production.
- A deploy freeze switch, for incidents and high-risk periods, that anyone can flip.
- Lightweight on-call if there isn't one already. With deploys during working hours, issues surface during working hours, which is a plus.
- Blameless review for any failed deploy, focused on what the pipeline should have caught.
- Tell QA and stakeholders early. QA's job changes rather than disappears, and that needs to be clear so it isn't seen as cutting them out.

## Risks to watch
- **Moving to frequent deploys before tests are fast and trustworthy.** You get either a merge queue backlog or people bypassing CI.
- **Migrations.** These are the most common cause of incidents in this kind of move. Enforce expand/contract from day one of Phase 2.
- **Flag debt.** Budget time to delete flags.
- **Background workers (Celery etc.) and scheduled jobs** must tolerate running mixed versions during a rollout, the same as web servers. Task signatures need to stay backward compatible.

## Suggested first steps this week
1. Profile the test suite and get a breakdown of where the 35 minutes goes.
2. Collect the last quarter of QA-found and production-found bugs to see what the Thursday pass really protects against.
3. Write down the current deploy and rollback procedure and time it.

From those three results I can turn this into a concrete backlog with estimates. I can also start immediately on test parallelisation, because that's the step most likely to pay off quickly.
