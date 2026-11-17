# Plan: single-tenant Rails monolith to multi-tenant on a shared Postgres database

## Summary

Add a `tenant_id` to every tenant-owned table, enforce tenant scoping in the application with Postgres row-level security underneath as a safety net, and move the 60 customers into the shared database one at a time while the application can serve both kinds of customer. No big-bang cutover.

I have not seen the codebase, so the sizes below are estimates. Three decisions shape the whole project and need a human answer; I have assumed a default for each and marked it:

1. **Isolation model:** shared tables with a `tenant_id` column (assumed), not a schema per tenant.
2. **What happens to record IDs,** since the 60 databases all have their own `id = 1`. This is the hardest technical problem in the project.
3. **Whether every customer may be moved** to shared infrastructure under their contract.

## Decision 1: isolation model

**Recommended: one set of tables, a `tenant_id` column on each, plus row-level security.**

- **Why not a schema per tenant** (the Apartment gem pattern): it is the smallest code change, but it keeps most of today's costs. Every migration still runs 60 times, connection pooling fights with `search_path` switching, and it scales badly as customer count grows. If the reason for this project is operational cost or cross-customer features, schemas do not deliver it.
- **Why row-level security as well as application scoping:** in a shared table, one forgotten `WHERE tenant_id = ?` shows one customer's data to another. Application scoping (the `acts_as_tenant` gem, or a hand-rolled equivalent on `ActiveSupport::CurrentAttributes`) is the first line; a Postgres policy that filters on a per-connection setting is the second, and it also covers raw SQL and the console.

## Decision 2: record IDs

Sixty databases with overlapping integer IDs cannot be merged as they are. Options:

| Option | Effect | Cost |
|---|---|---|
| **Offset per tenant** (recommended): new ID = old ID + tenant number × a large constant | IDs become globally unique; mapping is a formula, so it is reversible and easy to verify | Every foreign key, polymorphic reference and ID stored in JSON or text must get the same offset. IDs visible to customers change |
| Composite keys `(tenant_id, id)` | Old IDs survive unchanged | Invasive in Rails: needs 7.1 or later, and every association and many gems are affected |
| New IDs (UUID or fresh sequence) with a `legacy_id` column | Clean end state | A mapping table per model during import; slowest and most error-prone import |

I recommend the offset because the mapping is deterministic: you can verify a migrated tenant by formula, redirect old URLs inside a tenant, and reverse the import if needed. It requires `bigint` keys throughout. The real risk is IDs hidden outside foreign-key columns: polymorphic `_id` columns, JSON blobs, serialized columns, file-storage keys, search indexes, and anything customers have stored on their side (API integrations, bookmarked URLs). Finding those is an explicit task in phase 0.

If customers hold IDs in external integrations and those cannot change, composite keys become the better choice despite the cost. That is question 2 below.

## Phases

### Phase 0: audit (1 to 2 weeks)

1. **Schema drift.** Compare the 60 schemas and migration versions. They are supposed to be identical; after years they often are not (hot fixes, custom columns, extensions). Everything must be brought to one schema before any merge.
2. **Table classification.** Tenant-owned, global reference data (plans, countries), or system tables.
3. **ID inventory.** Every place an ID is stored outside a normal foreign key, as described above.
4. **Uniqueness inventory.** Every unique index and `validates uniqueness`. Almost all must become unique per tenant (for example user e-mail).
5. **Everything outside the request cycle that assumes one customer:** background jobs, scheduled tasks, mailers, caches, sessions, file storage paths, search indexes, rate limits, feature flags, analytics, raw SQL, reports, admin tools, per-customer configuration in environment variables.
6. **Sizes.** Rows and bytes per customer, to order the migration and size the shared database.
7. **Contracts.** Which customers have clauses on data isolation, data residency or dedicated infrastructure.

### Phase 1: make the application tenant-aware while still single-tenant (4 to 8 weeks, the bulk of the work)

All of this ships to the existing 60 deployments with no visible change. That is the point: the risky code changes are tested in production before any data moves.

