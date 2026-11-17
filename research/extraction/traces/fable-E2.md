# Rate limiting for the shopmini API

I have not changed anything yet. Below is the change I propose, with the code, and two questions whose answers could make a per-IP limit harmful if I guess wrong. The code has not been run.

## What I found in the repository

- `src/server.js` defines four routes and no middleware other than body parsing. There is no rate limiting, no authentication, and no `trust proxy` setting.
- Because there is no authentication, the client IP address is the only thing a limit can be keyed on. `userId` arrives in the request body and can be set to anything by the caller.
- `POST /orders` is the expensive route. Each call inserts a row and then waits for an SMTP send before responding (`src/orders/orderService.js` line 10, `src/notifications/mailer.js`). A bot hitting it creates junk orders and sends e-mail from your domain.
- The app is a single process with a local SQLite file, so an in-memory counter is sufficient. There is no deployment configuration in the repository, so I cannot see whether a proxy or load balancer sits in front.
- `package.json` has no rate limiting library and there is no lockfile.
- The existing tests call the service functions directly and never go through HTTP.

## Questions I would ask

1. **Is there a reverse proxy, load balancer, or CDN in front of the app?** This matters more than anything else here. Behind a proxy, and without `trust proxy` set, Express sees every request as coming from the proxy's address. A per-IP limit would then put all users in one bucket and block everyone as soon as traffic is normal. Default: the app is reached directly, with no proxy. The setting is exposed as `TRUST_PROXY` so it can be corrected without a code change.
2. **Who calls `POST /orders`: end customers directly, or a storefront backend on one address?** If it is one backend, a strict per-IP limit on that route throttles all customers at once. Default: callers have their own addresses.
3. **Which route did the bot hit, at what rate, and from how many addresses?** Default: `POST /orders`, from a small number of addresses. If it rotated across many addresses, a per-IP limit will slow it only slightly, and the real fix is authentication on the API.
4. **Do the warehouse staff share one office IP address?** Default: yes. For that reason I have not put a strict limit on the shipping and import routes, and the general limit is set high.
5. **What is normal peak traffic?** I have no traffic data, so the numbers below are guesses. Default: 300 requests per minute per address overall, and 20 orders per minute per address. Both are environment variables.

## Proposed change

Two limits, both per IP address, both counted in memory:

| Scope | Default | Reason |
|---|---|---|
| Every route | 300 per minute | Stops a flood on any route, loose enough for a shared office address |
| `POST /orders` | 20 per minute | The route that writes a row and sends an e-mail |

A blocked request gets status 429 with a `Retry-After` header and a JSON body.

I would use the `express-rate-limit` package rather than write the counter by hand. It is the standard middleware for Express, it handles expiry of old entries and the response headers, and the alternative is about forty lines of our own code to maintain for no gain.

### `package.json`

Add `"express-rate-limit": "^7"` to `dependencies`.

### `src/server.js`

```js
const express = require('express');
const { rateLimit } = require('express-rate-limit');
const orders = require('./orders/orderService');
const { importShipments } = require('./admin/bulkImport');
const app = express();

// Set TRUST_PROXY to the number of proxies in front of the app (for example 1).
// Leave it unset when clients connect directly.
if (process.env.TRUST_PROXY) app.set('trust proxy', Number(process.env.TRUST_PROXY));

const perMinute = (envName, fallback) => rateLimit({
  windowMs: 60 * 1000,
  limit: Number(process.env[envName] || fallback),
  standardHeaders: 'draft-7',
  legacyHeaders: false,
  message: { error: 'rate_limited' },
});

app.use(perMinute('RATE_LIMIT_PER_MIN', 300));   // before body parsing, so blocked requests are cheap
app.use(express.json()); app.use(express.text());
app.post('/orders', perMinute('RATE_LIMIT_ORDERS_PER_MIN', 20), async (req, res) => res.json(await orders.placeOrder(req.body.userId, req.body.totalCents)));
app.get('/orders/:id', (req, res) => res.json(orders.getOrder(Number(req.params.id))));
app.post('/orders/:id/ship', (req, res) => res.json(orders.markShipped(Number(req.params.id), req.body.trackingCode)));
app.post('/admin/shipments/import', (req, res) => res.json({ updated: importShipments(req.body) }));
if (require.main === module) app.listen(3000);
module.exports = app;
```

