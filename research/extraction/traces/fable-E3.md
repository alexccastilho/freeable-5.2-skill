# Plan: duplicate rows in `transactions` from the nightly ETL

I cannot see the DAG, the table, or the logs, so this plan does not name a cause. The duplicates started on a specific day, which means something changed on or just before that day. The plan is to find that change first, stop the damage, then make the load safe to re-run so the same class of problem cannot recur, and only then clean up the existing rows.

I am reading "last Tuesday" as 10 November 2026. If you mean 3 November, the steps are the same with a longer window.

## Questions I would ask

1. **What identifies a transaction uniquely?** A vendor transaction ID, or a combination of columns? Default: the vendor supplies a stable ID per transaction. Step 1 tests this before anything relies on it.
2. **Does `transactions` have a primary key or unique constraint on that identifier today?** Default: no. If it had one, the duplicates could not have been inserted.
3. **What changed around 10 November?** A deploy, a DAG edit, an Airflow or provider upgrade, a change to retries or schedule, a manual re-run or backfill, or a notice from the vendor. Default: unknown, to be found in step 2.
4. **Who reads `transactions`?** Reports, finance exports, downstream tables. Default: there are downstream consumers that have already read duplicated data and will need a re-run or correction after cleanup.
5. **Can I query production read-only and read the Airflow logs?** Default: yes. Without that, step 1 has to be run by someone who can.
6. **Is the load append-only, or can the vendor legitimately send corrections to an earlier transaction?** Default: append-only. If corrections exist, "duplicate" needs a more careful definition and the fix becomes an update on conflict instead of a skip.

## Step 1: Describe the duplicates (read-only, about an hour)

The shape of the duplicates narrows the cause more than reading code does.

```sql
-- How many, and since when?
SELECT vendor_txn_id, COUNT(*) AS copies, MIN(loaded_at), MAX(loaded_at)
FROM transactions
GROUP BY vendor_txn_id
HAVING COUNT(*) > 1
ORDER BY MIN(loaded_at);
```

Column names are placeholders. What to read from the result:

| Observation | Points toward |
|---|---|
| Copies are identical in every column | The same file or the same rows loaded twice |
| Copies differ in some columns (amount, status, timestamp) | The vendor is sending updated records, or a parsing change (time zone, number format) |
| Every row from a night is doubled | The whole task ran twice: retry after partial success, two DAG runs for one date, a manual re-run |
| Only some rows are doubled | Overlapping files, or an overlapping extraction window |
| Copies were loaded seconds or minutes apart | Retry or concurrent runs |
| Copies were loaded a day apart | The same file picked up on consecutive nights, or the vendor re-sending prior days |
| Nothing before 10 November, some every night since | A lasting change (code, configuration, vendor format) |
| Only the night of 10 November | A one-off event such as a backfill or manual re-run |

If the table has no load timestamp or source file column, compare row counts per night against the vendor file line counts instead, and note the missing columns as something step 4 adds.

## Step 2: Find what changed

Check these in order, cheapest first. Each one is a specific thing to look at, with the evidence that confirms or rules it out.

1. **Repository history.** `git log` on the DAG and its helpers from 3 to 11 November. Look for changes to the load statement, file matching pattern, dedup logic, retries, `schedule`, `catchup`, or `start_date`.
2. **Airflow run history for the DAG.** More than one DAG run per logical date, task instances with a try number above 1, manually triggered runs, cleared tasks. A task that inserts rows, fails afterwards, and retries will insert again.
3. **Task logs for the first bad night.** Which files were downloaded, how many rows each produced, and whether any file name appears twice or appears again the next night.
4. **The vendor SFTP folder.** Has the file naming changed, are files now cumulative (each containing earlier days), are yesterday's files being left in place or re-uploaded, are there both a `.csv` and a compressed copy? A changed file name defeats any "already processed" check that works by name.
5. **How the job remembers what it has loaded.** If it moves or deletes files after loading, check that this still succeeds (permissions on the SFTP can change). If it tracks processed files in a table or an Airflow Variable, check that it is still being written.
6. **Platform changes.** Airflow, provider package, or Postgres driver upgrades, and any change to the table itself, such as a dropped constraint or index around that date.

Step 2 ends with a cause I can demonstrate: re-running the load for one affected night in a staging copy reproduces the duplicates, and the same run with the suspected change reverted does not. If I cannot reproduce it, I do not have the cause yet.

## Step 3: Stop new duplicates (same day)

Pick the smallest action that step 2 supports:

