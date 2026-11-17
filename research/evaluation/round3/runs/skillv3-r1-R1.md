shopmini today is what its README says it is, "a small order-management API used by our warehouse team" (`README.md:3`), not a customer-facing shop. None of its four routes checks who is calling, the order total is whatever the caller sends, and one bad order request can stop the whole process. So what comes first is not features or polish. It is a trust boundary: staff routes behind a credential, customer traffic arriving only through a caller you control, and a server that survives bad input. My default is the cheapest safe shape: shopmini stays behind your storefront or app server, which logs customers in and calls shopmini with a service key. If customers' browsers or apps will call shopmini directly, Q1 selects the larger branch at the end of Phase 1. I read "next month" as December 2026. I have not run anything: dependencies are not installed and I did not modify the repository, so everything below comes from reading the code. The claim most likely to be wrong is the foreign-key behaviour in the fourth finding.

## What I found that changes the request

- No route has authentication or authorisation, and the only middleware is body parsing (`src/server.js:5-9`) -> anyone who can reach port 3000 can mark any order shipped (`POST /orders/:id/ship`) or overwrite tracking codes in bulk (`POST /admin/shipments/import`).
- `userId` and `totalCents` are read from the request body (`src/server.js:6`), and the schema has no product or price table (`src/db.js:4-5`) -> a caller can order as any user at any price, and the server has nothing to check the price against.
- Order IDs are sequential integers, and `GET /orders/:id` returns the whole row to anyone (`src/server.js:7`) -> anyone can read every customer's order, total and tracking code just by counting up.
- `POST /orders` has an async handler, and Express 4 does not catch rejected promises (`src/server.js:6`) -> any throw inside `placeOrder` becomes an unhandled rejection, and on Node 15 and later that ends the process. One way to trigger it is an unknown `userId`: `getUser` returns undefined, and the template reads `user.name` (`src/notifications/mailer.js:6`), which runs before the `try` on line 12. If foreign keys are off, the order row is already inserted by then, so a client retry creates a duplicate. I do not remember whether better-sqlite3 turns foreign keys on by default. `node -e "console.log(require('better-sqlite3')(':memory:').pragma('foreign_keys'))"` settles it.
- The confirmation e-mail is awaited inside the request, and failures are only logged (`src/orders/orderService.js:10`, `src/notifications/mailer.js:9-13`) -> a slow mail server slows every checkout, and a failed send leaves the customer with no confirmation and no record to retry from. The mail transport has no credentials configured (`mailer.js:2`).
- The bulk import updates row by row, with no transaction and no line validation (`src/admin/bulkImport.js:7-10`) -> a short or blank line throws at `tracking.trim()` after the earlier rows are already updated. The returned count also includes IDs that do not exist, and the import never sets `updated_at`, which `markShipped` does set (`orderService.js:15`).
- Tables are created with `CREATE TABLE IF NOT EXISTS` (`src/db.js:3-6`) -> editing that statement will not change a database that already exists, so every new column below needs an explicit migration.
- Users are only ever read; nothing creates them (`src/users/userService.js`) -> customer accounts have to come from somewhere else (Q1).

## Questions I would ask

Q1. How will customers reach shopmini: through a storefront or app server you run, or directly from browsers and mobile apps? And what will they do: place orders, check status, or only receive e-mails? - Default: a storefront server calls shopmini with a service key, and customers place orders and check status through that storefront. If customers call shopmini directly, it needs its own customer accounts and login, ownership checks on every order read, server-side pricing and rate limits. That is several weeks of work and puts the December date at risk (branch below).
Q2. Where do prices and payment come from? - Default: the storefront calculates the total and takes payment before it calls `POST /orders`, and shopmini only records the order. If shopmini should own prices, it needs a products table, order line items and a payment-provider integration, which is a project of its own.
Q3. What order volume do you expect at launch and at peak, and do you need more than one server instance? - Default: one instance, with SQLite kept. If you need several instances, the mail sender in step 7 has to claim rows before sending, and SQLite gives way to Postgres.
Q4. How do warehouse staff call the ship and import routes today: a browser form, curl, a script, or another system? - Default: an unknown mix. Step 2 uses a credential every one of those clients can send, and starts in a logging stage that reveals callers nobody listed.
Q5. Where does shopmini run today (host, TLS, backups), and who will do this work? - Default: one server, no TLS in the app, no backups. Step 5 covers all three.

Answer first: Q1 and Q2. They decide whether the December date holds.

## Plan

### Phase 1 - Safe to expose (blocks launch)

