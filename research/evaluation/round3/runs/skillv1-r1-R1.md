shopmini was written as an internal warehouse tool, and it has no idea who is calling it. Putting it in front of customers is mainly an access-control job, not a polish pass: today anyone who can reach the server can read any order by counting up IDs, place an order for any user at any total they choose, mark orders shipped, and run the warehouse bulk import. That has to be fixed before launch, and it is most of the work. Second in line: one bad request can take the whole server down.

I read "next month" as December 2026. I read all ten files in the repository (`src/`, `test/`, `package.json`, `README.md`). I did not change anything and I did not run the code or the tests. The process crash in finding 2 below is from reading the code, so it is the first thing I would confirm by running it.

## What I found, in priority order

**Must fix before customers touch it**

1. **No authentication or authorisation on any route** (`src/server.js`).
   - `GET /orders/:id`: IDs are sequential integers, so anyone can walk through every order (user ID, total, tracking code).
   - `POST /orders`: `userId` and `totalCents` both come from the request body. A caller can order as someone else, at a price they choose, negative included. Each call also sends a confirmation e-mail to that user's address.
   - `POST /orders/:id/ship` and `POST /admin/shipments/import` are warehouse actions, open to the public.
2. **One request can kill the process.** `POST /orders` with an unknown `userId` inserts the order, then `templates.orderConfirmation` reads `user.name` on `undefined`. That throws outside the `try` in `mailer.send`. Express 4 does not catch rejections from `async` handlers, so it becomes an unhandled rejection, and current Node versions exit on those by default. The order row stays behind.
3. **No input validation anywhere.** `Number(req.params.id)` can be `NaN`. `totalCents` can be a string or negative. A missing order returns `200` with an empty body instead of `404`.
4. **The bulk import can half-apply** (`src/admin/bulkImport.js`). There is no transaction, so a line with no comma throws after earlier rows are already updated. It counts IDs that matched nothing as "updated", skips `updated_at`, and bypasses `markShipped`. A file sent as `text/csv` gets an empty body (only `text/plain` is parsed), so the call fails with a 500.
5. **The database path can silently point to a new, empty database.** `DB_PATH` falls back to the relative `shopmini.db`, and the schema is `CREATE TABLE IF NOT EXISTS`. Start the server from a different directory and it creates a fresh empty database and carries on.

**Fix before launch, but after the above**

