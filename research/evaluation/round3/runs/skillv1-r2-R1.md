shopmini was built as an internal warehouse API: there is no idea of who is calling it anywhere. Opening it to customers means the most important work is giving it identity and permissions, and moving the price calculation to the server. Today anyone who can reach the server can place an order for any user at any price they choose, read every order by counting up IDs, mark orders as shipped, and run the admin import. Code quality and email reliability come second. "Next month" I take to mean December 2026. That leaves room for the must-fix list below, but not for much more.

**A cheaper path, if it fits the goal.** If what customers actually need is to see their order status and tracking (they already get the confirmation e-mail), you don't have to open the whole API. You can add one read-only endpoint, `GET /track/:token`, keyed by a random token that goes in the e-mail, and keep everything else on the internal network. That is a few days of work instead of the multi-week plan below, and it is the right choice if placing orders happens in some other system (a storefront or a sales channel) that calls shopmini from the server side. I plan what you asked below: customers using shopmini directly.

**Not seen / not run:** I read the whole repository (6 source files and 1 test file) but did not run anything, because installing dependencies would have changed the folder. I have not seen your hosting, any storefront, or a payment flow. None of those appear in the code.

## What I found (by severity)

**Blocks launch: security and money**
1. **No authentication on any route** (`src/server.js`). `POST /orders`, `GET /orders/:id`, `POST /orders/:id/ship` and `POST /admin/shipments/import` are all open.
2. **The client sets the price.** `placeOrder(req.body.userId, req.body.totalCents)` stores whatever total the caller sends, and there is no product or price table anywhere.
3. **The client chooses who it is.** `userId` comes from the request body, so anyone can place an order as someone else and have the confirmation e-mail sent to that person.
4. **Orders can be listed by anyone.** `GET /orders/:id` with sequential integer IDs returns any order, including `user_id`, total and tracking code. The sequential IDs also show how many orders you take.
5. **Anyone can mark orders shipped**, through either `/orders/:id/ship` or the CSV import.

**Blocks launch: correctness**
6. **An order for a missing user leaves an orphan order and a hung request.** SQLite does not enforce foreign keys unless `PRAGMA foreign_keys = ON`, so the insert succeeds. Then `templates.orderConfirmation` reads `user.name` on `undefined` *outside* the `try` in `mailer.send`, so `placeOrder` rejects. Express 4 does not catch rejected async handlers, so the client never gets a response and the order row stays behind.
7. **No validation and no error responses.** `Number('abc')` gives `NaN`, and a missing order returns an empty `200`. Any thrown error becomes a hang (async) or an HTML stack trace (sync).
8. **The bulk import can half-apply.** A blank line or a line without a comma throws on `tracking.trim()` partway through, after earlier rows are already committed, because there is no transaction. It also counts IDs that don't exist as "updated" and never sets `updated_at`.
9. **Shipping ignores the current state.** `markShipped` will "ship" an order that doesn't exist, or ship one twice and overwrite its tracking code.

**Hurts customers soon after launch**
10. **E-mail failures are silent, and sending blocks the order request** (`mailer.js`). If SMTP is slow, checkout is slow. If SMTP fails, the customer gets nothing, there is no retry, and nobody notices beyond a console line. The transport has no auth or TLS settings, and `from` is hard-coded.
11. **No operations basics:** port 3000 is hard-coded, and there is no HTTPS, health check, structured logging, rate limiting or backups. The SQLite file sits in the working directory by default (`DB_PATH || 'shopmini.db'`).
12. **The tests cover two happy paths**, and the second test depends on the first having run.

## Questions I would ask

Q1. Do customers need to place orders through shopmini, or only check order status? - Default: they place and view orders, as asked. If status only, take the tracking-token path above and skip phases 2 and 3.

Q2. How do customers reach it: their browser or app calling shopmini directly, or your own storefront backend calling it server to server? - Default: directly, over the internet. If server to server, customer login moves to the storefront and shopmini needs only service-to-service authentication (an API key or mTLS) plus network restriction. Phase 1 shrinks to a few days.

Q3. Where do prices and payment come from? - Default: shopmini gets a minimal `products` table (id, name, price_cents, active), and orders carry line items whose total the server computes. Payment is out of scope, and orders are created only after the payment provider confirms. If payment is handled by a provider such as Stripe, the order total is checked against the provider's confirmed amount, not just computed.

Q4. Do customer accounts already exist somewhere (there is no sign-up code here)? - Default: your existing login system issues a signed token (JWT or session) that shopmini verifies, with the `sub` matched to `users.email`. If no login system exists, I add e-mail magic-link login, which is roughly one more week and a new e-mail template.

