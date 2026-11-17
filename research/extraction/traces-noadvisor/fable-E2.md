# Rate limiting for the shopmini API

I have not changed anything yet: the repository is read-only for me here, so nothing below has been applied or run. This is the exact change I would make, and it is small enough to review in one pass.

One thing to settle before it goes live: the API has no authentication, so the only thing I can limit by is the client IP address. If your legitimate traffic arrives from one address (a storefront server placing orders for customers, or the whole warehouse behind one office connection), a per-IP limit throttles all of it together. The limits below are set loosely for that reason, and there is a log-only switch so you can watch a day of real traffic before enforcing.

## What the change does

- **Every route:** 300 requests per minute per IP.
- **`POST /orders`:** 20 per minute per IP. This is the expensive route: each call writes a row and sends a confirmation e-mail inside the request, so a bot here also spams your SMTP provider.
- **`POST /admin/shipments/import`:** 10 per minute per IP. It is an end-of-day CSV upload, so it needs very little.
- **Over the limit:** the client gets HTTP 429 with a JSON body and the standard `RateLimit` headers.
- **Placement:** the limiter runs before the body parsers, so rejected requests are not parsed.

All three numbers are environment variables. They are my guesses, since I have no traffic data.

## The change

`package.json`: add the dependency.

```diff
-  "dependencies": { "express": "^4.19.2", "nodemailer": "^6.9.13", "better-sqlite3": "^11.0.0" }
+  "dependencies": { "express": "^4.19.2", "express-rate-limit": "^7.4.0", "nodemailer": "^6.9.13", "better-sqlite3": "^11.0.0" }
```

New file `src/rateLimit.js`:

```js
const { rateLimit } = require('express-rate-limit');

const num = (name, fallback) => Number(process.env[name]) || fallback;
const enforce = process.env.RATE_LIMIT_ENFORCE !== 'false';

function limiter(name, perMinute) {
  return rateLimit({
    windowMs: 60_000,
    limit: perMinute,
    standardHeaders: 'draft-7',
    legacyHeaders: false,
    handler: (req, res, next) => {
      console.warn(`rate limit hit: ${name} ip=${req.ip} ${req.method} ${req.path}`);
      if (!enforce) return next();
      res.status(429).json({ error: 'rate_limited', message: 'Too many requests, try again shortly.' });
    },
  });
}

module.exports = {
  general: limiter('general', num('RATE_LIMIT_GENERAL', 300)),
  orders: limiter('orders', num('RATE_LIMIT_ORDERS', 20)),
  adminImport: limiter('adminImport', num('RATE_LIMIT_ADMIN_IMPORT', 10)),
};
```

`src/server.js`:

```diff
 const { importShipments } = require('./admin/bulkImport');
+const limits = require('./rateLimit');
 const app = express();
+if (process.env.TRUST_PROXY) app.set('trust proxy', Number(process.env.TRUST_PROXY));
+app.use(limits.general);
 app.use(express.json()); app.use(express.text());
-app.post('/orders', async (req, res) => res.json(await orders.placeOrder(req.body.userId, req.body.totalCents)));
+app.post('/orders', limits.orders, async (req, res) => res.json(await orders.placeOrder(req.body.userId, req.body.totalCents)));
 app.get('/orders/:id', (req, res) => res.json(orders.getOrder(Number(req.params.id))));
 app.post('/orders/:id/ship', (req, res) => res.json(orders.markShipped(Number(req.params.id), req.body.trackingCode)));
-app.post('/admin/shipments/import', (req, res) => res.json({ updated: importShipments(req.body) }));
+app.post('/admin/shipments/import', limits.adminImport, (req, res) => res.json({ updated: importShipments(req.body) }));
```

New file `test/rateLimit.test.js` (the existing tests call the service directly, so they are unaffected):

```js
const test = require('node:test');
const assert = require('node:assert');
process.env.DB_PATH = ':memory:';
process.env.RATE_LIMIT_GENERAL = '3';
const app = require('../src/server');

test('requests over the limit get 429', async () => {
  const server = app.listen(0);
  const url = `http://127.0.0.1:${server.address().port}/orders/1`;
  try {
    for (let i = 0; i < 3; i++) assert.equal((await fetch(url)).status, 200);
    const blocked = await fetch(url);
    assert.equal(blocked.status, 429);
    assert.equal((await blocked.json()).error, 'rate_limited');
  } finally { server.close(); }
});
```

I would also add a short "Rate limits" section to the README listing the four environment variables.

## Two deployment settings that decide whether this works

- **Proxy:** if the API sits behind a load balancer or reverse proxy, Express sees the proxy's address for every request, and everyone shares one bucket. Set `TRUST_PROXY=1` (the number of proxies in front) so the real client IP is used. If the API is exposed directly, leave it unset; setting it there would let a bot fake its address with a header.
- **Process count:** the counters live in memory, per process. That is correct for a single Node process, which is what `npm start` and the local SQLite file suggest. With several instances each one counts separately, and the store would need to move to Redis.

## What this does not fix

- **A bot that rotates IP addresses** gets a fresh budget on each one. Per-IP limiting stops a single noisy client, not a distributed one.
- **The admin import and ship routes are open to anyone who can reach the server.** Rate limiting slows abuse of them but does not prevent it. Authentication is the real fix and would also give a better key to limit by. I left it out because it is a larger change than you asked for; say if you want it.

## Questions I would ask

1. **Which routes did the bot hit, and from how many addresses?** Default assumed: one or a few addresses hammering `POST /orders` or `GET /orders/:id`, which this change covers.
2. **Where do legitimate requests come from?** Default assumed: several distinct client addresses, none needing more than 20 orders a minute. If a storefront server places all orders from one IP, raise `RATE_LIMIT_ORDERS` or start with `RATE_LIMIT_ENFORCE=false` and read the warnings for a day.
3. **Is there a proxy or load balancer in front, and how many app instances run?** Default assumed: one instance, exposed directly, so `TRUST_PROXY` stays unset and the in-memory store is enough.
4. **Is a new dependency acceptable?** Default assumed: yes. `express-rate-limit` is the standard Express middleware for this; a hand-written limiter of about 30 lines is the alternative if you would rather not add one.

## Process log

1. Ran `find` and `ls -la` on the fixture root to list its files.
2. Ran one command that printed, with `cat -n`: `package.json`, `README.md`, `src/server.js`, `src/db.js`, `src/clock.js`, `src/admin/bulkImport.js`, `src/orders/orderService.js`, `src/users/userService.js`, `src/notifications/mailer.js`, `test/orders.test.js`; the same command ran `ls -a` on the fixture root and `ls` on the output folder.
3. Wrote this file.
