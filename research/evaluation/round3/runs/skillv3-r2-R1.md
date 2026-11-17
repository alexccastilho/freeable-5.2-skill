shopmini is built as an internal warehouse tool (the README calls it "small order-management API used by our warehouse team"), and nothing in it yet assumes an outsider can reach it. That gap is where most of the work is, not code quality. Every route is open, the client sets the order total, and a request with an unknown user can very likely take the whole process down. So the order I recommend is: first stop anyone outside from reaching or crashing it, then make placing an order safe to retry, then the operational basics (backups, logs, restarts), then a staged launch behind a go/no-go list. I read every file in the repository but have not run anything. `npm install` fails on this machine because `better-sqlite3` does not build, so the crash below comes from reading the code and is the first thing to confirm. I read "next month" as December 2026.

## What I found that changes the request

- **No route has any authentication** (`src/server.js`, lines 6-9). Anyone who can reach the port can mark orders shipped and bulk-overwrite tracking codes through `/admin/shipments/import`. -> Access control comes first, before anything customer-facing.
- **`GET /orders/:id` takes sequential integer IDs with no ownership check** (`server.js:7`, `orderService.js:13`). -> Any customer can read every other customer's order by counting up from 1.
- **`userId` and `totalCents` come straight from the request body** (`server.js:6`). -> A caller chooses whose order it is and what it costs. There is no product or price table in the schema (`src/db.js`), so the server has nothing to check the price against.
- **An unknown `userId` likely crashes the process.** `placeOrder` inserts the row and then calls the mail template with `getUser()` returning `undefined`. `user.name` throws outside the `try` (`mailer.js:11`). The async route handler rejects, Express 4 does not catch rejected promises, and Node's default for an unhandled rejection is to exit. -> One bad request stops the service for everybody and leaves an order row with no user behind it.
- **The foreign key is not enforced.** `REFERENCES users(id)` is declared, but SQLite ignores it unless `PRAGMA foreign_keys = ON` is set, and `db.js` never sets it. -> Orphan orders are possible today.
- **The confirmation e-mail is sent inside the request, and failures are swallowed** (`mailer.js:9-13`). -> A slow SMTP server makes checkout slow and invites retries, which create duplicate orders. A failed send leaves no record.

## Questions I would ask

Q1. Who calls this API: customers' browsers or apps directly, or a storefront server of yours? Default: only your own servers and warehouse staff call it, and every route requires a credential. If customers' browsers call it directly, a browser cannot keep a service key secret, so the plan gains customer accounts or sessions plus per-order ownership checks. That is the largest single addition, and it goes at the front of phase 1.

Q2. Where does the price come from? Default: the trusted caller from Q1 computes it, and the API only checks that it is a positive integer. If no trusted caller exists, a `products` table and server-side pricing are added before launch.

Q3. Can a confirmation e-mail be late, or lost? Default: minutes late is fine, lost is not, so the plan uses an outbox table with retries. If occasional loss is acceptable, sending after the response and logging failures is enough.

Q4. How will it be hosted: one process or several, and is there TLS in front? Default: one process on one machine behind a TLS proxy, with SQLite kept. If it runs as several instances or on serverless, SQLite has to be replaced, and that becomes its own phase.

Q5. The launch date in December, expected orders per day, and who does the work? Default: low hundreds of orders a day and one developer, with phases 1 and 2 done before launch.

Answer first: Q1 and Q4. Each one can add a phase.

## Plan

### Phase 1: nobody outside can crash it, read others' orders or change shipments

