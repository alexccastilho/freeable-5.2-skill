I would get there in stages over roughly a quarter, with each stage useful on its own. The Friday release and the Thursday QA pass go away last, once the things they currently protect you from are covered another way. The timings below are estimates; they depend on the answers to the questions at the end.

## What has to be true first

Continuous deployment means every merge to main goes to production without a person deciding. For that to be safe with your setup, four things have to change:

- **The 35-minute suite.** At 14 engineers it turns into a merge queue. The target is under 10 minutes.
- **The Thursday QA pass.** It is a weekly gate by design. Whatever it catches has to be caught per change instead.
- **Unfinished work.** Today it can sit on main until Friday. With continuous deployment it reaches production the moment it merges, so it needs to be hidden behind flags.
- **Database migrations.** During a rolling deploy, old and new code run against the same schema at once. Every migration has to be compatible with both.

## Stages

### 1. Measure the starting point (week 1)

- **Friday releases:** how long they take, how often they are rolled back or hotfixed, and how long a rollback takes.
- **Thursday QA:** list what it found over the last two or three months. This tells you which automated checks to write and how much the gate is really buying you.
- **Test suite:** where the 35 minutes go, and how often it fails for reasons unrelated to the change.

### 2. Make the deploy boring (weeks 1 to 4)

Keep releasing weekly, but change how.

- **One command, no manual steps.** The pipeline builds one artifact, deploys it to staging, then promotes the same artifact to production.
- **Zero downtime.** Rolling or blue/green, with health checks that stop the rollout.
- **Rollback in minutes.** Redeploy the previous artifact, and rehearse it.
- **Migrations as a separate step.** Adopt expand-then-contract: add the column, deploy code that works with both, remove the old one in a later deploy. Add a CI check that flags dropped or renamed columns, and locking operations on large tables.
- **Background jobs.** If you use Celery, task signatures need the same both-versions rule, because queued tasks outlive a deploy.

### 3. Speed up and trust the tests (weeks 2 to 6, in parallel)

- **Parallelise.** Split the suite across CI workers and run it in parallel within each (`pytest-xdist`, or `manage.py test --parallel`). This is normally the largest single saving.
- **Fix the slowest tests.** A small share of tests normally accounts for much of the runtime.
- **Quarantine flaky tests.** A suite people re-run until it passes can't gate production.
- **Add smoke tests.** A short end-to-end set covering sign-in, the main paid flow and whatever QA found most often, run against staging after each deploy.

### 4. Separate deploying from releasing (weeks 4 to 8)

- **Feature flags.** Incomplete or risky work merges dark and is turned on separately, for staff first.
- **Short-lived branches.** Merge to main daily, with main always deployable and branch protection requiring green CI and one review.
- **QA moves earlier.** QA tests features behind flags in production or staging before they are switched on, and does exploratory testing, in place of a Thursday sign-off on a batch.

### 5. Raise the frequency (weeks 6 to 10)

- **Daily deploys with a person pressing the button.** This surfaces the remaining problems at low risk.
- **Automatic deploy to staging on every merge**, followed by the smoke tests.
- **Automatic deploy to production**, with a canary or staged rollout and automatic rollback on error rate or latency.

### 6. Operate it (ongoing)

- **Monitoring tied to deploys.** Error rate, latency and key business metrics, with deploy markers on the dashboards and alerts to the person whose change went out.
- **Ownership.** Whoever merges watches their change reach production.
- **Track four numbers.** Deploy frequency, time from merge to production, share of deploys that cause a problem, and time to recover.

## Where this usually goes wrong

- **Skipping stage 2.** Automating a deploy that is fragile by hand makes failures more frequent, not less.
- **Removing QA before stage 3 is done.** The gate should go when its findings have dried up, not on a date.
- **Flags that never get removed.** Give each one an owner and a removal date.
- **A destructive migration.** This is the failure a rollback can't undo, which is why the CI check in stage 2 matters.

## Questions I would ask

1. **What is driving the change?** Default assumed: faster delivery and smaller, safer releases, not a specific incident.
2. **How is the app deployed today, and how does it run on AWS?** Default assumed: a partly scripted deploy to ECS or EC2 behind a load balancer, with RDS Postgres.
3. **What does Thursday QA find in a typical week?** Default assumed: a small number of real regressions, mostly in a few critical flows that can be automated.
4. **Are there compliance or customer commitments that require change approval or release notes?** Default assumed: none beyond code review, which serves as the approval record.
5. **Do mobile apps or external API clients depend on the monolith?** Default assumed: yes, so API changes must stay backward compatible, which the flag and migration rules already cover.
6. **Is there a dedicated QA person or team, and are they part of this decision?** Default assumed: one or two people, whose role shifts to exploratory testing and owning the smoke tests.
7. **Who will own the pipeline work?** Default assumed: one or two engineers at roughly half time for the quarter.
