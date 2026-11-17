# Plan: move `users` (8M rows) from MySQL 5.7 to PostgreSQL 16 without downtime

## Summary

Copy the table to Postgres with change data capture (CDC), keep it continuously in sync from the MySQL binlog, prove the two copies match, then switch the application over in two steps: reads first, writes second. After the switch, replicate in the reverse direction so you can go back to MySQL without losing data.

Two things to know up front:

- **"Zero downtime" here means no failed requests, not zero pause.** Switching the single writer from MySQL to Postgres needs a write stall of a few seconds while replication drains. Requests wait and then succeed. The only way to avoid even that is to write to both databases at once, which I do not recommend for a table under heavy write load (reasons below).
- **The hard part is probably not the 8M rows.** That is a small data set; the initial copy takes minutes to an hour or so. The hard part is everything in MySQL that touches `users`: joins, foreign keys and transactions that span other tables. That depends on a question I cannot answer from here (question 1), and it can change the size of this project by an order of magnitude.

## Approach and why

**Recommended: CDC replication plus a staged cutover.** A tool reads a consistent snapshot of `users`, then streams every later change from the binlog into Postgres. The application keeps writing to MySQL only, so MySQL stays the single source of truth until the moment of cutover.

- **Tooling:** Debezium (Kafka Connect, or Debezium Server if you do not run Kafka) if self-managed; AWS DMS or the equivalent managed service if you are on a cloud that offers one. Either works at this size. I would pick whichever your team already operates.
- **MySQL prerequisites:** `binlog_format=ROW`, `binlog_row_image=FULL`, binlog retention of several days, and a replication user. Check these first: changing `binlog_format` on a busy 5.7 primary needs care, and if the binlog is not row-based today that is the first task.
- **Snapshot source:** take it from a replica if you have one, to keep load off the primary.

**Not recommended: application dual-writes.** Writing every change to both databases from the application looks simpler but gives you two writers with no shared transaction. Under heavy write traffic, a failure between the two writes or two concurrent updates arriving in different orders leaves the copies silently different. CDC applies changes in binlog order, so it does not have that problem.

## Phases

### Phase 0: inventory (2 to 4 days)

1. **Every query that touches `users`:** from the code, the ORM and the MySQL slow log or performance schema. Classify each as a plain read, a plain write, a join to another table, or part of a multi-table transaction.
2. **Every other consumer:** reporting tools, ETL jobs, other services, triggers, stored procedures, anything reading replicas.
3. **Foreign keys** pointing at `users.id` from other tables.
4. **Write rate and row size**, to size Postgres and to estimate replication lag at peak.

This inventory decides whether the plan below is enough or whether joins have to be rewritten first.

### Phase 1: schema translation (2 to 3 days)

Create the table in Postgres by hand, not by letting a tool guess. The differences that cause real incidents:

- **Case sensitivity.** MySQL's default collations compare text case-insensitively; Postgres does not. A unique index on `email` and every lookup by e-mail or username change behaviour. Use `citext` or a unique index on `lower(email)`, and check the existing data for values that differ only by case.
- **Auto-increment.** Use an identity column, and at cutover set the sequence above MySQL's maximum ID plus a safety margin. Forgetting this causes primary-key collisions on the first inserts.
- **Dates.** MySQL `DATETIME` has no time zone; decide whether it becomes `timestamptz` and which zone the old values were in. Zero dates (`0000-00-00`) are invalid in Postgres and must map to NULL.
- **Types.** `TINYINT(1)` to `boolean`, unsigned integers to the next larger type, `ENUM` to a check constraint or enum type, `JSON` to `jsonb`.
- **Text.** Postgres rejects NUL bytes in text and invalid UTF-8. If any column is `latin1` or old `utf8` (3-byte), scan for bad values before the copy.
- **Trailing spaces and padding.** MySQL ignores trailing spaces in comparisons for most collations; Postgres does not.
- **Indexes.** Recreate them to match the real query list from phase 0, not the MySQL index list.

### Phase 2: initial copy and continuous sync (about a week including soak)

1. Provision Postgres 16 with a replica, backups, monitoring and connection pooling (PgBouncer). MySQL applications often open far more connections than Postgres handles well.
2. Start the CDC snapshot, then let streaming run.
3. Monitor replication lag and alert on it. Target: under a few seconds at peak write load. If it cannot keep up at peak, fix that before going further.
4. Let it run through at least one full weekly traffic cycle.

### Phase 3: verification (runs continuously from here on)

