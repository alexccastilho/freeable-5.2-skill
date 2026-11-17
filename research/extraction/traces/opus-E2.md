# E2: Rate limiting for the shopmini API

I read through shopmini (`src/server.js`, the services, `db.js`, the mailer and the test) before planning, because some of what's in there changes what "add rate limiting" should mean.

## What I found that matters

1. **There's no authentication anywhere.** `server.js` exposes `POST /orders`, `GET /orders/:id`, `POST /orders/:id/ship` and `POST /admin/shipments/import` to anyone who can reach port 3000. So rate limits can only key on client IP; there's no user or API key to key on.
2. **`/admin/shipments/import` is wide open.** Anyone can mark any order shipped with any tracking code, in bulk. Rate limiting doesn't fix that: one request with a 10,000-line CSV does all the damage. If the bot found this endpoint, this is a bigger problem than request volume.
3. **`POST /orders` sends an e-mail on every call, inline in the request** (`orderService.placeOrder` → `mailer.send`, awaited). A bot hammering this endpoint creates junk orders, sends SMTP traffic to whatever addresses are attached to the `userId`s it guesses, and holds requests open while SMTP is slow. That puts your sender reputation at risk too. It also takes any `userId`/`totalCents` without validation.
4. **`GET /orders/:id` uses sequential integer ids and has no auth**, so a bot can enumerate every order. Rate limiting slows that down but doesn't stop it.
5. **No `trust proxy` setting.** If shopmini runs behind nginx, a load balancer or Cloudflare, `req.ip` is the proxy's address. A naive per-IP limiter would then throttle *everyone* as one client. I need to know the deployment to get this right.
6. **It's a single process using SQLite** (`better-sqlite3`, `app.listen(3000)`). An in-memory limiter store is correct as long as there's one instance; it would be wrong with several.
7. **`express.json()` / `express.text()` use default body limits (100kb).** That's fine, but the CSV import may need a larger, explicit limit, and other routes should stay small.

## Questions I would ask

1. **What did the bot actually hit?** Which endpoints, and was it one IP or many? (Access logs from last week.) Default: **assume `POST /orders` and order-id enumeration from a small number of IPs.** If it was a distributed botnet, per-IP limits help little, and the real answer is an edge WAF/bot protection (Cloudflare, AWS WAF) in front of the app.
2. **How is it deployed: directly exposed, or behind a reverse proxy/LB? How many hops? One instance or several?** Default: **one instance behind one reverse proxy**, so `app.set('trust proxy', 1)` and an in-memory store.
3. **Who are the legitimate callers?** The README says "used by our warehouse team". Are customers calling `POST /orders` directly, or is it called from a storefront backend? If everything goes through one backend or one office IP, per-IP limits could throttle real traffic. Default: **warehouse staff from a few office IPs plus a storefront calling `POST /orders`**, so the office/storefront IPs get an allowlist or higher limits.
4. **Can I add authentication to `/admin/*` in the same change, or should that be separate?** Default: **I'll propose it as a separate, urgent follow-up and not slip it in unasked.** I'll flag it prominently because it's the bigger hole.
5. **Is adding a dependency (`express-rate-limit`) OK?** Default: **yes.** It's the standard, maintained Express middleware, and writing your own limiter isn't worth it.

## Plan

### Step 1: Limiter middleware (the change you asked for)

New file `src/middleware/rateLimit.js`, using `express-rate-limit` (add it to `package.json`):

- **Global baseline:** 300 requests / 5 min per IP on all routes.
- **`POST /orders`: tight.** 10 / 15 min per IP. This is the expensive route (DB write + SMTP).
- **`GET /orders/:id`:** 60 / min per IP, to slow enumeration.
- **`/admin/*`:** 20 / 15 min per IP, plus an explicit body limit on the import route (`express.text({ limit: '2mb' })`).
- Responses: `429` with JSON `{ error: 'Too many requests' }`, `standardHeaders: 'draft-7'` (`RateLimit-*` + `Retry-After`), `legacyHeaders: false`.
- Log each limit hit (IP, route) so we can see whether it's working and tune the numbers.
- Limits are read from env vars (`RATE_LIMIT_ORDERS_MAX` etc.) with the defaults above, so ops can loosen them without a deploy.
- Optional `RATE_LIMIT_ALLOWLIST` (comma-separated IPs) for the warehouse/storefront IPs.

The limits above are starting guesses. I'll check them against real traffic before they go live (see Rollout).

### Step 2: Wire it into `server.js` correctly

- `app.set('trust proxy', <hops from env, default 1>)` **before** the limiters. The test plan below checks this, since getting it wrong makes the limiter either useless (bot spoofs `X-Forwarded-For`) or harmful (everyone shares one bucket).
- Mount the global limiter first, then the per-route limiters on their routes.
- Keep `module.exports = app` unchanged so the tests keep working.

### Step 3: Tests (`test/rateLimit.test.js`, `node --test`)

There's no HTTP-level test today, so I'd add `supertest` as a dev dependency, or use `app.listen(0)` + `fetch`:

- N allowed requests then a 429 on `POST /orders`, with `Retry-After` present.
- Separate IPs get separate buckets (via `X-Forwarded-For` with trust proxy set).
- An allowlisted IP is never limited.
- `GET /orders/:id` and `POST /orders` buckets are independent.
- The existing `orders.test.js` still passes. Mailer is stubbed, `DB_PATH=:memory:`.
- Limiters need to be created by a factory (`createApp(config)` or similar) so tests can use tiny limits and don't share state. That's a small refactor of `server.js`.

### Step 4: Rollout

1. Deploy first in **log-only mode** (`skip` returns true but logs would-be-limited requests) for a day or two. Compare against normal warehouse traffic so we don't lock out the warehouse at end-of-day import time.
2. Tune the numbers, then enforce.
3. Watch the 429 counts and SMTP send volume afterwards.

### Step 5: Follow-ups I'd strongly recommend (not part of this change unless you say so)

- **Authenticate `/admin/*`** (even a shared API key from env checked by middleware is a big improvement), and validate the CSV in `bulkImport.js`. It currently crashes on a malformed line and skips `updated_at`.
- **Make the order confirmation e-mail async** (queue/outbox) so `POST /orders` doesn't wait on SMTP, and validate `userId` exists and `totalCents` is a positive integer.
- **Authorization on `GET /orders/:id`**, or non-sequential public ids, to stop enumeration properly.
- **If the bot was distributed:** put an edge WAF/bot rule in front. App-level per-IP limits won't hold against many IPs.
- **If you ever scale to more than one instance:** move the limiter store to Redis (`rate-limit-redis`).

## Files I'd touch

- `package.json`: add `express-rate-limit`; add `supertest` (dev)
- `src/middleware/rateLimit.js`: new
- `src/server.js`: `trust proxy`, mount limiters, route-specific body limit, app factory
- `test/rateLimit.test.js`: new
- `README.md`: document the env vars

I haven't changed any code yet. Once you answer the deployment question (proxy or no proxy, how many instances), I'll implement steps 1–3.

## Process log

1. `find . -type f` (excluding node_modules/.git) in the shopmini fixture, to list files.
2. Read with `cat`: `package.json`, `README.md`, `src/server.js`, `src/db.js`, `src/clock.js`, `src/users/userService.js`, `src/orders/orderService.js`, `src/admin/bulkImport.js`, `src/notifications/mailer.js`, `test/orders.test.js`; ran `ls -la` and `git log --oneline -5` (not a git repository).
3. `ls` on the traces output directory.
4. Wrote this file.
