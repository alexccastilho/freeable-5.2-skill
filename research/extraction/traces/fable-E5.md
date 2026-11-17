# Migrating `users` (8M rows) from MySQL 5.7 to PostgreSQL 16 with no downtime

## Summary

The approach I recommend is a backfill plus binlog-based change capture into PostgreSQL, continuous verification, then a rehearsed cutover in which writes are held (not failed) for a few seconds, with reverse replication back to MySQL so you can roll back for two weeks afterwards.

Two things shape the plan more than the row count:

- **Only `users` is moving.** Every foreign key, join and transaction that spans `users` and a table staying in MySQL stops working once `users` lives elsewhere. Untangling that is most of the effort, and it has to be done before any data moves.
- **8M rows is small.** The backfill takes minutes to an hour. The risk is in the behavioural differences between the two databases and in the cutover, not in volume.

I have not seen your schema, application or infrastructure, so the plan below rests on the defaults in the next section. The estimate is 6 to 10 weeks, most of it in phase 1; treat that as a guess until the phase 0 inventory is done.

## Questions I would ask

| # | Question | Default I am assuming |
|---|---|---|
| 1 | Are the other tables moving to PostgreSQL later, or is `users` moving alone for good? | `users` is the first table of a wider migration, so the tooling should be reusable. |
| 2 | Does "zero downtime" allow writes to be held for a few seconds at cutover, as long as none fail? | Yes: up to about 10 seconds of added latency on user writes, once, with no errors and no maintenance page. |
| 3 | Which tables have foreign keys to `users`, and which queries join to it or write to it inside a larger transaction? | There are several of each, and they must be decoupled first. |
| 4 | Managed or self-hosted (RDS/Aurora, Cloud SQL, own hardware)? | Self-hosted or managed with binlog access; row-based binlog can be enabled. |
| 5 | What writes to `users` besides the main application (batch jobs, admin tools, other services, analysts, ETL readers)? | One main application plus a few jobs; all can be changed. |
| 6 | Which language and ORM, and is there a single data-access layer for users? | A mainstream ORM; user access is spread around and needs consolidating. |
| 7 | What is the write rate, and how much replication lag can reads tolerate? | Hundreds of writes per second at peak; reads after a write must see that write. |

If the answer to question 2 is "no pause at all", the cutover changes to application dual-writes with reconciliation. That is possible but costs more and has more ways to lose or diverge data, so I would only do it if a few seconds of latency is truly unacceptable.

## Phase 0: Inventory (about 1 week)

- Dump the `users` DDL: column types, character set, collation, indexes, triggers, defaults, `sql_mode`.
- List inbound and outbound foreign keys.
- Collect every query that touches `users` from the slow log, `performance_schema` digests and a code search. Classify each as a single-table read, single-table write, join, or part of a multi-table transaction.
- List every non-application reader and writer.
- Measure peak write rate, row size, and the hottest update patterns.

The output is a list of code changes for phase 1 and a type-mapping table for phase 2.

## Phase 1: Make the application ready (the bulk of the work)

All of this ships against MySQL, with no behaviour change, before PostgreSQL holds any data.

1. **One data-access seam.** Route every read and write of `users` through one module, with a runtime flag that selects the backing store per operation (`mysql`, `shadow`, `postgres`). The flag must change without a deploy.
2. **Remove joins to `users`.** Replace each with a lookup by ID through the seam, batched to avoid N+1 queries. Reports and analytics that need joins should move to a warehouse or a replica that has both data sets.
3. **Drop foreign keys that reference `users`.** Integrity moves to the application. Add a periodic orphan check to replace what the constraint gave you.
4. **Break up cross-table transactions.** Where a transaction writes `users` and another table, pick the order of writes and make the second step retryable (an outbox table is the usual tool). List each case and decide it explicitly; this is where data bugs come from.
5. **Port the SQL.** Things that differ and will bite:
   - `INSERT ... ON DUPLICATE KEY UPDATE` becomes `ON CONFLICT`; `LAST_INSERT_ID()` becomes `RETURNING`.
   - `LIKE` is case-sensitive in PostgreSQL.
   - PostgreSQL rejects values MySQL silently truncates or coerces when strict mode is off.
   - Ordering without `ORDER BY`, loose `GROUP BY`, backtick quoting.
6. **Run the user test suite against both stores in CI.**

## Phase 2: Build the PostgreSQL side

Write the schema by hand rather than accepting a tool's translation. The traps:

| MySQL | PostgreSQL | Note |
|---|---|---|
| Case-insensitive collation on `email` with a unique index | `citext`, or a unique index on `lower(email)` | Without this, `A@x.com` and `a@x.com` become two users. Check existing data for values that differ only by case or trailing spaces. |
| `utf8` (3-byte) or `latin1` columns | UTF-8 | Check for mis-encoded data. PostgreSQL text cannot hold NUL bytes. |
| `tinyint(1)` | `boolean` | Confirm no column stores values other than 0 and 1. |
| `int unsigned`, `bigint unsigned` | `bigint`, `numeric(20)` | |
| `datetime` | `timestamptz` | Decide which time zone the stored values are in. Getting this wrong shifts every timestamp. |
| `0000-00-00` dates | `NULL` | PostgreSQL has no zero date. |
| `ON UPDATE CURRENT_TIMESTAMP` | Trigger, or set in the application | Replication must not fire it; apply replicated rows with the trigger bypassed. |
| `AUTO_INCREMENT` | Identity column | Sequence is set at cutover, with headroom (see phase 5). |
| `enum`, `json` | `text` with a check or a native enum; `jsonb` | `jsonb` does not preserve key order or duplicate keys. |

Operational setup:

