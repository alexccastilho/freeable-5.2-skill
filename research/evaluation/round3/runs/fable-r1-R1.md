# shopmini: what to fix before customers see it

shopmini is not ready for customers yet, and the gaps are mostly ones a month can cover. It was built as an internal warehouse tool (the README says so), so it has no login, trusts whatever the caller sends, and one bad request can take the whole server down.

I read all of the code (about 115 lines, 7 source files, 1 test file). I did not run it: the repository has no installed dependencies and I was asked not to modify it, so the behaviours below come from reading the code and should be confirmed with a test as each one is fixed.

## What I found

**Blockers: anyone on the internet could abuse these on day one**

1. **There is no authentication or authorisation anywhere** (`src/server.js:6-9`). Any caller can:
   - place an order as any user by sending someone else's `userId`;
   - read any order by counting up ids (`GET /orders/1`, `/orders/2`, ...);
   - mark any order as shipped with any tracking code;
   - call the warehouse bulk import at `/admin/shipments/import`.
2. **The caller sets the price.** `POST /orders` takes `totalCents` straight from the request body (`server.js:6`, `orderService.js:6-8`). There are no products, line items or payment step, so an order for 1 cent, or a negative amount, is accepted.
3. **A single malformed request can crash the process.** The `POST /orders` handler is `async` with no error handling, and Express 4 does not catch rejected promises. An unknown or missing `userId` makes `placeOrder` throw (`mailer.js:11` reads `user.name` outside its `try`), which becomes an unhandled rejection; on current Node versions that exits the process. The order row may already have been written by then.
4. **No input validation.** `userId`, `totalCents`, `trackingCode` and the id in the URL are used as they arrive. A missing order returns `200` with an empty body instead of `404`.

**Serious: customers will notice these in the first weeks**

5. **Confirmation e-mails fail silently.** `mailer.js:12-13` logs and swallows every failure, with no retry and no record on the order. The SMTP transport has no credentials or timeout configured, and sending happens inside the request, so a slow mail server makes checkout slow and a broken one means customers get nothing, and you do not find out.
6. **The bulk import bypasses the order service** (`admin/bulkImport.js`):
   - it never updates `updated_at`;
   - it counts a row as "updated" even when the order id does not exist;
   - it does not run in a transaction, so a bad line halfway through leaves the file half applied;
   - it can mark an order shipped regardless of its current status.
7. **Customers are not told when their order ships.** Only the confirmation template exists.
8. **Retries create duplicate orders.** `POST /orders` has no idempotency key, so a flaky mobile connection can produce two orders.
9. **No operational basics:**
   - no request logging, error tracking or health check;
   - port 3000 is hard-coded;
   - the SQLite file is created in the working directory with no backup;
   - there is no rate limiting.

**Hygiene: cheap, and it protects everything above**

10. **Thin tests.** Two tests cover the service layer with the mailer stubbed; nothing tests the HTTP routes or the bulk import, and the second test depends on the first having run.
11. **No lockfile and no CI.** Dependency versions float (`express ^4.19.2`), so each install can pull different code.

## The plan, in order

**Week 1: close the open doors (items 1 to 4)**

- Add authentication, and tie every order read and write to the logged-in customer. Take `userId` from the session or token, never from the body.
- Put the ship and import endpoints behind a separate staff role, ideally not reachable from the public internet at all.
- Compute the total on the server. This is the largest piece, because it needs a decision on where prices come from (see question 2).
- Validate every input, return proper `400`/`404` responses, and add an error-handling wrapper so no request can crash the process.
- Add route-level tests for each of these as they are fixed, plus a lockfile and a CI job that runs them.

**Week 2: make orders and e-mail trustworthy (items 5 to 8)**

- Move e-mail out of the request: record each message as pending on the order, send from a small worker with retries, and alert on repeated failures. Configure SMTP credentials and timeouts.
- Route the bulk import through the order service, inside a transaction, and return a per-line report (updated, not found, invalid).
- Enforce status transitions (`placed` to `shipped` only once) and send a shipment e-mail.
- Accept an idempotency key on `POST /orders`.

**Week 3: be able to run it (item 9)**

- Structured logs, error tracking, a health endpoint, rate limiting, configuration through environment variables.
- Scheduled SQLite backups and one tested restore. SQLite is fine at this size if the service runs as a single instance; I would not migrate databases before launch.

**Week 4: rehearse**

- Deploy to a staging copy, run the full journey (place, confirm, ship, import) with real e-mail delivery, and try the abuse cases from the blocker list by hand.
- Hold back a few days of slack for what the rehearsal turns up.

## What I would leave for after launch

- Moving off SQLite.
- Refactoring the folder layout or converting to TypeScript.
- HTML e-mail templates and marketing e-mail (`marketing_opt_in` exists in the schema but nothing uses it).

## Questions I would ask

1. **What does "in front of real customers" mean in practice?** Customers calling this API from a website or app, or a separate storefront that calls shopmini on their behalf?
   *Default assumed:* customers reach `POST /orders` and `GET /orders/:id` over the internet through your own front end, and warehouse staff keep using the ship and import endpoints.
2. **Where do prices and payment live?** shopmini has no products or payment today.
   *Default assumed:* another system owns the catalogue and takes payment, and shopmini must verify the amount against it instead of trusting the caller. If shopmini itself must take payment, that is a second project and the month is at risk.
3. **How do customers log in today, if anywhere?** There is a `users` table but no way to create a user or sign in.
   *Default assumed:* an existing identity provider or front-end session can issue a token shopmini verifies; shopmini does not build its own password system.
4. **How many orders per day do you expect at launch?**
   *Default assumed:* tens to low hundreds, which a single instance on SQLite handles.
5. **Is the launch date fixed?**
   *Default assumed:* yes, so if time runs short the order of sacrifice is week 3 polish first, then shipment e-mails; the blockers in week 1 are not negotiable.
