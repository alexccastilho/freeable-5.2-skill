# Moving a single-tenant Rails SaaS (60 customer databases) to a shared multi-tenant database

## Summary

I recommend row-level tenancy: a `tenant_id` on every tenant-owned table, enforced by the application and backed by PostgreSQL row-level security, with customers migrated one at a time in waves.

The key sequencing decision is to make the application tenant-aware while each customer still has its own database. The code becomes multi-tenant, is deployed to all 60 customers and runs in production before any data moves. Data migration is then a separate, per-customer, reversible step.

Before committing, check one thing: **what the goal is.** If it is mainly to cut the cost of running 60 databases, a schema per customer inside one database gets most of that for a fraction of the work, because primary keys do not collide and the code barely changes. It does not scale well past a few hundred customers and keeps 60 copies of every migration. I assume below that you want real shared tables.

I have not seen the codebase. My rough estimate is 4 to 6 months for a small team; the audit in phase 0 will show whether that holds.

## Questions I would ask

| # | Question | Default I am assuming |
|---|---|---|
| 1 | What is driving this: operating cost, onboarding speed, growth beyond 60, cross-customer features? | Cost and onboarding speed, with growth expected. Row-level tenancy is the right target. |
| 2 | Do any contracts promise a dedicated database, data residency in a region, or customer-managed encryption? | A few customers do. The routing layer must keep supporting dedicated databases permanently for them. |
| 3 | Do all 60 run the same code version and schema? | Same code; small schema drift (missed migrations, hand-added indexes or columns). |
| 4 | Are integer record IDs visible outside the app: URLs, public API, webhooks, customer integrations, exports? | Yes. Changing them is a breaking change that needs managing. |
| 5 | Can each customer accept a short read-only window, out of hours, for its own cutover? | Yes, up to about 30 minutes, scheduled with notice. |
| 6 | How big is the largest customer compared with the rest, and what is the total data size? | One or two customers are far larger than the median; total fits comfortably on one primary with replicas. |
| 7 | How are customers identified on a request today: subdomain, separate deployment, separate domain? | A subdomain or domain per customer, mapped to a database by configuration. |
| 8 | Rails and PostgreSQL versions; which job system, cache, search and file storage? | Rails 7.x, PostgreSQL 14 or later, Sidekiq, Redis, object storage via Active Storage. |

## Design decisions

### Tenant column and enforcement

- A `tenants` table. Every tenant-owned table gets `tenant_id bigint NOT NULL` with a foreign key to it. Tables that are truly global (plans, feature definitions) are listed explicitly and have none.
- **Application layer:** tenant set once per request in `Current.tenant`, resolved from the host. Models are scoped automatically; `acts_as_tenant` does this, or a small concern of your own. Running without a tenant raises an error unless wrapped in an explicit, logged `without_tenant` block for admin and maintenance code.
- **Database layer:** row-level security on every tenant table, with a policy comparing `tenant_id` to a session setting. The application sets it with `SET LOCAL` inside each transaction, which is safe with PgBouncer in transaction mode. The application's database role must not own the tables or have `BYPASSRLS`; use `FORCE ROW LEVEL SECURITY`. Migrations and the migration tool use a separate role.

Both layers are needed. Application scoping alone fails on the first raw SQL query or forgotten `unscoped`; the database policy turns that from a data leak into an empty result.

### Primary keys

Sixty databases each have a `users` row with ID 1. Options:

| Option | Effect | Verdict |
|---|---|---|
| Add a per-tenant offset to every ID and every foreign key on import | Simple, mechanical, keeps single-column keys and Rails conventions. IDs change. | **Recommended.** |
| Composite keys `(tenant_id, id)` | IDs preserved. Every association, join and gem has to cope with composite keys. | Too invasive. |
| New UUIDs | No collisions ever. Every foreign key rewritten through a mapping; larger indexes. | Only if you want UUIDs anyway. |

With offsets, all keys must be `bigint` first. The hard part is finding every place an ID is stored outside a foreign key column: polymorphic `*_id` columns, IDs inside JSON or serialised columns, audit and version tables, Active Storage attachments, queued job arguments, search indexes, caches, and external systems such as a billing provider's metadata. Phase 0 must list these.

If IDs are public (question 4), keep a `(tenant_id, legacy_id)` lookup so old URLs and API calls can be redirected or translated for a deprecation period, and tell customers ahead of time.

### Constraints and indexes

- Every unique index gains `tenant_id` as its first column (email unique per tenant, not globally). Check login: it must resolve the tenant before looking up the user.
- Most existing indexes should lead with `tenant_id`.
- Optional hardening: composite foreign keys `(tenant_id, parent_id)` so a row cannot reference another tenant's parent.

### Everything outside the database

Each of these needs tenant context, and each is a place data can leak:

- **Background jobs:** middleware that stores the tenant with the job and restores it on execution. Scheduled jobs iterate over tenants.
- **Cache:** tenant in every key, including fragment caches and rate-limit counters.
- **File storage:** tenant prefix in object keys; signed URLs checked against the tenant.
- **Search indexes:** tenant filter on every query, or an index per tenant.
- **Action Cable channels, mailers, exports, reports, analytics.**
- **Rails console and rake tasks:** require an explicit tenant.
- **Logs and error reports:** tag with tenant ID.

## Phases

### Phase 0: Audit (2 to 3 weeks)

