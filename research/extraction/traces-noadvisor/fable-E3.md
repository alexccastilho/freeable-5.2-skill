# Plan: duplicate rows in `transactions` from the nightly ETL

I have no access to the DAG, the logs or the database, so this is a plan, not a diagnosis. It has two halves: find what changed last Tuesday, and make the load safe to re-run so that no future change of this kind can produce duplicates again. The second half is worth doing whatever the first one finds.

I am reading "last Tuesday" as 10 November 2026, so about six nightly runs are affected.

## Step 0: stop it getting worse (today)

- **Decide whether tonight's run should go ahead.** If downstream consumers sum or count `transactions` (finance reports, billing), pause the DAG or warn them now. If they can tolerate another night, leave it running; more samples help the diagnosis.
- **Do not delete anything yet.** The duplicates are the evidence. Take a copy of the affected date range first (`CREATE TABLE transactions_dupes_backup AS SELECT ...`).

## Step 1: characterise the duplicates (about an hour, read-only SQL)

The shape of the duplicates narrows the cause more than anything else. Four queries answer it:

1. **How many, and since exactly when?** Group by load date and count rows against distinct business keys (the vendor's transaction ID, or whatever identifies a transaction). This confirms the start date and shows whether every night is affected.
2. **Are the copies byte-identical or slightly different?** Compare the duplicate pairs column by column, ignoring surrogate ID and load timestamp.
3. **Were the copies loaded in the same run or on different nights?** Compare their load timestamps or batch IDs, if the table has them.
4. **Is it every row or a subset?** For example only one file, one vendor account, or only rows near midnight.

How to read the answers:

| What you see | Most likely cause |
|---|---|
| Identical copies, loaded minutes apart on the same night | The task ran twice: a retry after a partial failure, or two DAG runs for the same date |
| Identical copies, loaded on different nights | The same file or the same records were picked up again: overlapping date window, file not marked as processed, or the vendor resending |
| Every row doubled every night since Tuesday | The vendor now sends cumulative files, or the file pattern now matches two files (for example `.csv` and `.csv.gz`) |
| Copies differ in one field (whitespace, ID format, timestamp, amount precision) | An existing dedupe or `ON CONFLICT` key stopped matching because the vendor changed a format, or a code change altered the key |
| Only rows near a date boundary | A time zone or date-window change |

## Step 2: find what changed on or just before Tuesday

Check these in order; each takes minutes and the first three cover most cases.

1. **Airflow run history for the DAG since 9 November.** Look for more than one DAG run per logical date, task retries (try number above 1), manually triggered or cleared runs, and backfill or catchup runs. A task that inserts, fails late and retries is the classic source of duplicates in a load that is not idempotent.
2. **Deploys.** `git log` on the DAG repository and on any shared library it imports, for the week before. Also image, Airflow and provider-package upgrades, and changes to Airflow Variables or Connections (their audit log is in the Airflow UI). Things to look for: a changed schedule, `catchup`, `retries`, the date-window logic, the file glob, or a switch from truncate-and-load or upsert to plain insert.
3. **The vendor's SFTP directory.** List files with sizes and modification times for the past two weeks. Look for a naming change, a second file per day, re-uploaded files, or files that have grown (cumulative instead of daily). Diff Monday's file against Wednesday's. Ask the vendor whether anything changed on their side; a one-line e-mail is cheap and they often know.
4. **Database changes.** Was a unique constraint or index on `transactions` dropped or altered, or a migration run, around that date? `pg_stat_user_tables` and your migration history will show it.
5. **Infrastructure.** A second scheduler, a restored or cloned environment (staging pointing at production Postgres), or a duplicated DAG file under a new `dag_id`. Query `pg_stat_activity` during the run or check which hosts connect.

I would stop as soon as the evidence from step 1 and one of these line up, and reproduce it once in a non-production environment by re-running the job against the same file.

## Step 3: fix the cause

This depends on the finding, so only the shape is fixed in advance:

- **Double execution:** remove the duplicate run or schedule, and make the task safe to retry (step 4 does this).
- **Reprocessed files or overlapping window:** correct the window or the processed-file tracking.
- **Vendor change:** adapt the parser or the key, or get the vendor to revert.
- **Dropped constraint:** restore it (after the cleanup in step 5, or it will fail to build).

## Step 4: make the load idempotent (the durable fix)

Right now the job's correctness depends on running exactly once on exactly the right input. Change it so that re-running it, or receiving the same record twice, cannot create a second row.

1. **Agree the business key.** Ideally the vendor's transaction ID, possibly combined with account or source. If the vendor provides no stable ID, use a hash of the fields that define a transaction. This is the one decision that needs someone who knows the data; see the questions below.
2. **Enforce it in Postgres** with a unique constraint or unique index on that key.
3. **Load through a staging table.** Each run copies the file into a staging table, dedupes within the file, then merges into `transactions` with `INSERT ... ON CONFLICT (key) DO UPDATE` (or `DO NOTHING` if transactions never change after the fact), all in one database transaction. A retry after a failure then starts clean.
4. **Record what was loaded.** A small `etl_file_log` table (file name, size, checksum, row count, run ID, loaded at) lets the job skip files it has already loaded and makes the next incident a five-minute query. Add `source_file` and `load_run_id` columns to `transactions` if they are not there.
5. **Airflow settings.** `max_active_runs=1` on the DAG, `catchup` set deliberately, and the date window derived from the run's data interval, not from the wall clock.

## Step 5: clean up the existing duplicates

1. Work on the backup from step 0 first and confirm the delete touches only the expected rows.
2. Pick the survivor rule: normally keep the earliest-loaded row per business key. If copies differ in content, decide which version is correct before deleting anything; that case needs a human check on a sample.
3. Delete with `ROW_NUMBER() OVER (PARTITION BY key ORDER BY loaded_at, id)` and remove everything with a row number above 1, inside a transaction, comparing the deleted count with the count from step 1.
4. Check whether other tables reference `transactions.id`. If they do, repoint those rows to the survivor before deleting.
5. Build the unique index after the cleanup. On a large table use `CREATE UNIQUE INDEX CONCURRENTLY` and then attach it as a constraint, to avoid blocking writes.
6. Tell downstream consumers which dates were wrong and that they are corrected, so that reports and aggregates built from those days can be rebuilt.

## Step 6: detect it next time

- A data-quality task at the end of the DAG that fails the run if the count of rows differs from the count of distinct keys for the loaded date.
- A row-count check against the file (rows in file equals rows merged plus rows skipped) and an alert on a large day-over-day swing.

## Order and effort

Steps 0 to 2 are half a day and should happen first. Steps 4 and 5 are one to two days of work plus review, and the unique constraint can only go in after the cleanup. If the root cause turns out to be trivial (for example a duplicated schedule), I would still do step 4: the constraint is what makes this class of problem impossible instead of merely fixed.

## Questions I would ask

1. **What uniquely identifies a transaction?** Default assumed: a vendor-supplied transaction ID exists and is stable. If not, I would use a hash of account, timestamp, amount and reference, and confirm with the vendor that two genuinely separate transactions can never share those values.
2. **Does `transactions` have a unique constraint today, and how does the job write (plain insert, truncate-and-load, upsert)?** Default assumed: plain append with no constraint, since duplicates were able to land.
3. **What changed around 9 to 10 November: a deploy, an Airflow upgrade, a manual backfill, a vendor notice?** Default assumed: nobody knows yet, which is why step 2 checks all of them.
4. **Can legitimate transactions be updated later by the vendor (corrections, reversals)?** Default assumed: yes, so the merge uses `DO UPDATE` and the latest file wins.
5. **Who consumes `transactions`, and has wrong data already gone out (reports, invoices)?** Default assumed: internal reporting only, so pausing is not required and a correction notice is enough.
6. **Do other tables reference `transactions.id`?** Default assumed: no, so duplicates can be deleted directly.
7. **How large is the table and the nightly load?** Default assumed: millions of rows in total and well under a million per night, so the cleanup and index build fit in a normal maintenance window.

## Process log

1. No files were read and no commands were run for this task. The shopmini fixture, which I had explored earlier for task E2, is unrelated to this job.
2. Wrote this file.
