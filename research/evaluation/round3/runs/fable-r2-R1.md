# shopmini: what to fix before customers arrive

shopmini is not ready for customers as it stands. It was built as an internal warehouse tool and has no access control at all, and one malformed request can take the whole server down. Both are fixable well inside a month; the plan below puts them first.

I read every file in the repository (about 115 lines: seven source files and one test file). I could not run it: `better-sqlite3` failed to build on the Node version on this machine (v26), so the findings come from reading the code, not from exercising it. I changed nothing in the repository.

## What I found, in order of how much it would hurt

**1. Anyone who can reach the server can do anything** (`src/server.js`)

There is no login, API key or role check on any route. With the API reachable from the internet, a stranger could:

- read any order by counting up through ids (`GET /orders/1`, `/orders/2`, ...);
- mark any order as shipped with a made-up tracking code (`POST /orders/:id/ship`);
- overwrite tracking for many orders at once through the warehouse import (`POST /admin/shipments/import`);
- place orders for any `userId`, with any total.

**2. One bad request can crash the server** (`src/server.js:6`, `src/orders/orderService.js`)

`POST /orders` is an async handler with no error handling. If `placeOrder` throws, Express 4 does not catch it and Node exits on the unhandled rejection. It throws for an unknown or missing `userId`: the user lookup returns nothing and the e-mail template then reads `user.name`. That takes the service down for everyone until something restarts it, and I saw no process manager in the repository.

**3. The order total is whatever the caller sends** (`src/orders/orderService.js:6`)

`totalCents` is stored unchecked: negative, zero, fractional or text values all go in. There are no order lines, products or prices in the schema, so the server cannot recompute a total. How serious this is depends on who calls the API (see the first question).

**4. Confirmation e-mails can fail without anyone knowing** (`src/notifications/mailer.js`)

- Failures are logged to the console and dropped, with no retry and no record on the order.
- The e-mail is sent inside the order request, so a slow SMTP server makes placing an order slow. A client that times out and retries creates a duplicate order, because nothing de-duplicates requests.
- The SMTP connection has no credentials, and the sender is `orders@shopmini.example`, a placeholder domain that real mailboxes will reject or mark as spam.

**5. The warehouse import can leave data half-updated** (`src/admin/bulkImport.js`)

- It runs without a transaction, so a malformed line (for example, one with no comma) stops the import with the earlier lines already applied.
- It reports the number of lines read, not the number of orders actually changed, so a typo in an order id looks like a success.
- It skips the order service: `updated_at` is not set, and it will "ship" an order in any state.
- It always drops the first line as a header, so a file without one silently loses its first shipment.
- It only accepts a `text/plain` body within Express's default size limit (100 kB), so a real CSV upload, or a large peak-season file, would fail.

**6. Missing or wrong ids return success** (`src/server.js:7-8`)

A lookup or ship request for an order that does not exist returns a 200 with an empty body. Other errors return Express's default page, which includes a stack trace unless `NODE_ENV=production` is set.

**7. Nothing tells you when it breaks**

- The data is a single SQLite file in the working directory, with no backup or migration mechanism in the repository.
- There are no request logs, no health check, and no error reporting.
- The port is hard-coded to 3000.
- There are two tests, both at service level; the HTTP routes and the import are untested.
- There is no lockfile, so installs are not reproducible.

## The plan

| Order | Work | Done when |
|---|---|---|
| 1 | Add authentication to every route, with separate permissions for customers (their own orders only) and warehouse staff (ship, import). Until that ships, keep the service off the public internet. | A test proves a customer cannot read or change another customer's order, and an unauthenticated call to each route gets a 401. |
| 2 | Add request validation and a central error handler; wrap the async route. Return 404 for unknown orders and 400 for bad input. | A test posts junk to every route and the process stays up, with no stack trace in the response. |
| 3 | Make order placement safe: validate the total (or compute it server-side, depending on the answer to question 1) and accept an idempotency key so a retry does not create a second order. | Posting the same order twice with the same key yields one order. |
| 4 | Move e-mail out of the request: record a pending notification with the order, send it from a worker with retries, and mark the outcome. Configure real SMTP credentials and a sender on a domain you own, with SPF and DKIM set up. | Placing an order with SMTP down still succeeds, and the e-mail goes out once SMTP is back. |
| 5 | Rework the import: route it through the order service, run it in one transaction, validate each line, and return a per-line report of what changed and what was rejected. | A file with one bad line changes nothing and names the line. |
| 6 | Operations: scheduled backups of the database with a tested restore, structured logs, a health endpoint, error alerts, a process manager, config from environment, a committed lockfile and a pinned Node version. | You have restored a backup once and been paged by a test error once. |
| 7 | A rehearsal before launch: run the full customer journey and a warehouse end-of-day import against a staging copy. | The rehearsal passes without manual fixes. |

Items 1 and 2 are the launch blockers; I would not expose the service without them. Items 3 to 5 protect money, customer trust and warehouse data, and fit in the following two weeks. Item 6 can run alongside from the start, since it is mostly setup. That leaves the last week for the rehearsal and whatever it turns up.

I would leave these alone for now: moving off SQLite (it is adequate for one server at modest volume, provided it is backed up), restructuring the code, and the unused `marketing_opt_in` column and `getUserByEmail` function.

## Questions I would ask

1. **What will customers actually touch?** Will a storefront or app call this API directly, or does another system you control sit in front of it?
   Assumed default: a customer-facing front end calls this API over the internet, so the caller cannot be trusted. If a trusted backend sits in front, item 3 shrinks and item 1 becomes service-to-service authentication plus network restriction.
2. **Where do users and payment live?** The repository has no way to create a user and no payment step.
   Assumed default: both are handled by another system, and shopmini only records the order after payment.
3. **How many orders a day do you expect, and on what hosting?**
   Assumed default: a single server and at most a few thousand orders a day, which SQLite handles.
4. **Should customers be told when their order ships?** Today only the confirmation e-mail exists.
   Assumed default: not required for launch; it becomes cheap to add once item 4 is done.