The option names (`limit`, `standardHeaders: 'draft-7'`, `legacyHeaders`) are from version 7 of the library as I remember it. I would check them against the installed version's documentation before committing, since older versions used `max` instead of `limit`.

### `test/rateLimit.test.js` (new)

The existing tests do not use HTTP, so this needs its own file. `node --test` runs each file in a separate process, so the low limits set here do not affect `orders.test.js`. No new test dependency is needed: the test starts the exported app on a free port and uses the built-in `fetch`.

```js
const test = require('node:test');
const assert = require('node:assert');
process.env.DB_PATH = ':memory:';
process.env.RATE_LIMIT_PER_MIN = '5';
process.env.RATE_LIMIT_ORDERS_PER_MIN = '2';
const mailer = require('../src/notifications/mailer');
mailer.send = async () => {};
const db = require('../src/db');
const app = require('../src/server');
db.prepare("INSERT INTO users (id, email, name) VALUES (1, 'a@example.com', 'Ana')").run();

test('rate limits', async (t) => {
  const server = app.listen(0);
  t.after(() => server.close());
  const base = `http://127.0.0.1:${server.address().port}`;
  const post = () => fetch(`${base}/orders`, {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ userId: 1, totalCents: 100 }),
  });

  assert.equal((await post()).status, 200);
  assert.equal((await post()).status, 200);
  const blocked = await post();                       // third order in the window
  assert.equal(blocked.status, 429);
  assert.ok(blocked.headers.get('retry-after'));
  assert.equal(db.prepare('SELECT COUNT(*) AS n FROM orders').get().n, 2);  // blocked call wrote nothing

  assert.equal((await fetch(`${base}/orders/1`)).status, 200);   // 4th request overall
  assert.equal((await fetch(`${base}/orders/1`)).status, 200);   // 5th
  assert.equal((await fetch(`${base}/orders/1`)).status, 429);   // 6th, over the general limit
});
```

The count in the last three lines depends on the blocked order request still counting toward the general limit, which is how I expect the middleware order to behave. That is the first thing I would confirm when running it.

### `README.md`

Add a short section listing `RATE_LIMIT_PER_MIN`, `RATE_LIMIT_ORDERS_PER_MIN`, and `TRUST_PROXY`, with the warning from question 1.

## How I would verify it

1. `npm install`, then `npm test`: the two existing tests and the new one pass.
2. Start the server locally and send 25 order requests in a loop: the first 20 return 200, the rest return 429, and the `orders` table has 20 new rows.
3. Before production: log `req.ip` for one real request in the deployed environment. If it shows a proxy address instead of the client's, set `TRUST_PROXY` before enabling the limits. This check is what prevents the limit from blocking everyone.

## Limits of this change

- **Counters are in memory.** They reset on restart and are not shared between processes. That is correct for one process. If the app ever runs as several instances, the limiter needs a shared store such as Redis.
- **A bot that rotates addresses gets through.** Per-IP limiting handles a crude flood and nothing more.
- **The API has no authentication, including `/admin/shipments/import`.** Anyone who can reach the server can place orders and mark them shipped. Rate limiting reduces the volume of abuse but does not prevent it. I have not touched this, but it is the larger exposure and worth its own piece of work.
- **The confirmation e-mail is sent inside the request.** Up to 20 e-mails per minute per address can still be triggered. Lowering `RATE_LIMIT_ORDERS_PER_MIN` is the lever if that is too many.

## Process log

1. Ran one shell command in the shopmini fixture: `find` to list files, `wc -c` for file sizes, and `ls` of the traces output folder. This was a single exploration pass done before starting any of the four tasks.
2. Ran one shell command in the shopmini fixture: `cat -n` over `package.json`, `README.md`, `src/server.js`, `src/db.js`, `src/clock.js`, `src/admin/bulkImport.js`, `src/notifications/mailer.js`, `src/orders/orderService.js`, `src/users/userService.js`, `test/orders.test.js`; then `ls -la` of the fixture root and `ls` of the traces output folder.
3. Called the advisor tool once.
4. Wrote this file with the Write tool. No command was run against the proposed code, and nothing in the fixture was modified or installed.