6. **Confirmation e-mail is sent inside the request and failures are swallowed** (`src/notifications/mailer.js`). A slow SMTP server makes checkout slow. A failed send is logged once and lost, with no retry and no record. No SMTP credentials are configured, and most providers require them.
7. **No operational basics:** port 3000 is hard-coded, there is no health check, no request logging, no error handler (Express's default shows stack traces unless `NODE_ENV=production`), no rate limit, and no backup of the SQLite file.
8. **Tests cover two service functions and depend on each other** (the second test ships the order the first one created). There are no route tests, so none of the problems above would show up as a failing test. There is no lockfile, and `better-sqlite3` is a native module, so installs are not reproducible.

## Questions I would ask

1. **How will customers reach this: directly from a browser or app, or only through a storefront backend you control?** Default: directly, so every route is treated as public. If only a trusted backend calls it, phase 1 shrinks to one service credential plus a network restriction, and per-customer ownership checks move into that backend.
2. **Where should order totals come from?** There is no product or price table. Default: customers cannot set `totalCents`. Order creation is accepted only from a trusted caller (staff or the storefront backend) until prices are computed on the server. If customers must create orders directly, a product/price table becomes launch-blocking work of its own.
3. **Is there an existing login system (storefront accounts, an identity provider) the API should trust?** Default: none, so the plan uses signed tokens issued by whatever logs customers in, plus a separate staff credential. If there is one, the API verifies its tokens and nothing new is built.
4. **Where will it run, and how many instances?** Default: one instance behind an HTTPS reverse proxy, so SQLite stays. If you need more than one instance, SQLite has to be replaced before launch, and that becomes the largest phase.
5. **Which privacy law applies to your customers (LGPD, GDPR)?** Default: one does, so the plan includes a backup policy, access logs for staff actions, and deletion on request. `marketing_opt_in` is stored but never used today.

Answer first: 1 and 2. They decide whether phase 1 is a day of gateway work or the core of the launch, and whether a pricing model is needed before December.

## Plan

The order is deliberate. Validation, e-mail and operations are worth little while anyone can mark an order shipped, so access control comes first.

**Phase 0: make changes safe to ship (small, first).** Commit a lockfile. Add route-level tests using the existing `node:test` runner. Make each test create its own data. Require `DB_PATH` to be set and absolute in production, and refuse to start otherwise. Take a backup of the current database and restore it once to prove the backup works.
*Check:* `npm test` passes from a clean `npm ci`. Starting without `DB_PATH` in production fails loudly.

**Phase 1: access control (the bulk of the work).**
- Split routes into customer routes (`POST /orders`, `GET /orders/:id`) and staff routes (`/orders/:id/ship`, `/admin/*`).
- Customer routes: identity comes from the verified credential, never from the body. `GET /orders/:id` returns 404 unless the order belongs to the caller. Use 404 rather than 403 so the response does not confirm the order exists.
- Staff routes: a separate staff credential. If possible, also restrict them to the warehouse network at the proxy.
- `totalCents`: follows question 2's default.
*Check:* tests prove that customer A gets 404 on customer B's order, that a customer token gets 401/403 on both staff routes, and that a request with no credential gets 401 everywhere.

**Phase 2: stop bad input from crashing or corrupting.**
- Validate every body and parameter. Return 400 or 404 instead of `undefined`.
- Wrap async handlers (or move to Express 5, which forwards rejections) and add one error handler that logs the error and returns a generic 500.
- Look up the user before inserting the order, and do both inside one transaction.
- Bulk import: parse and validate the whole file first, then apply it in one transaction through the same code as `markShipped`. Return `{updated, skipped: [{line, reason}]}`. Accept `text/csv`.
*Check:* tests for an unknown user, a non-numeric ID, a malformed CSV line (nothing applied, line reported) and an ID that does not exist (reported as skipped). The process is still up after each one.

**Phase 3: reliable confirmation e-mail.** Write an `outbox` row in the same transaction as the order. A small worker in the same process sends from the outbox with retries and backoff. Configure SMTP credentials and require TLS. Alert when any message stays unsent past a set age. The age is a setting; start it at a value you would notice within a working day.
*Check:* with SMTP pointed at a dead host, placing an order returns quickly and the message is sent once SMTP comes back.

**Phase 4: run it in production.** Read the port from `PORT`. Add a health check that touches the database. Add structured request logs with no personal data in them. Put HTTPS at the proxy, with Express `trust proxy` set to match the real setup and exposed as a setting; log `req.ip` once in the deployed environment to confirm it. Rate-limit the customer routes in log-only mode first, because the numbers are guesses, then enforce. Schedule SQLite backups using its online backup API (better-sqlite3 has `db.backup()`; check this against the installed version) and turn on WAL mode.
*Check:* one restore from a scheduled backup into a scratch environment.

## Go / no-go for opening to customers

All of these must be true:
- Every route returns 401 without a credential, and the cross-customer and staff-route tests from phase 1 pass in CI.
- An automated sweep of `GET /orders/1..N` with one customer's token returns only that customer's orders.
- None of the phase 2 malformed-input tests crashes the process.
- A backup taken on the production host has been restored successfully at least once.
- Confirmation e-mails sent through the outbox were all delivered in a staging run against the real SMTP provider.

**Revert rule after launch:** if the error rate on customer routes, or the count of unsent outbox messages, goes above what staging showed during the first days, close customer access at the proxy. Staff routes keep working, so the warehouse is not affected.

## Found, not touched

- `README.md` says "recieve". Typo.
- `marketing_opt_in` is stored but nothing reads or sets it. If marketing e-mail is planned, consent capture needs its own work.
- Customers are not told when an order ships. Neither ship path sends anything.
- `markShipped` does not check the current status, so it can "ship" a cancelled or already-shipped order.
- `express.text()` is mounted on every route. It is only needed for the import.

## Need from you

- Answers to questions 1 and 2.
- How the storefront or app will call this API, if one exists.
- The intended hosting target and the SMTP provider, so phase 3 and phase 4 settings can be filled in.
