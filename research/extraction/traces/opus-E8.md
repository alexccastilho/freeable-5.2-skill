# Single-tenant to multi-tenant (shared DB): plan

This is a large, risky migration. The safest approach makes tenant isolation **structural and enforced at the database**, not something each developer has to remember in every query. Customers then move one at a time, with a rollback path at each step. Below are the questions that most affect the design, the defaults I'm assuming, and a phased plan.

## Questions I would ask

1. **Why move?** Ops cost, migration time across 60 DBs, cross-tenant analytics, a planned move to self-serve signups? Default: ops cost and deploy/migration complexity, plus planned growth to hundreds of customers.
2. **Do any customers have contracts that require physical isolation** (dedicated DB, data residency, a compliance regime such as HIPAA or SOC 2 commitments)? Default: a few may. The design keeps the option of a dedicated shard for them.
3. **Are the 60 schemas identical** (same migrations, same Rails version), or has there been per-customer drift? Default: mostly identical, with some drift that needs detecting and reconciling.
4. **Data size.** Largest tenant and total? Default: total under 1–2 TB, largest tenant under 20% of the total. One shared Postgres cluster (plus replicas) is enough to start.
5. **How do requests identify the tenant today?** Subdomain, separate deployments per customer, a separate env/DATABASE_URL? Default: one deployment per customer, or a per-request DB switch by subdomain.
6. **Background jobs, caches, file storage, search indexes?** Default: Sidekiq + Redis, ActiveStorage on S3, possibly Elasticsearch. All of these need tenant scoping too.
7. **Downtime tolerance per customer migration?** Default: a short scheduled window (under 30 minutes) per customer is acceptable, announced in advance.
8. **Team size and timeline?** Default: 3–4 engineers, about 6 months.

## Key design decisions