1. Add a `tenants` table and a `tenant_id` column (nullable at first, then backfilled with the customer's own ID, then `NOT NULL`) to every tenant-owned table in every database.
2. Resolve the current tenant per request (subdomain or the existing per-customer hostname) and set it for the request, and fail closed: no tenant, no query.
3. Scope every tenant-owned model. Change unique indexes and validations to include `tenant_id`. Add `tenant_id` as the leading column of the indexes that serve the main queries.
4. Carry the tenant through background jobs (serialize it with the job and restore it in the worker), mailers, cache keys, file-storage paths, search indexes and sessions.
5. Remove or wrap every unscoped query and raw SQL statement. A test-suite check that fails on any query against a tenant table without a tenant filter is worth building here.
6. Add the row-level security policies, enforced for the application's database role.
7. **Tests:** a two-tenant fixture and a cross-tenant leak suite that tries, for every endpoint and job, to read tenant B's data as tenant A.

### Phase 2: shared database and dual-mode routing (2 to 3 weeks)

1. Provision the shared database, sized from phase 0, with connection pooling, backups and monitoring broken down per tenant.
2. Make the application choose its database per tenant from a routing table: "this tenant lives in its old database" or "this tenant lives in the shared database". Rails' multiple-database support covers this. Now both kinds of customer run on the same code, and moving a customer is a data operation plus one routing change.
3. If today each customer has a separate application deployment, consolidating those into one deployment belongs here. That is question 4.

### Phase 3: build and rehearse the tenant import (2 to 3 weeks)

1. A repeatable import job per tenant: copy from the customer's database, apply the ID offset to every key and reference from the phase 0 inventory, load into the shared tables, move or re-key files and search documents.
2. **Verification per tenant:** row counts per table, checksums on content, referential integrity, and a scripted walk through key screens comparing old and new.
3. Rehearse on copies of production data for the smallest and the largest customer. Measure duration; that decides between a short maintenance window per customer and a no-downtime import using logical replication. For most customers a window of minutes at night is far simpler.
4. Write the rollback: flip the routing entry back to the old database, which stays untouched and read-only for a retention period.

### Phase 4: migrate customers in waves (4 to 8 weeks)

1. **Pilot:** an internal or demo tenant, then two or three small, friendly customers. Hold for a week or two.
2. **Waves** of increasing size, largest and most sensitive customers last. Each customer: announce, freeze writes, import, verify, flip routing, monitor.
3. Stop the waves on any cross-tenant finding or unexplained verification mismatch.

### Phase 5: clean up (2 weeks)

Remove the dual-mode routing and per-customer deployment tooling, decommission the old databases after the retention period, and replace per-database operational habits: per-tenant export, per-tenant restore (no longer "restore the database"), and tenant deletion.

## Main risks

| Risk | Mitigation |
|---|---|
| Cross-tenant data leak | Application scoping, row-level security, leak test suite, fail-closed tenant resolution |
| IDs missed in the offset (JSON, polymorphic, external systems) | Phase 0 inventory; per-tenant referential verification; rehearsal on real copies |
| Schema drift blocks the merge | Found and fixed in phase 0, before any other work |
| One large customer degrades everyone | Per-tenant monitoring, tenant-leading indexes, statement timeouts, limits on heavy jobs; consider partitioning the largest tables by tenant later |
| A customer needs a point-in-time restore | Build per-tenant export and restore tooling before the first real customer moves |
| A contract forbids shared infrastructure | Found in phase 0; those customers stay on a dedicated database, which dual-mode routing already supports |

## Timeline and team

Roughly four to six months for two to four engineers, with phase 1 the largest and least predictable part. It depends heavily on the size of the codebase and how much raw SQL and background processing it has. Phase 0 will tighten the estimate, and I would treat its output as the checkpoint to confirm or change this plan.

## Questions I would ask

1. **Why move to multi-tenant: operating cost, deployment pain, cross-customer features, faster onboarding?** Default assumed: operating cost and onboarding speed, which favours shared tables over schema-per-tenant.
2. **Are record IDs visible to customers (URLs, API, exports, integrations), and can they change?** Default assumed: they appear in URLs and can change with redirects, so the offset approach is acceptable. If API integrations depend on them, switch to composite keys.
3. **Do any contracts or regulations require dedicated databases or a specific region?** Default assumed: no, all 60 can move. Customers who cannot will stay on dedicated databases.
4. **Is there one application deployment per customer today, or one deployment that switches database?** Default assumed: one deployment per customer, so consolidating deployments is part of phase 2.
5. **Are the 60 schemas identical, and do any customers have custom code or columns?** Default assumed: the same code and nearly the same schema, with minor drift to clean up.
6. **Which Rails and Postgres versions, and are primary keys `bigint`?** Default assumed: Rails 7 or later, a supported Postgres, `bigint` keys. Older Rails or `integer` keys add upgrade work before phase 1.
7. **How large are the biggest customers, and is a short maintenance window per customer acceptable?** Default assumed: the largest is tens of gigabytes and a night-time window of under an hour is fine.
8. **Is there a deadline or a team-size constraint?** Default assumed: no fixed date, and two to four engineers.

## Process log

1. No files were read and no commands were run for this task. The shopmini fixture, which I had explored earlier for task E2, is unrelated to this system.
2. Wrote this file.