1. **Row counts and checksums** by primary-key range, compared between the two databases, repeated on a schedule. Compare normalised values, since types differ.
2. **Row-level sampling** of recently modified rows.
3. **Shadow reads.** The application reads from MySQL as usual and, for a sample of requests, also reads from Postgres in the background and logs any difference. This catches the collation, time zone and NULL-handling differences that checksums miss, and it exercises the Postgres query paths and indexes under real traffic.
4. **Load test the write path** on Postgres at peak rate before cutover; Postgres has different locking and vacuum behaviour under heavy updates.

Do not proceed until the mismatch rate is zero or every remaining mismatch is explained.

### Phase 4: move reads (1 to 2 weeks, gradual)

Behind a feature flag, send a growing percentage of read queries to Postgres: 1%, 10%, 50%, 100%. Because Postgres lags MySQL by a moment, keep reads that follow a write in the same request on MySQL until phase 5. Rollback at this stage is flipping the flag back.

### Phase 5: move writes (the cutover, minutes of work, seconds of stall)

Rehearse this on staging at least twice. The sequence:

1. Start reverse replication tooling in a stopped state (Postgres to MySQL), ready to turn on.
2. Pause writes to `users` at the application or proxy layer. Requests queue; they do not fail.
3. Wait until CDC lag is zero and confirm the last MySQL binlog position has been applied.
4. Set the Postgres sequence above the MySQL maximum ID.
5. Flip the write flag to Postgres and release the queued writes.
6. Make MySQL `users` read-only (revoke write privileges) so any missed code path fails loudly instead of writing to the old table.
7. Start reverse replication so that MySQL keeps receiving every change.

Expected stall: 2 to 10 seconds if lag is healthy. Do it at the lowest-traffic hour, with an abort rule: if lag has not drained in 30 seconds, release the writes back to MySQL and try another day.

### Phase 6: rollback window and decommission (2 to 4 weeks)

- While reverse replication is running, going back to MySQL is the same procedure as phase 5 in the other direction.
- Once you are confident, stop reverse replication, take a final MySQL backup of the table, and drop it later, not the same day.

## Main risks

| Risk | Mitigation |
|---|---|
| Queries join `users` with tables still in MySQL | Found in phase 0; must be rewritten as two queries or served from a read-only copy before cutover |
| Behaviour differences (case, time zones, NULL ordering) surface after cutover | Shadow reads in phase 3 |
| CDC cannot keep up at peak | Measured in phase 2; tune batch apply or pick a quieter cutover time |
| A forgotten writer keeps writing to MySQL | MySQL table made read-only at cutover |
| Sequence collision on first inserts | Explicit step in the cutover runbook |
| Rollback loses data | Reverse replication from the moment of cutover |

## Rough timeline

Five to eight weeks elapsed for a small team, most of it soak and gradual rollout, not engineering. If phase 0 finds many joins or cross-table transactions on `users`, add the time to untangle those before phase 4; that could be weeks more.

## Questions I would ask

1. **Is only `users` moving, or is this the first table of a full migration to Postgres?** Default assumed: `users` is moving first and the other tables stay in MySQL for now. That means foreign keys to `users.id` in MySQL stop being enforced, and joins have to be dealt with as described. If the whole database is moving, I would migrate all tables through the same CDC pipeline and cut over once, which avoids the split entirely and is usually the better project.
2. **Does one application own all access to `users`, or do several services and tools query it directly?** Default assumed: one main application plus some reporting readers, so feature flags in one codebase control the switch.
3. **Is a write stall of a few seconds acceptable under your definition of zero downtime?** Default assumed: yes. If not, the cutover needs dual-writing with conflict handling, which adds risk and several weeks.
4. **Where is this hosted, and is the binlog already row-based?** Default assumed: a cloud provider with a managed migration service available, binlog in ROW format, at least one MySQL replica.
5. **What is the peak write rate on `users`, and which columns change most?** Default assumed: hundreds to low thousands of writes per second, which CDC handles comfortably.
6. **How do the other MySQL tables that reference `users.id` need to behave after the move?** Default assumed: they keep the same IDs, with integrity enforced by the application.
7. **Is there a deadline, for example tied to MySQL 5.7 being past end of life?** Default assumed: no hard date, so the gradual rollout above is acceptable.

## Process log

1. No files were read and no commands were run for this task. The shopmini fixture, which I had explored earlier for task E2, is unrelated to this migration.
2. Wrote this file.
