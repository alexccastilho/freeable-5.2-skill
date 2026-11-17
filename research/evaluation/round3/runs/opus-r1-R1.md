# shopmini: pre-launch review and priority plan

I read the whole repo: `package.json`, `README.md`, the files under `src/`, and `test/orders.test.js`. It's about 115 lines. I didn't install dependencies or run the tests, because I was told not to touch the repo. Everything below comes from reading the code.

## The headline

The README describes shopmini as a "small order-management API used by our warehouse team". The code matches that description: it assumes every caller is a trusted employee on the inside. It has no authentication, it trusts whatever the client sends (including the price), and the admin endpoints sit on the same open app as everything else. That's survivable on an internal network. It can't go in front of customers like this. Most of the work below is about closing that gap, not polishing code.

## Questions I would ask

1. **What does "in front of customers" mean here?** Will customers call this API (from a storefront or app), or will they only see its effects (confirmation e-mails, a tracking page)?
   *Default: a customer-facing storefront will call `POST /orders` and `GET /orders/:id`, and `/admin/*` and `/orders/:id/ship` stay for warehouse staff.*
2. **Where does the order total come from today?** Is there a product catalogue or price list anywhere, or does the caller just send `totalCents`?
   *Default: nothing exists server-side, so we need at least a minimal price lookup.*
3. **Who takes payment, and when?** Is it a payment provider, or invoicing outside this system?
   *Default: payment happens outside shopmini for now, and shopmini only records orders. If shopmini will take payment, that becomes its own workstream, and pricing (P0-2) gets even more urgent.*
4. **Where will it run?** One instance, or several? Is there a managed database, and are there backups?
   *Default: one Node process with the SQLite file on persistent disk. That's fine at launch volume if we add backups.*
5. **Which country and which privacy law?** The schema stores e-mail and a `marketing_opt_in` flag.
   *Default: LGPD/GDPR-style obligations apply.*
6. **What's the launch volume and the go-live date?**
   *Default: low hundreds of orders a day, about 4 weeks to launch.*

## What I found, ranked by risk

### Critical: must fix before any customer touches it

1. **No authentication or authorization on any route** (`src/server.js`).
   - `GET /orders/:id` uses sequential integer IDs, so anyone can walk `/orders/1`, `/orders/2`, … and read every order: totals, status, tracking codes, user IDs.
   - `POST /orders/:id/ship` and `POST /admin/shipments/import` are open to the internet. Anyone could mark any order as shipped with a fake tracking code.
   - `POST /orders` takes `userId` from the request body, so a caller can place orders as any user.
2. **The client sets the price.** `POST /orders` stores `req.body.totalCents` as is. A customer can send `1`, or a negative number. There's no validation of any field.
3. **A bad request can crash the whole server.** If `userId` doesn't exist, `getUser` returns `undefined`. Then `templates.orderConfirmation` reads `user.name`. That line (`mailer.js:11`) is **outside** the `try`, so it throws inside an async route handler. Express 4 doesn't catch rejected promises, so this becomes an unhandled rejection, and current Node versions **terminate the process** on those. The order row has already been inserted by then. So one malformed request leaves an orphan order and takes the API down for everyone.

### High: will cause incidents or angry customers in the first weeks

4. **Confirmation e-mails can silently not go out.** `mailer.send` is awaited inside the order request, so a slow SMTP server makes checkout slow. Failures are only `console.error`'d, with no retry and no record that the e-mail never went. The README promises customers a confirmation e-mail. Once real customers are involved, the first "I never got my confirmation" ticket will have nothing to check. The SMTP transport also has no auth or TLS settings, so most real providers will reject it.
5. **The bulk shipment import is fragile and bypasses the rules** (`src/admin/bulkImport.js`).
   - A blank line in the middle of the file or a line without a comma makes `tracking.trim()` throw halfway through. There's no transaction, so you're left with a **partial import**, and nobody knows which rows were applied.
   - It counts every line as "updated", even when the order ID doesn't exist (`stmt.run(...).changes` is ignored), so the number the warehouse sees can be wrong.
   - It doesn't set `updated_at` (unlike `markShipped`), and it overwrites any status, including orders that should never ship.
6. **No order-state rules.** `markShipped` and the import will "ship" any order regardless of its current status. Unknown IDs return `200` with an empty body instead of `404` (`res.json(undefined)`).
7. **No error handling, logging, or health check.** There's no Express error middleware, no request logging, and no `/health` route. The port is hard-coded to `3000`. On launch day you'd be debugging blind.