**1. Isolation model: shared tables with a `tenant_id` column** (row-level), as you asked. The alternatives were schema-per-tenant (Apartment-style, which doesn't scale well and the Apartment gem is effectively abandoned) and keeping a DB per tenant. Shared tables give the best operational simplicity at your scale.

**2. Enforcement in two layers:**
- **App layer:** the `acts_as_tenant` gem (or a hand-rolled `Current.tenant` + `default_scope`-style concern). It auto-scopes queries and sets `tenant_id` on create.
- **DB layer: Postgres Row-Level Security (RLS)** as the backstop. Each table gets a policy `USING (tenant_id = current_setting('app.tenant_id')::bigint)`. The app connects as a non-owner role without `BYPASSRLS` and runs `SET LOCAL app.tenant_id = ...` per transaction/request. A missed scope then returns zero rows instead of leaking another customer's data. Watch two things: PgBouncer transaction pooling requires `SET LOCAL` inside a transaction (not session-level `SET`), and migrations and admin tooling use a separate role.

**3. Primary keys.** Merging 60 databases creates ID collisions (every tenant has `users.id = 1`). Options:
- (a) Re-key during import: new IDs, rewrite all FKs through mapping tables. Correct, but heavy and it breaks external references (URLs, API clients, webhooks that carry IDs).
- (b) **Composite keys `(tenant_id, id)`**. Rails 7.1+ supports composite primary keys. Preserves the old IDs, and the tenant ID is on every index anyway.
- (c) Switch to UUIDs. Big change.

Default: **(a) with new `bigint` IDs plus a `legacy_id` column and an ID-mapping table per tenant**, with redirects for old URLs, *unless* public URLs and APIs expose IDs widely. In that case go with (b). This is the decision I would most want to settle with you early, since it shapes the import tooling.

**4. Indexes and constraints.** Every unique constraint becomes tenant-scoped (`UNIQUE (tenant_id, email)`). Every FK and index leads with `tenant_id`. Consider foreign keys that include `tenant_id`, so a row cannot reference another tenant's row.

**5. Global vs. tenant tables.** Classify every table: tenant-owned (most), global (plans, feature flags, countries), or join tables. Global tables don't get RLS.

## Phase 0: Discovery (2–3 weeks)

- Schema diff across all 60 DBs (`pg_dump --schema-only` + diff). Reconcile drift so every tenant DB is on the same migration version.
- Inventory every table and classify it (tenant / global). Find every raw SQL string, `find_by_sql`, `connection.execute`, reporting query, rake task and data-fix script.
- Inventory per-tenant state outside the DB: Redis keys, cache keys, S3 prefixes, search indexes, cron jobs, per-customer env config and secrets (SSO, SMTP, API keys).
- Size the data and find the largest tenants.
- Decide the PK strategy (decision 3).

## Phase 1: Make the codebase tenant-aware while still single-tenant (6–8 weeks)

This is the most important trick: **ship all the multi-tenant code into the existing per-customer deployments first.** Each customer DB gets a `tenants` table with one row and `tenant_id` on every table, all set to that one value. Then the code is exercised in production with no cross-tenant risk yet.

1. Add a `tenants` table and the `Current.tenant` resolution (subdomain or custom domain to tenant) in a middleware/controller concern. Fail closed: no tenant means no data access.
2. Migrations: add a nullable `tenant_id` to every tenant table, backfill it in batches, then make it `NOT NULL`. Add the composite indexes (`algorithm: :concurrently`) and make the uniqueness constraints tenant-scoped.
3. Add `acts_as_tenant` to all tenant models. Audit raw SQL and add tenant predicates.
4. Background jobs: serialize `tenant_id` into every job and restore `Current.tenant` in a Sidekiq server middleware. Jobs without a tenant raise unless explicitly marked global.
5. Namespace cache keys, Redis keys, S3 paths and search indexes by tenant.
6. Move per-customer config (env vars) into a `tenant_settings` table or encrypted credentials keyed by tenant.
7. Enable RLS policies in **permissive/log mode first**, and turn on enforcement once tests pass.

**Testing:** a test helper that runs specs with *two* tenants and asserts that tenant A can never see tenant B's data, including a request-spec sweep across every controller and every API endpoint. Add a CI check (a RuboCop rule or custom lint) that flags new raw SQL against tenant tables without a tenant predicate.

## Phase 2: Build the shared cluster and import tooling (3–4 weeks, overlaps Phase 1)

- Provision the shared Postgres 16 cluster: primary + replica, PgBouncer, backups/PITR, monitoring. Size it for 1.5–2× the current total.
- Write the **tenant import tool**: export one tenant DB, remap IDs (if strategy (a)), load into the shared DB inside a transaction or staging schema, then verify with row counts per table, per-table checksums of the important columns, and FK integrity checks.
- Write the **reverse tool** (export a tenant from the shared DB back into a standalone DB). It's needed for rollback, for customers who later require dedicated hosting, and for offboarding/GDPR data export. Tenant deletion becomes `DELETE ... WHERE tenant_id = X` across tables in dependency order.
- Rehearse the import of every tenant into a staging copy of the shared cluster. Fix failures and record the timings.

## Phase 3: Migrate tenants in waves (6–8 weeks)

1. **Internal/demo tenant first**, then 2–3 small, friendly customers, then waves of about 10, with the largest and most sensitive customers last.
2. Per-tenant runbook: announce a window → set the tenant to maintenance mode → final export → import + verify → switch routing (tenant lookup now points at the shared DB) → smoke tests as that tenant → lift maintenance → keep the old DB read-only for 30 days.
3. **Rollback per tenant:** flip routing back to the old DB. Any writes made after cutover are exported with the reverse tool. Once you have confidence, shorten the window in which rollback is offered.
4. Monitor per-tenant query latency, especially noisy-neighbor effects. Add per-tenant statement timeouts and rate limits, and consider partitioning the largest tables by `tenant_id` (hash or list) if they grow big.

Routing during the transition: the app needs to serve both "old dedicated DB" and "shared DB" tenants. Use Rails multi-database (`connects_to` / `connected_to(shard:)`) with a `tenants.database_shard` column. That same mechanism later lets you put one big or regulated customer on its own shard while the code stays the same.

## Phase 4: Decommission and harden (2–4 weeks)

- Drop the old DBs after the retention period and a final backup.
- Collapse the per-customer deployments into one deployment, and simplify CI/CD and migrations (one migration run instead of 60).
- A security review focused on tenant isolation, ideally with an external pen test against cross-tenant access.
- Update the DPA, security docs and the incident runbook (for example "how to restore a single tenant from backup", which is much harder in a shared DB. Build and test that tool *before* you need it).

## Timeline (default team of 3–4)

| Months | Work |
|---|---|
| 1 | Discovery, schema reconciliation, PK decision, cluster design |
| 2–3 | Tenant-aware codebase shipped into existing single-tenant deploys; RLS in log mode |
| 3–4 | Shared cluster, import/export tools, full rehearsals |
| 4–6 | Tenant waves, then decommission and hardening |

## Top risks and mitigations

| Risk | Mitigation |
|---|---|
| Cross-tenant data leak | RLS backstop, fail-closed tenant resolution, two-tenant test suite, lint for raw SQL |
| ID collisions / broken external references | Decide the PK strategy up front, legacy-ID mapping, URL redirects |
| Schema drift between tenants | Reconcile in Phase 0, before any import |
| Background jobs running without tenant context | Sidekiq middleware that raises when the tenant is missing |
| Noisy neighbors | Per-tenant timeouts and limits, a dedicated shard option |
| Single-tenant restore becomes hard | Build the export/restore tool in Phase 2 and test it regularly |
| Contractual isolation requirements | Check contracts in Phase 0; keep the shard option for those customers |

My suggested next step: run the Phase 0 discovery (schema diff plus a table classification) and settle the primary key strategy. Those two outputs drive everything else. If you share the schema and how tenant routing works today, I can draft the concrete migration order and the `Current.tenant`/RLS wiring.

## Process log

1. Wrote this file (no repository or files were relevant to this task; no files read, no commands run for it).
