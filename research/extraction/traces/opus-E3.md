# E3: Duplicate rows in `transactions` since last Tuesday, plan

Short version: stop the bleeding, find out *what changed on Tuesday* and *what kind* of duplicates these are, then fix the cause and make the load idempotent so it can't happen again. Last, clean up existing duplicates carefully. Don't jump straight to `DELETE ... USING` + a unique constraint. The kind of duplicate decides the right fix, and deleting rows first destroys the evidence.

I don't have access to the DAG or the database, so this plan comes with the queries and checks I'd run, plus questions for you.

## Questions I would ask

1. **Does `transactions` have a natural/business key from the vendor** (e.g. `vendor_txn_id`), and is there any unique constraint on it today? Default: **there's a vendor transaction id, but no unique constraint.** That's the usual reason duplicates can get in at all.
2. **How does the load write?** Plain `INSERT`/`COPY` append, `INSERT ... ON CONFLICT`, or truncate-and-reload of a staging table? Default: **append via COPY/INSERT, with no idempotency.**
3. **What changed around last Tuesday?** Deploys to the DAG or loader, Airflow upgrade, retries/`catchup` settings, vendor file naming/format, new files on the SFTP, a schedule or timezone change, infra changes. Default: **unknown. Finding this is step 2 of the plan.**
4. **How do downstream consumers use `transactions`** (finance reports, billing, reconciliation)? Has anyone already acted on inflated numbers? Default: **downstream reporting depends on it**, so the timeline and a communication to stakeholders matter.
5. **Is there a staging/raw table or an archive of the vendor files we can re-derive from?** Default: **vendor files are still on the SFTP or archived somewhere.** Check retention before relying on that.
6. **Can I pause the DAG or add a guard today?** Default: **yes for a guard, no for pausing without your go-ahead**, since a pause delays reporting.

## Step 0: Contain (today)

- Don't run manual backfills or "clear task" re-runs until the cause is known; those can add more duplicates.
- Pick one of these:
  (a) pause the DAG,
  (b) add a post-load check task that fails the run if duplicates by key appear for that load window, or
  (c) put a dedup view in front of consumers (`SELECT DISTINCT ON (vendor_txn_id) ...`) and point reports at it.
  Default: **(b) + (c)**. Data keeps flowing, consumers see correct numbers, and we get alerted.
- Take a snapshot of the affected rows (`CREATE TABLE transactions_dupe_snapshot AS SELECT ... WHERE loaded_at >= '<last Monday>'`) before anyone cleans anything up.

## Step 1: Characterize the duplicates (about an hour of SQL)

The *shape* of the duplicates points to the cause:

```sql
-- How many, since when, per load date
SELECT date_trunc('day', loaded_at) d, count(*) total,
       count(*) - count(DISTINCT vendor_txn_id) dupes
FROM transactions WHERE loaded_at >= now() - interval '21 days'
GROUP BY 1 ORDER BY 1;

-- Are duplicates exact copies or do they differ?
SELECT vendor_txn_id, count(*), count(DISTINCT (amount, status, txn_ts, ...)) variants,
       array_agg(DISTINCT source_file), array_agg(DISTINCT loaded_at), array_agg(DISTINCT dag_run_id)
FROM transactions WHERE loaded_at >= '<last Monday>'
GROUP BY 1 HAVING count(*) > 1 LIMIT 50;
```

