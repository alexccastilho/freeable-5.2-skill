# Extraction tasks

Used to collect planning traces from Fable 5.2 and from Opus 5.5 with no skill loaded. The evaluation tasks are a separate, disjoint set.
The fixture repo lives at `research/fixtures/shopmini/`.

The tasks vary on purpose by size, ambiguity and domain. E7 is a control task where the right response is to just do it, not to plan.

## E1 — Greenfield tool
"I want a command-line tool that takes a folder of Markdown notes and publishes them as a static website I can host on GitHub Pages. Plan it."

## E2 — Brownfield feature (fixture: shopmini)
"Add rate limiting to the shopmini API. We got hammered by a bot last week." (Explore the fixture repo before planning.)

## E3 — Incident investigation
"Since last Tuesday our nightly ETL job (Python, Airflow, loads from a vendor SFTP into Postgres) has been producing duplicate rows in the `transactions` table. Plan how to fix this."

## E4 — Vague request
"Make our app faster." (Context: a React SPA + Node API used by about 2,000 B2B customers.)

## E5 — High-risk migration
"Migrate our `users` table (8M rows, heavy write traffic) from MySQL 5.7 to PostgreSQL 16 with zero downtime."

## E6 — Non-software project
"Plan a two-day offsite for 40 people from our company, in three months."

## E7 — Trivial change, control (fixture: shopmini)
"Rename the function `getUser` to `fetchUser` in shopmini."

## E8 — Large cross-cutting change
"Our single-tenant SaaS (Rails monolith, one Postgres DB per customer, 60 customers) needs to become multi-tenant on a shared database. Plan it."
