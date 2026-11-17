# shopmini: launch-readiness review and what to fix first

I read the whole repo (it's small: about 115 lines across `server.js`, the order, user, mail and admin modules, plus one test file). I didn't change anything and didn't run it, because there's no `node_modules` and installing would have modified the repo. Every finding below comes from reading the code. The two crash and data bugs I'd confirm with a quick test before fixing them.

## The headline

**shopmini isn't safe to put in front of customers yet, and the biggest problem isn't a bug.** The README calls it a "small order-management API used by our warehouse team", and the code matches that: it assumes every caller is trusted. Nothing checks who is calling. The client chooses the price. Back-office endpoints sit on the same open server as everything else. Opening it to the public changes what it's for, so step one is a short decision about what customers will actually reach. Then come the fixes.

## Questions I would ask

1. **What exactly will customers touch?** Will they call this API directly (from a mobile app or a browser storefront), or will it sit behind a storefront or backend you own that calls it server-to-server?
   *Default:* customers' devices reach it, directly or through a thin frontend. So treat every endpoint as public.
2. **Where do prices come from?** No product or price table exists. `POST /orders` stores whatever `totalCents` the caller sends. Is there a catalogue or payment step somewhere else?
   *Default:* no. Payment is taken elsewhere (for example a PSP checkout), and shopmini must not trust a client-sent total.
3. **How do customers log in today, if at all?**
   *Default:* there's no customer auth yet, and we need some (accounts or signed per-order links).
4. **Expected volume and hosting?** SQLite is fine for one instance at modest traffic. It isn't fine for several instances or serverless.
   *Default:* one instance with a persistent disk, low hundreds of orders a day.
5. **Which jurisdictions?** The `users` table holds emails and a `marketing_opt_in` flag, so LGPD or GDPR obligations apply.
   *Default:* Brazil (LGPD), possibly the EU.

## Findings, ranked

### P0: blocks launch

**1. No authentication or authorization on any route** (`src/server.js:6-9`)
- `GET /orders/:id` returns any order to anyone. IDs are sequential integers, so the whole order table can be listed by counting up (an IDOR).
- `POST /orders` accepts any `userId`, so anyone can place orders as any customer.
- `POST /orders/:id/ship` lets anyone mark any order shipped, with any tracking code.
- `POST /admin/shipments/import` is a public endpoint that bulk-rewrites order status. It's the most dangerous route in the app.

Fix: put admin routes behind staff auth, or better, off the public listener entirely (a separate port, VPN, or internal network). Make `/ship` staff-only. Customers should only read and create their own orders. The user should come from the session or token, never from `req.body.userId`.

**2. The client sets the order total** (`src/server.js:6`, `orderService.js:6-8`)
`totalCents` comes straight from the request body with no validation. Negative, zero, fractional or absurd values are all stored. If anything downstream bills or fulfils from this number, it's a direct price-tampering hole. Fix: compute the total on the server from line items and a price source, or take it only from a verified payment event. Answer question 2 first, because it decides which.

**3. One request can crash the whole server** (`orderService.js:10`, `mailer.js:11`)
If you post an order for a `userId` that doesn't exist, `getUser` returns `undefined`. `templates.orderConfirmation` then reads `user.name`. That line sits *outside* the `try`, so `send()` rejects. Express 4 doesn't catch rejected promises from async handlers, so this becomes an unhandled rejection, and on current Node that ends the process. A single bad (or malicious) request takes the API down. The order row is also already inserted. SQLite doesn't enforce the `REFERENCES users(id)` foreign key unless `PRAGMA foreign_keys = ON` is set, so the bad order stays in the table.
Fix: validate input, enable foreign keys, add an async error wrapper and a global error handler, and run under a supervisor that restarts on crash.

**4. Order confirmation email is sent inline, and failures are hidden** (`mailer.js:9-14`)
- Each `POST /orders` waits for an SMTP round-trip. A slow or down mail server becomes slow or failing checkout.
- Failures go to `console.error` and are dropped. Customers silently get no confirmation, and nobody can see which ones were missed or resend them.
- The transport has no auth and no TLS settings. If `SMTP_HOST` isn't set, it quietly falls back to localhost.

Fix: write an "email to send" record in the same transaction as the order (an outbox) and send it from a background worker with retries. Alert on failures. Configure SMTP credentials and TLS, or use a transactional email provider.

### P1: fix before or right after launch

**5. Bulk shipment import is fragile and bypasses the business rules** (`src/admin/bulkImport.js`)
- A malformed line (blank line, missing comma) throws on `tracking.trim()`. There's no transaction, so the rows before it are already updated, the response is a 500, and nobody knows how far it got.
- `Number(orderId)` can be `NaN`, and the counter `n` goes up even when no row matched. The `updated` count it reports is therefore not reliable.
- It writes SQL directly instead of going through `markShipped`. It never sets `updated_at`, and it will "ship" orders in any state, including cancelled ones.
- `express.text()` only parses `text/plain`. Upload with a CSV content type and `req.body` is `{}`, so `.trim` throws.

Fix: parse with a real CSV parser, validate every row, run it in one transaction, report counts and per-row errors (`updated`, `not_found`, `invalid`), and route each change through the same shipping logic as `/ship`.

**6. Orders have no state machine and no protection against duplicates**
- `markShipped` works on any order, any number of times, and on IDs that don't exist (it returns an empty 200).
- A retried `POST /orders` (double click, mobile retry) creates duplicate orders. Add an idempotency key.
- Customers are never told their order shipped. Only the confirmation template exists.

**7. Basic production hygiene is missing**
- No input validation or response codes. A missing order returns `200` with an empty body instead of `404`.
- No request size limit decision, no rate limiting, no `helmet` or CORS policy.
- The port is hard-coded to 3000. There's no health endpoint, no graceful shutdown, and no structured logging, metrics or error tracking.
- SQLite runs with defaults. Turn on WAL mode and a busy timeout, and keep the DB file on persistent storage with **automated backups you have actually test-restored**. Today one lost disk means losing every order.

### P2: important, but not ahead of the above

**8. Test coverage is thin.** There are two tests and the mailer is mocked out. No test covers HTTP routes, bulk import, bad input, unknown users, or the crash path. The second test relies on the order the first test created. Add route-level tests (for example with `supertest`) for each P0 and P1 fix as you make it, starting with a regression test for finding 3.

**9. Privacy and compliance.** There's no endpoint or process to export or delete a customer's data. `marketing_opt_in` exists but nothing records when or how consent was given. You'll want a privacy notice and a data retention rule before collecting real customer data.

**10. Small things.** Dependencies use `^` ranges and there's no lockfile in the repo. Commit one and add `npm audit` to CI. There's also a README typo ("recieve").

## Plan: what to do first

**Week 1: decide and close the open doors**
1. Answer questions 1 to 3 in a 30-minute meeting. Write down the trust boundary: what's public, what's staff-only, and where prices come from.
2. Move `/admin/*` and `/orders/:id/ship` behind staff auth, or off the public network. This is quick and removes the worst exposure.
3. Fix the crash (finding 3): an async error handler, input validation on `POST /orders`, foreign keys on, and a regression test.

**Week 2: make orders trustworthy**
4. Customer authentication: only the logged-in customer can create and read their orders. Also stop exposing sequential IDs in public URLs, or always check ownership (both is better).
5. Server-side pricing, or totals taken from verified payment data (finding 2).
6. Idempotency key on order creation, and a simple order state machine (`placed → paid → shipped`, plus `cancelled`).

**Week 3: reliability and operations**
7. Email outbox with a background worker and retries, real SMTP config, and a shipping notification.
8. Rewrite the bulk import (finding 5), going through the state machine.
9. Production setup: env-based config, health check, structured logs and error tracking, rate limiting, SQLite WAL, and tested backups.

**Before go-live**
10. Route-level test suite in CI. A load test at about 3x expected traffic, so we know whether SQLite and the single instance hold up. A short external security review or pentest of the public endpoints. The privacy basics (finding 9).

If the launch date can't move, the minimum for a safe launch is items 1 to 5 plus backups. Everything else can follow in the first weeks after launch, as long as you watch it closely.

I can start on any of these. The admin lockdown and the crash fix are the quickest big wins, and I'd begin there.