(Column names are guesses; I'd adapt to the real schema.) Each pattern points somewhere different:

| Pattern | Likely cause |
|---|---|
| Same row, **same source file, different `loaded_at` / run id** | Task retry or re-run that isn't idempotent (Airflow retry after a partial commit, a cleared task, `catchup`/backfill, two overlapping DAG runs) |
| Same row, **different source file names** | Vendor re-delivering data (cumulative/rolling files, re-sent files, new naming so the "already processed" check misses them) |
| Same key, **different field values** | Vendor sending *updates/corrections* that we insert as new rows, but that should be upserts. These aren't really duplicates, and deleting them would be wrong |
| Exactly 2× everything from one day on | Loader now runs twice (duplicate DAG after a rename, two schedulers, schedule/timezone change) |
| Duplicates only within a single file | The vendor file itself contains duplicates. Check the raw file |

## Step 2: Find the Tuesday change

- `git log --since="last Monday"` on the DAG / loader repo, and the deployment history.
- Airflow UI: runs and task tries for Monday through Wednesday. Look for retries, manually cleared tasks, two runs for the same logical date, `max_active_runs`, a changed `schedule`/`start_date`/`catchup`, or a renamed `dag_id` (which leaves the old DAG active too).
- Airflow/provider version changes (e.g. SFTP provider or sensor behaviour).
- SFTP: list files and modification times since last Monday. New naming? Files re-uploaded? Cumulative files now instead of daily deltas? Ask the vendor if they changed anything.
- The "already processed" mechanism, if there is one: how does it decide a file is new (filename? a processed table? moving files to `/archive` on the SFTP)? A permission change that stops the move/delete on the SFTP would cause every night to reload old files. That's a classic cause.

Exit criterion: one cause that explains the counts from Step 1, ideally reproduced in a dev environment by replaying Tuesday's files and run.

## Step 3: Fix: cause + idempotency (both)

1. **Fix the specific cause** found in Step 2 (revert the change, fix the file-tracking, dedupe overlapping runs, handle the vendor's new file format, etc.).
2. **Make the load idempotent regardless of the cause.** Any retry or re-run should then produce the same table state:
   - Load each file into a **staging table** first, recording `source_file`, file checksum and `dag_run_id`.
   - Keep a **`processed_files`** table (filename + checksum + row count + status). Skip files already loaded successfully.
   - Merge staging into `transactions` in **one transaction** using `INSERT ... ON CONFLICT (vendor_txn_id) DO UPDATE` (if the vendor sends corrections) or `DO NOTHING` (if records are immutable). Which one depends on what Step 1 showed.
   - Alternatively, for date-partitioned loads: `DELETE WHERE load_date = {{ ds }}` + insert, in one transaction.
   - Airflow: `max_active_runs=1` on the DAG, and check that retries can't re-insert a partial commit.
3. **Add the unique constraint** on the business key (`CREATE UNIQUE INDEX CONCURRENTLY`). This only works *after* the cleanup in Step 4, so it comes in the same release. It's the safety net that turns a future duplicate into a loud failure instead of silent bad data.

## Step 4: Clean up existing duplicates

- Decide the survivor rule from Step 1: exact copies → keep the earliest `id`; versions of a record → keep the latest by vendor timestamp (or whatever the business rule is; confirm with whoever owns the data).
- Dry run first: count what would be deleted and compare with the Step 1 numbers and the vendor's file row counts.
- Then, in a transaction, after a backup/snapshot:
  ```sql
  DELETE FROM transactions t USING transactions k
  WHERE t.vendor_txn_id = k.vendor_txn_id AND t.id > k.id
    AND t.loaded_at >= '<last Monday>';
  ```
- Check foreign keys first: do other tables reference the duplicate `transactions.id`s? If so, repoint them before deleting.
- Reconcile totals per day against vendor file totals for the affected dates.
- Tell downstream consumers which dates were affected and that the numbers are now correct. Some reports may need to be re-run.

## Step 5: Verification & prevention

- Test: run the loader twice on the same file in dev and confirm the row count doesn't change. Test a mid-load failure + retry the same way.
- Keep the post-load data quality check from Step 0 permanently (duplicate count by key = 0; row count ≈ file row count).
- Alert on row-count anomalies vs. the trailing average.

## Order of work and rough effort

| Step | When | Effort |
|---|---|---|
| 0 Contain + snapshot | today | ~1h |
| 1 Characterize | today | ~1–2h |
| 2 Root cause | today/tomorrow | a few hours (depends on what changed) |
| 3 Fix + idempotency + tests | 1–2 days | |
| 4 Cleanup + constraint | same release as 3 | ~half day incl. reconciliation |
| 5 DQ checks/alerts | with 3 | ~2h |

If you can share the DAG file, the loader code and the `transactions` DDL, I can turn Steps 1 and 3 into concrete queries and a diff.

## Process log

1. Wrote this file. No files were read and no commands were run for this task (no ETL code was available in the environment; the shopmini fixture is unrelated).