### Medium: fix soon after launch, or before if time allows

8. **Data and operations.** The SQLite file defaults to `shopmini.db` in whatever directory the process starts from. The schema is created inline with no migrations. There are no backups. The `orders` table has no index on `user_id` and no `created_at` column; `updated_at` gets overwritten, so you lose when the order was placed.
9. **Privacy.** `marketing_opt_in` exists but nothing reads it. That's fine today, but make sure transactional e-mails stay transactional, and decide how customers can see or delete their data.
10. **Tests are thin and order-dependent.** There are two tests. The second only passes because the first created order #1. The mailer is stubbed, so the crash in #3 and the swallowed failures in #4 are never exercised. Nothing tests over HTTP, and nothing tests the import.
11. **Hygiene.** There's no lockfile, no `engines` field, no rate limiting, and no security headers. `express.text()` is enabled for every route. The README has a typo ("recieve").

## The plan, in order

I've sequenced the work so each phase removes the largest remaining risk, and so you could stop after Phase 1 and still be safer than today.

### Phase 0: safety net (1–2 days)
- Add a lockfile and an `engines` field, and confirm `npm test` passes as is.
- Add HTTP-level tests with `supertest` or Node's `fetch` against `app`. **First, write failing tests that reproduce the critical bugs:** unknown `userId` crashes the process, someone else's order is readable, the client sets the total, a malformed CSV leaves a partial import.
- Make the tests independent of each other (fresh in-memory DB per test, or explicit fixtures).

### Phase 1: launch blockers (about week 1)
1. **Split the surfaces.** Put `/admin/*` and `/orders/:id/ship` behind staff authentication (simplest: a separate router with an API key or SSO, ideally only reachable on the internal network). Put customer routes behind customer authentication. Derive `userId` from the session or token, never from the body.
2. **Ownership checks.** `GET /orders/:id` returns only the caller's own orders, and `404` otherwise. Consider non-guessable public order references (UUIDs or random tokens) for anything shown in URLs or e-mails.
3. **Server-side pricing and input validation.** Compute the total from line items and a server-side price table. Validate every body with a schema (zod, joi, or similar). Reject zero, negative, and non-integer amounts.
4. **Stop the crash.** Add an async error wrapper (or move to Express 5, which forwards rejected promises) plus a central error handler that returns JSON `4xx`/`5xx`. Check that the user exists before inserting the order.

### Phase 2: reliability of the customer promise (about week 2)
5. **Reliable e-mail.** Write the order row and an "outbox" row in the same transaction, and send from a background worker with retries. Record sent/failed status so support can answer "did my e-mail go out?". Configure SMTP auth and TLS from environment variables. Consider a transactional e-mail provider.
6. **Fix the bulk import.** Parse with a real CSV parser, run inside `db.transaction`, validate every row first, and return a per-row report (applied / unknown ID / invalid / wrong state). Route it through the same `markShipped` logic so `updated_at` and the state rules apply. If customers should get a "your order shipped" e-mail, this is where it gets triggered.
7. **Order state machine.** Allowed transitions only (`placed → shipped`, plus whatever cancel or refund states you need). Return `404` for unknown IDs and `409` for invalid transitions.

### Phase 3: operate it (about week 3)
8. Structured logging with request IDs, a `/health` route, configurable `PORT`, and graceful shutdown.
9. Error monitoring (Sentry or similar) and an alert on 5xx rate and e-mail failure rate.
10. Database: proper migrations, a `created_at` column, an index on `orders.user_id`, the DB path set explicitly in config, and **automated backups with a tested restore**.
11. Rate limiting on public routes, `helmet`, HTTPS at the proxy, and request-size limits.

### Phase 4: before go-live (week 4)
- An end-to-end rehearsal on a staging copy: place an order, get the e-mail, import shipments, check the customer view.
- A short runbook: how to restart, restore a backup, and resend a failed e-mail.
- Privacy items: a retention policy, honouring `marketing_opt_in` before any marketing e-mail exists, and a process for data-deletion requests.

## What I'd do first, concretely

If you only have this week: **#1 auth and splitting the admin routes, #2 server-side pricing, and #3 the crash fix, each with a test that reproduces the problem first.** Those three are the difference between "has bugs" and "anyone on the internet can read every order, ship anything, set their own price, or knock the service over with one request".

Once you've confirmed the defaults above (especially what "in front of customers" means and where prices come from), I can turn Phase 0 and Phase 1 into concrete tickets or start on the failing tests.