- Diff the schema of all 60 databases; list drift.
- Inventory tables (tenant-owned or global), unique constraints, and every non-foreign-key place an ID is stored.
- Find raw SQL, `unscoped`, `find_by_sql`, and direct connection use.
- List integrations, jobs, caches, file storage, search.
- Read the contracts for isolation and residency terms.
- Measure sizes and peak load per customer.

### Phase 1: Tenant-aware application on the existing databases

All of this deploys to the 60 separate databases with no visible change.

1. Converge all 60 schemas to one version.
2. Convert keys to `bigint` where needed.
3. Add `tenants` and `tenant_id` to every tenant table. Backfill with that customer's tenant ID, then set `NOT NULL`. Use the usual safe-migration steps for large tables.
4. Add tenant resolution, `Current.tenant`, model scoping, and the job, cache and storage changes.
5. Rebuild unique indexes with `tenant_id`, concurrently.
6. Turn on row-level security.
7. Tests: fixtures with two tenants in one database; a suite that asserts tenant A cannot see tenant B through every controller, job and API endpoint; a CI check that fails when a new table lacks `tenant_id` and a policy, or is not on the global list.

Outcome: the code is multi-tenant and proven in production, while each customer's blast radius is still one database.

### Phase 2: Shared database and routing

- Provision the shared database: sized for all customers plus headroom, replicas, point-in-time recovery, connection pooling, monitoring broken down by tenant.
- A tenant directory mapping each tenant to `dedicated` or `shared`, used by Rails multi-database connection switching per request and per job. Migrated and unmigrated customers run side by side on the same code.
- Schema migrations now run against the shared database and every remaining dedicated one.

### Phase 3: Migration tool

A repeatable, per-tenant tool that:

1. Puts the tenant in read-only mode.
2. Copies each table into the shared database, in dependency order, applying the offset to IDs and all ID references.
3. Advances the shared sequences past the imported range.
4. Verifies: row counts per table, checksums of non-ID columns, referential integrity, a sample of records compared through the application, and a zero-rows check for the tenant's ID range belonging to anyone else.
5. Flips the directory entry to `shared`, clears the tenant's caches, reindexes search.
6. Lifts read-only mode.

Rollback is flipping the directory entry back; the dedicated database is untouched and was read-only during the copy. After the tenant has taken writes on the shared database, rollback needs a reverse export, so build and test that before wave 2.

Rehearse against restored copies of real customer databases, including the largest, and time them.

### Phase 4: Migrate in waves

| Wave | Who | Purpose |
|---|---|---|
| 0 | Internal and demo tenants | Prove the tool end to end. |
| 1 | 3 to 5 small, low-risk customers | Soak for two weeks. |
| 2 onward | Batches of 5 to 10, by size | Steady pace; stop on any verification failure. |
| Last | The largest customers | Benefit from everything learned; may need a longer window or an online copy. |

Customers with contractual isolation stay on dedicated databases unless the contract changes.

Stop criteria for any wave: a verification mismatch, a cross-tenant result in any log or test, or shared-database latency above the agreed threshold.

### Phase 5: Clean up

- Keep each old database, read-only, for a retention period (for example 30 days), then take a final backup and delete it.
- Remove the dedicated path only if no customer needs it; otherwise keep it as a supported tier.

## What you lose, and what replaces it

| Today, free with separate databases | Replacement to build |
|---|---|
| Restore one customer from backup | Per-tenant export and import tool; point-in-time restore to a side database, then extract one tenant. |
| Delete a customer by dropping a database | Tenant deletion job covering every table, files, search and caches. |
| One customer's heavy query hurts only them | Statement timeouts, per-tenant rate limits and job queue limits, per-tenant query monitoring; move a very large tenant to a dedicated database if needed. |
| Customer data export on request | Per-tenant export, same tool as above. |
| An outage affects one customer | An outage affects all. Invest in failover, safe-migration checks and staged rollouts. |

## Main risks

| Risk | Mitigation |
|---|---|
| Cross-tenant data leak | Two enforcement layers; two-tenant test suite; CI check on new tables; a security review before wave 1. |
| An ID reference missed during re-keying | Phase 0 inventory; verification through the application; rehearsal on real copies. |
| Schema drift breaks an import | Converge schemas in phase 1, before any migration. |
| Shared database performance | Tenant-leading indexes; load test with the combined workload before wave 2; keep the dedicated tier as an escape. |
| Public IDs change | Legacy ID lookup, deprecation period, customer notice. |
| The project stalls halfway | Each phase leaves a working system; phase 1 alone is useful, and mixed dedicated and shared running is a supported state. |

## What I need to firm this up

Access to the repository and one schema dump, the answers to questions 1, 2 and 4, and a size and load figure per customer. With those I can produce the phase 0 inventory and a task-level plan for phase 1.

## Process log

1. Bash: listed all files in the fixture (`find`), ran `grep -rn "getUser"` over the fixture, and listed the traces output directory.
2. Bash: printed the contents of `package.json`, `README.md`, `src/admin/bulkImport.js`, `src/clock.js`, `src/db.js`, `src/notifications/mailer.js`, `src/orders/orderService.js`, `src/server.js`, `src/users/userService.js` and `test/orders.test.js`; ran `ls -la` in the fixture root; ran `git status` (not a git repository); ran a case-insensitive `grep -rniE "get_?user|fetch_?user"` over the fixture; listed the traces output directory (empty).
3. Called the advisor tool once.
4. Write: `fable-E7.md`.
5. Write: `fable-E5.md`.
6. Write: `fable-E6.md`.
7. Write: `fable-E8.md`.