1. **Error handling.** In `src/server.js`, wrap every handler so a rejected promise reaches an error middleware that returns a 500 without stopping the process. In `placeOrder`, look up the user before the insert and return 400 when it is missing. Add `db.pragma('foreign_keys = ON')` in `db.js`. Check: a test posts `userId: 999`, gets 400, the process stays up, and `orders` has no new row.
2. **Authentication.** Staff routes (`/orders/:id/ship`, `/admin/*`) use HTTP Basic auth over TLS. Whatever the staff upload the CSV with (a browser form, curl or a script), it can send Basic credentials, and a custom header would fail from a plain browser form. The order routes require a service key read from `API_KEY`. Per Q1, `GET /orders/:id` checks that the order belongs to the caller's user. Check: each route returns 401 without credentials and 200 with them. Compare credentials with `crypto.timingSafeEqual` so the comparison does not leak timing.
3. **Input checks.** `totalCents` must be a positive integer and `trackingCode` a non-empty string. `getOrder` and `markShipped` return 404 for a missing ID instead of an empty 200. Check: one route test per rule.
4. **Tests that go through HTTP.** Today's two tests call the service directly and replace the mailer with a stub. Add `test/routes.test.js`, which starts the app with `app.listen(0)` and calls it with the built-in `fetch`, so no new dependency is needed. Check: `npm test` passes.

**First steps** (none needs an answer):
- Get the build working: `npm install` on Node 20 or 22 LTS, since `better-sqlite3` failed to build here on Node 26. Then run `npm test` and record the count. It should be 2 passing.
- Reproduce the crash: `npm start`, then `curl -X POST localhost:3000/orders -H "content-type: application/json" -d "{\"userId\":999,\"totalCents\":100}"`. Confirm the process exits and that `SELECT * FROM orders WHERE user_id = 999` returns one row.
- Write the failing route tests from steps 1 to 3 in `test/routes.test.js` before changing `server.js`.
- Make the changes to `src/server.js`, `src/orders/orderService.js` and `src/db.js` from step 1.

### Phase 2: placing an order is safe to retry, and the e-mail goes out reliably

5. **Idempotent order creation.** Accept an `Idempotency-Key` header and store it in a new `orders.idempotency_key` column with a unique index. A repeat with the same key returns the first order. This covers a client that times out and retries, and two submits at the same moment. Check: two concurrent posts with the same key leave one row.
6. **Outbox.** `placeOrder` writes an `outbox` row in the same transaction as the order and returns. A worker in the same process sends pending rows, retries with backoff and marks them `sent` or `failed` after N attempts. N is a setting, initially 5, which is a guess. Check: with `SMTP_HOST` pointing at a closed port, the order still returns at once, and the row moves to `failed` after N attempts. `createTransport` sets no `auth` (`mailer.js:2`), and most providers require it, so check your provider's settings before launch. Fix the "recieve" typo in the README while you are there.
7. **Bulk import.** In `src/admin/bulkImport.js`, run the whole file in one `db.transaction`. A malformed line currently throws halfway through and leaves earlier lines applied. Validate every line first and reject the file listing the bad line numbers. Count `info.changes` instead of lines, and return the IDs that matched nothing. Set `updated_at` like `markShipped` does. Check: a file with one bad line changes no rows. Express's default text body limit is 100 kb as I remember it, so confirm it against a real end-of-day file.

### Phase 3: running it

8. **Backups.** Turn on WAL mode and run a nightly online backup with `db.backup()` (better-sqlite3's API as I recall it; confirm in its documentation) to storage off the machine. Check: restore last night's copy and run `SELECT COUNT(*) FROM orders`.
9. **Operations.** Read `PORT` from the environment, add a `/healthz` route, log one structured line per request without e-mail addresses, and run under a process manager that restarts on exit, with an alert on every restart.
10. **Rate limit on `POST /orders`.** Start in log-only mode for a week, then enforce. Staff routes are excluded because the warehouse probably shares one office address.

### Phase 4: launch

All of these must be true before real customers:
- Every route test passes, and an unauthenticated request to each route returns 401.
- The crash reproduction from phase 1 returns 400 and the process keeps running.
- A backup has been restored successfully at least once.
- The outbox shows no `failed` rows after a staging run of 50 orders.

Open to a small invited group first. Roll back or pause new orders if there is any process restart that has no known cause, any `failed` outbox row that has no known cause, or any order whose total differs from the storefront's.

## Found, not touched

- `marketing_opt_in` exists and nothing reads it. Check it before any marketing e-mail goes out.
- `express.text()` accepts any text body on every route, but only the import route needs it.
- `markShipped` can ship an order in any status. There is no cancellation status yet, so this is fine for now.