1. **Survive bad input.** In `src/server.js`, wrap the async handler with `const wrap = fn => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);` and add a final error middleware that logs the error and returns a 500 JSON body. On `POST /orders`, return 400 unless `userId` is an existing user and `totalCents` is a positive integer. When `getOrder` finds nothing, return 404 (today it returns 200 with an empty body). Check: post `{"userId":999,"totalCents":100}` and get a 400, the next request still succeeds, and `SELECT COUNT(*) FROM orders` has not changed.
2. **Staff credential on `/orders/:id/ship` and `/admin/*`.** HTTP Basic auth, with credentials from an environment variable, compared using `crypto.timingSafeEqual`. I chose Basic auth because of how the routes are used: browsers prompt for it on their own, and curl or scripts send it with `-u`. A custom header would break a browser form. Rollout: set `STAFF_AUTH_MODE=log` for two working days, so calls without credentials are logged with their path and source address instead of blocked. That catches callers nobody listed, such as a cron job or someone's script. Switch to `enforce` once two end-of-day imports have run with zero unexplained callers. Revert rule: if the end-of-day import fails after enforcement, set the variable back to `log` (no deploy needed), and find the caller from the log.
3. **Service key on customer routes.** `POST /orders` and `GET /orders/:id` require `Authorization: Bearer <SERVICE_KEY>` and reject every other caller with 401. The customer's browser never sees the key: the storefront server sends it, along with the logged-in customer's ID. `GET` also takes that ID and returns 404 unless it matches `order.user_id`, so a storefront bug cannot show one customer another customer's order. With Q2's default, the total is trusted only because it arrives with the service key.
4. **Keep secrets out of the repository.** `SERVICE_KEY`, the staff credentials and the SMTP credentials live only in the host's environment. Check: a search of the repository for the key values returns nothing.
5. **Run it like a production service.** Terminate TLS in front of the app (Basic auth over plain HTTP exposes the password), read the port from `PORT`, and back up the SQLite file nightly with better-sqlite3's `db.backup()` (from memory; confirm the method name against the installed version). Restore one backup to a scratch path and compare `SELECT COUNT(*) FROM orders` with production. The restore must succeed before launch.

**If Q1 is "direct access":** add customer sign-up and login (sessions or tokens), an ownership check on every order read, a products table with server-side totals, CORS limited to your domains, and a per-address limit on `POST /orders`. This is the largest single cost in this response, and it pushes launch past December unless it starts now.

**First steps (need no answers):**
- Run the foreign-key check command above and record the result.
- Edit `src/server.js`: add `wrap`, the error middleware, the input checks and the 404 (step 1).
- Add a test to `test/orders.test.js` that posts an unknown `userId` through `app` and asserts a 400 and an unchanged order count. Then run `npm install && npm test` in a working copy.
- Add the Basic-auth middleware in log mode to the two staff routes in `src/server.js` (step 2), and deploy it.
- Copy the production `shopmini.db`, then restore that copy once to prove the backup path (step 5).

### Phase 2 - Orders that are never lost or doubled

6. **Migration.** In `src/db.js`, migrations run at startup, guarded by `PRAGMA user_version`. The first adds `orders.confirmation_sent_at` and a unique `orders.idempotency_key`. Take a backup first, and check that the row count matches after the migration.
7. **Move the confirmation out of the request.** `placeOrder` inserts the order and returns. A loop in the same process runs every 30 seconds, sends confirmations for orders where `confirmation_sent_at IS NULL`, and sets the column on success. A failed send is retried on the next pass and logged loudly after five failures, so an SMTP outage delays mail without blocking orders. A crash between sending and updating can produce one duplicate e-mail, which I accept. This design is correct only for a single process (Q3). Call `transport.verify()` at startup so a mail misconfiguration fails visibly. Send from a real domain with SPF and DKIM set up, because `orders@shopmini.example` (`mailer.js:12`) will be rejected or land in spam. Check: point `SMTP_HOST` at a closed port, place an order, and it returns quickly with the row unsent; restore the host and the e-mail arrives within a minute.
8. **Idempotent order creation.** The storefront sends one `Idempotency-Key` per checkout. If the insert hits a key that already exists, shopmini returns the existing order. Check: the same key posted twice leaves one row.
9. **Safe bulk import.** In `bulkImport.js`, validate every line first: two fields, a numeric ID that exists, a non-empty tracking code, `\r` stripped. If any line fails, reject the whole file with the failing line numbers. Otherwise, apply the updates inside `db.transaction`, set `updated_at`, and return `{ updated, unknownIds }`. Uploading the same file twice is harmless. Check: a file with a bad line 3 gets a 400 that names line 3, and no rows change.

### Phase 3 - Launch gate

All of these must be true before customer traffic:
- `npm test` passes, with tests for each step above, and each test sets up its own order instead of relying on the previous test's.
- A request with no credentials to each of the four routes, sent from outside your network, returns 401.
- Staff auth has been enforced through at least two clean end-of-day imports.
- Last night's backup restored successfully.
- One storefront test order produces exactly one row and one e-mail within two minutes.

After launch: if more than 1% of `POST /orders` calls return a 5xx error in the first day, pause checkout on the storefront and read the error log before reopening.

## Found, not touched

- `marketing_opt_in` exists but nothing reads it; check consent before any marketing mail.
- There is no shipping-notification e-mail; customers will ask where their order is.
- `express.text()` and `express.json()` apply to every route, and a JSON body sent to the import crashes it at `csvText.trim` (step 9's validation covers this).
- The README says "recieve".