- Put PgBouncer (or equivalent) in front. PostgreSQL connections are costly compared with MySQL's, and an application sized for MySQL can exhaust them.
- Tune for an update-heavy table: lower `fillfactor` so updates stay on the same page, more aggressive autovacuum on this table.
- Replicas, backups with point-in-time recovery, monitoring and alerting in place before any production traffic. Test a restore.
- Load test with a replay or a realistic simulation of production write traffic at 2x peak.

## Phase 3: Backfill and change capture

1. On MySQL, confirm `binlog_format=ROW`, `binlog_row_image=FULL`, and binlog retention of several days. GTIDs make this easier. If a setting needs a restart, do it through a replica failover.
2. Start change capture from a consistent snapshot, so that the backfill and the change stream meet at a known binlog position with nothing lost or applied twice. Debezium does this itself; AWS DMS (full load plus CDC) does too. Take the snapshot from a replica to keep load off the primary.
3. Apply changes to PostgreSQL as idempotent upserts keyed on the primary key, and deletes as deletes.
4. Add a heartbeat row written every second in MySQL, so lag is measured directly in PostgreSQL.
5. Alert on lag and on any apply error. An apply error is a semantic difference you have not handled; stop and fix it, do not skip the row.

Why change capture rather than application dual-writes: the binlog sees every write, including jobs, admin tools and manual fixes, and it preserves order. Dual-writes miss anything outside the main code path and can leave the stores different when one write fails.

## Phase 4: Verify

- **Row counts and checksums.** Compare in primary-key ranges, on a canonical rendering of each row (normalised time zones, booleans, trailing spaces). Run continuously; re-check mismatched ranges after lag settles to separate real differences from in-flight changes.
- **Shadow reads.** Serve from MySQL, also read from PostgreSQL, compare in the background, log differences. Run for at least a week covering a peak.
- **Shadow query performance.** Compare latency for each query shape; fix plans and indexes now.
- **Limited real reads.** Send a small share of lag-tolerant reads to PostgreSQL to prove it under production conditions.

I would not move all reads to PostgreSQL ahead of writes. With heavy writes, any replication lag means a user updates their profile and then reads the old value. Moving reads and writes together at cutover avoids that.

## Phase 5: Cutover

Rehearse the whole sequence in staging until it is routine and timed. Then, at a low-traffic time:

1. Turn on the write hold: new writes to `users` wait at the seam; in-flight ones finish. Reads continue from MySQL.
2. Wait until PostgreSQL has applied everything, confirmed by binlog position and the heartbeat. This is normally under a second.
3. Stop forward replication.
4. Set the PostgreSQL identity sequence to `max(id)` plus a large gap (for example one million), so no late write can collide.
5. Start reverse replication, PostgreSQL to MySQL, from a logical replication slot created at this point. Only one direction is ever active, so there is no loop.
6. Flip the flag: reads and writes go to PostgreSQL.
7. Release the hold.

Expect 2 to 10 seconds of held writes. Put a hard timeout on the hold: if step 2 has not completed in, say, 15 seconds, release the hold with the flag still on MySQL and try another day.

Background jobs and other writers must be on the seam or paused for the cutover. Revoke write privileges on `users` in MySQL for everything except the reverse-replication user, so a missed writer fails loudly instead of silently writing to the old store.

## Phase 6: Rollback window and cleanup

- Keep reverse replication running for about two weeks. MySQL stays a current copy, and rollback is the same held-write flip in the other direction.
- Run the checksum comparison in reverse during this period.
- After the window: stop reverse replication, take a final archive of the MySQL table, rename it (do not drop yet), then drop it a few weeks later. Remove the MySQL path and the flag from the code.

## Go / no-go for cutover

All of these must be true:

- Zero unexplained checksum differences for 7 consecutive days.
- Shadow-read mismatch rate at zero, apart from documented, accepted cases.
- Replication lag under 1 second at peak for 7 days.
- PostgreSQL latency at or better than MySQL for every query shape, at 2x peak load.
- Cutover and rollback each rehearsed in staging at least twice, within the time budget.
- Every writer to `users` accounted for and on the seam.
- Backups restored successfully; on-call staff have the runbook.

## Main risks

| Risk | Mitigation |
|---|---|
| A cross-table transaction or join was missed | Phase 0 inventory from query digests, not only code search; MySQL privileges revoked at cutover so misses fail loudly. |
| Collation or time zone difference corrupts data quietly | Hand-written schema, canonical checksums, shadow reads. |
| An unknown writer keeps writing to MySQL | Privilege revocation; monitor the MySQL binlog for non-replication writes to `users` after cutover. |
| PostgreSQL struggles under update load | Load test at 2x peak; pooling, fillfactor, autovacuum tuned beforehand. |
| Rollback needed after new writes | Reverse replication keeps MySQL current. |

## What I need from you to firm this up

The `users` DDL, the list of tables with foreign keys to it, a query digest for a peak day, and answers to questions 1, 2 and 4. With those I can turn phases 1 and 2 into concrete tasks and a firmer schedule.

## Process log

1. Bash: listed all files in the fixture (`find`), ran `grep -rn "getUser"` over the fixture, and listed the traces output directory.
2. Bash: printed the contents of `package.json`, `README.md`, `src/admin/bulkImport.js`, `src/clock.js`, `src/db.js`, `src/notifications/mailer.js`, `src/orders/orderService.js`, `src/server.js`, `src/users/userService.js` and `test/orders.test.js`; ran `ls -la` in the fixture root; ran `git status` (not a git repository); ran a case-insensitive `grep -rniE "get_?user|fetch_?user"` over the fixture; listed the traces output directory (empty).
3. Called the advisor tool once.
4. Write: `fable-E7.md`.
5. Write: `fable-E5.md`.