- if a code or configuration change caused it, revert that change;
- if the vendor changed their delivery, add a temporary filter for the specific overlap;
- if the cause is still unknown by the end of the day, pause the DAG only if downstream users would rather have late data than wrong data. That is a business decision and I would ask whoever owns the reports.

## Step 4: Make the load idempotent

This is the durable fix, and it is worth doing whatever the cause turns out to be. A nightly load from an external source will be re-run, retried, and re-sent files over its lifetime, so running it twice for the same input must leave the table unchanged.

1. **Load into a staging table first**, one batch per run, with the source file name and the run's logical date recorded on each row.
2. **Move rows to `transactions` in a single database transaction** using `INSERT ... ON CONFLICT (vendor_txn_id) DO NOTHING`, or `DO UPDATE` if question 6 shows that corrections are real.
3. **Add a unique constraint on the business key.** This cannot be created while duplicates exist, so it is applied at the end of step 5. Until then, the insert uses `WHERE NOT EXISTS` against the same key.
4. **Record processed files** (name, size, checksum, row count, run) in a small table, and skip a file whose checksum has already been loaded. The checksum covers the case of a renamed file with the same content.
5. **Keep the task safe to retry**: all writes for a run commit together or not at all, so a retry after a failure starts clean.

Tests, written before the change to the load: loading the same file twice yields the same row count as loading it once; loading two files that overlap yields each transaction once; a failure midway followed by a retry yields each transaction once.

## Step 5: Clean up existing duplicates

This step deletes production data, so it has its own safeguards and needs your sign-off on the rule before it runs.

1. **Agree the survivor rule.** For identical copies, keep the earliest loaded row. For copies that differ, the rule depends on step 1 and on the answer to question 6, and I would bring you examples before choosing.
2. **Check what references these rows.** If other tables hold foreign keys to the surrogate ID of a row that is about to be deleted, those references are repointed to the survivor first.
3. **Copy the rows to be deleted into a backup table**, and confirm its count matches the count from step 1.
4. **Run the delete in a transaction** on a staging copy first, then in production. Before committing, check that the number of deleted rows equals the backup count and that the duplicate query from step 1 returns nothing.
5. **Add the unique constraint** from step 4. On a large table, build the unique index with `CREATE UNIQUE INDEX CONCURRENTLY` and then attach it as a constraint, to avoid blocking writes.
6. **Tell downstream owners** which dates were affected so they can re-run aggregates and reissue anything already sent out. Totals for 10 November onward have been overstated wherever they were computed from this table.

The backup table is kept until downstream owners confirm their numbers, then dropped.

## Step 6: Detect it next time

- A final task in the DAG that fails the run if the duplicate query returns any rows. With the constraint in place this should never fire, which makes it a cheap check that the constraint is still there.
- A row count comparison per run: rows in the vendor files against rows staged against rows inserted, written to the log and alerted on when they diverge beyond an agreed tolerance.
- An alert when a run inserts zero rows or skips every file, since the idempotent load will now absorb a re-sent file silently.

## Order and effort

| Step | When | Depends on |
|---|---|---|
| 1. Describe | Day 1 | Read access |
| 2. Find the change | Day 1 | Step 1 |
| 3. Stop new duplicates | Day 1 | Step 2, or a decision to pause |
| 4. Idempotent load | Days 2 to 3 | Business key confirmed |
| 5. Cleanup and constraint | After step 4 is deployed and one clean night has passed | Survivor rule agreed |
| 6. Detection | With step 4 | None |

Cleanup comes after the fix on purpose: cleaning first would mean cleaning again after every night the faulty load runs.

## What would change this plan

- **There is no stable business key.** Then deduplication has to use a hash of the full row plus the source file, and legitimate identical transactions (two equal purchases in the same second) need a vendor-supplied sequence number to tell apart. I would raise that with the vendor.
- **The copies are not identical.** Then this may be a vendor data change and not a pipeline fault, and step 4 becomes an upsert with rules about which version wins.
- **The table is very large.** The cleanup and index build would be batched and scheduled outside the load window.

## Process log

1. Ran one shell command in the shopmini fixture: `find` to list files, `wc -c` for file sizes, and `ls` of the traces output folder. This was a single exploration pass done before starting any of the four tasks.
2. Ran one shell command in the shopmini fixture: `cat -n` over `package.json`, `README.md`, `src/server.js`, `src/db.js`, `src/clock.js`, `src/admin/bulkImport.js`, `src/notifications/mailer.js`, `src/orders/orderService.js`, `src/users/userService.js`, `test/orders.test.js`; then `ls -la` of the fixture root and `ls` of the traces output folder. None of this was used for this task.
3. Called the advisor tool once.
4. Wrote this file with the Write tool.