Q5. Where will it run, and as how many instances? - Default: one instance on a persistent disk behind a reverse proxy that terminates HTTPS, with SQLite kept. If you need several instances or serverless hosting, SQLite has to be replaced by Postgres, and that becomes the largest item in the plan.

Answer first: Q2, Q3 and Q4. Together they decide whether phase 1 takes days or weeks and whether a product table exists. The plan below works without the answers.

## Plan

**Phase 0: Keep it off the internet until the launch gate passes (now).** Bind the server to localhost or the private network only. The warehouse keeps using it as today. Check: from outside the network, `curl` to the host's port 3000 fails.

**Phase 1: Identity and permissions (largest phase, roughly half the effort).**
- Add an auth middleware that verifies the customer token (Q4 default) and sets `req.user`. Remove `userId` from the request body: `placeOrder` uses `req.user.id`.
- `GET /orders/:id` returns the order only if `order.user_id === req.user.id`, and otherwise returns `404` (not `403`, so it doesn't confirm the order exists). Add a public order reference (a random string) so customers never see the sequential integer ID.
- Move `/orders/:id/ship` and `/admin/*` behind staff authentication, kept separate from customer tokens. If they stay internal-only, also block them at the proxy.
- Check: a test per route proving that customer A cannot read, create for, or ship anything belonging to customer B, and that no route answers without a token.

**Phase 2: Server-side pricing (after phase 1, because it changes the same request shape).**
- Add a `products` table. `POST /orders` accepts `[{productId, qty}]` and the server computes `total_cents`, rejecting inactive products and quantities that are not positive integers.
- Check: a test that sends a forged `totalCents` and shows it is ignored.

**Phase 3: Correctness.**
- Run `PRAGMA foreign_keys = ON` in `db.js`. Use an async error wrapper and a final error handler that returns JSON `400`/`404`/`500` with no stack traces. Validate inputs (IDs, tracking codes).
- `placeOrder`: look up the user first, and do the insert inside a transaction.
- `importShipments`: validate every line before writing anything, run the whole import in one `db.transaction`, set `updated_at`, and return `{updated, unknownIds, badLines}`. `markShipped`: allowed only from `placed`, otherwise `409`.
- Check: tests for a missing user, a missing order, a malformed CSV (nothing written), a double ship, and a non-numeric ID.

**Phase 4: E-mail off the request path.**
- Add an `outbox` table written in the same transaction as the order, and a worker loop that sends with retries and marks rows `sent` or `failed`. Configure SMTP user, password and TLS, and the `from` address, through environment variables.
- Check: with SMTP pointed at a dead host, an order still returns in normal time, the outbox row shows `failed` with attempts counted, and it sends once SMTP is back.
- Order reason: the outbox comes after phase 3 because it relies on the transaction handling added there.

**Phase 5: Operations.**
- Read `PORT` from the environment. Put a reverse proxy in front for HTTPS. Add `GET /health`, JSON request logs (no e-mails or tokens in the logs), and a rate limit on `POST /orders` and the login endpoint, started in log-only mode for a few days because the limits are guesses. Turn on SQLite WAL mode and take scheduled backups using SQLite's online backup to off-host storage, then **restore one backup and confirm the order count matches**.
- Check: monitoring alerts on 5xx rate, on outbox `failed` rows, and on a backup older than its schedule.

**Phase 6: Soft launch.** Open to a small group of customers first (a list of invited accounts), then everyone.

## Go / no-go before customers get access

All of these must be true:
- Every route returns `401` without a token, and the cross-customer tests from phase 1 pass.
- A forged `totalCents` has no effect (test passes).
- A backup has been restored and its order count matched.
- Outbox failures alert someone, and the alert has fired at least once in testing.
- An end-to-end order by a real test customer on the production setup works: order created, e-mail received, warehouse ships it, status visible.

**During the soft launch:** go back to invite-only if the 5xx rate goes above your pre-launch baseline, if any outbox row stays `failed` for more than an hour, or if one order total differs from its line items.

## Found, not touched

- `marketing_opt_in` is stored but never used. Before any marketing e-mail goes out, consent capture and the privacy notice (LGPD/GDPR, depending on where customers are) need doing.
- `getUserByEmail` is unused.
- `express.text()` is applied globally only so the CSV import works. Scope it to the import route.
- README: "recieve" should be "receive", and it still describes the app as warehouse-only.
- `test/orders.test.js` mocks `mailer.send` by reassigning it, which won't cover the outbox worker. The tests will need restructuring in phase 4.

## Need from you

- Answers to Q2, Q3 and Q4, or a pointer to the storefront or login system if they exist.
- The hosting target, and whether the warehouse reaches shopmini over a private network or the internet.
- Who on your side owns the SMTP account and can create credentials and a sending domain record (SPF/DKIM).
