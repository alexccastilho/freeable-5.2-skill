# Orders CSV export for the admin area

I read through shopmini. This is a small feature, but one thing should be settled before it ships, so I'll start there.

## The issue to settle first: `/admin` has no authentication

`src/server.js` mounts `/admin/shipments/import` with no auth middleware. Nothing in the app checks who is calling. The rest of the API is open as well (`GET /orders/:id`). The new export would join `orders` to `users`, so a plain `GET /admin/orders.csv` would let anyone who can reach port 3000 download every customer's name and email in one request. That's a much bigger exposure than the existing endpoints, which return one order at a time.

So I wouldn't ship the export as an open endpoint. I can see two options:

1. **Minimum:** add a small `requireAdmin` middleware (a shared token in the `ADMIN_TOKEN` env var, sent as `Authorization: Bearer ...`) and apply it to the whole `/admin` router. That covers the existing import endpoint too, which needs it just as much, because it can mark any order as shipped.
2. **If the app only runs on an internal network or behind a VPN/reverse proxy that already handles auth:** still add the middleware, since it costs almost nothing. But then this becomes defence in depth rather than a blocker.

## Questions I would ask

1. **Which columns do warehouse staff need?** The schema only has `id, user_id, status, total_cents, tracking_code, updated_at` on orders, plus `name, email` on users. There is no shipping address or line items. If they need those to pick and pack, that's a schema change and a bigger task.
   *Default:* `order_id, status, customer_name, customer_email, total (decimal, e.g. 12.50), tracking_code, updated_at`.
2. **Should they be able to filter it?** For example, only `placed` (not yet shipped) orders, or a date range.
   *Default:* optional `?status=` and `?since=`/`?until=` (ISO dates on `updated_at`). With no parameters you get all orders, newest first.
3. **How do they reach "the admin area"?** No admin UI exists. The repo is API-only, and today staff upload the shipments CSV with some client of their own.
   *Default:* a GET endpoint that returns a file download, so a bookmarked link or a button in whatever tool they use works. No UI is built in this repo.
4. **What auth is acceptable for now?** (see above)
   *Default:* bearer token from `ADMIN_TOKEN`. If it's unset, admin routes return 503 rather than staying open.
5. **Do they open it in Excel?**
   *Default:* yes. So the file gets a UTF-8 BOM (accented names display correctly), and cells that start with `= + - @` are neutralised to prevent CSV/formula injection from customer-controlled `name` values.

## Plan

### 1. `src/admin/auth.js` (new)

```js
const crypto = require('crypto');
function requireAdmin(req, res, next) {
  const expected = process.env.ADMIN_TOKEN;
  if (!expected) return res.status(503).json({ error: 'admin disabled: ADMIN_TOKEN not set' });
  const got = (req.get('authorization') || '').replace(/^Bearer /, '');
  const a = Buffer.from(got), b = Buffer.from(expected);
  if (a.length !== b.length || !crypto.timingSafeEqual(a, b)) return res.status(401).json({ error: 'unauthorized' });
  next();
}
module.exports = { requireAdmin };
```

### 2. `src/admin/ordersExport.js` (new)

This keeps the pattern of the other admin module: plain functions over `db`, with no dependency on Express.

```js
const db = require('../db');

const COLUMNS = ['order_id', 'status', 'customer_name', 'customer_email', 'total', 'tracking_code', 'updated_at'];

function csvCell(v) {
  if (v === null || v === undefined) return '';
  let s = String(v);
  if (/^[=+\-@\t\r]/.test(s)) s = "'" + s;            // formula-injection guard
  return /[",\r\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
}

function listOrdersForExport({ status, since, until } = {}) {
  const where = [], params = [];
  if (status) { where.push('o.status = ?'); params.push(status); }
  if (since)  { where.push('o.updated_at >= ?'); params.push(since); }
  if (until)  { where.push('o.updated_at < ?');  params.push(until); }
  const sql = `SELECT o.id AS order_id, o.status, u.name AS customer_name, u.email AS customer_email,
                      o.total_cents, o.tracking_code, o.updated_at
               FROM orders o LEFT JOIN users u ON u.id = o.user_id
               ${where.length ? 'WHERE ' + where.join(' AND ') : ''}
               ORDER BY o.updated_at DESC, o.id DESC`;
  return db.prepare(sql).iterate(...params);
}

function* ordersCsvLines(filters) {
  yield '﻿' + COLUMNS.join(',') + '\r\n';
  for (const r of listOrdersForExport(filters)) {
    const total = r.total_cents == null ? '' : (r.total_cents / 100).toFixed(2);
    yield [r.order_id, r.status, r.customer_name, r.customer_email, total, r.tracking_code, r.updated_at]
      .map(csvCell).join(',') + '\r\n';
  }
}

module.exports = { ordersCsvLines, csvCell, COLUMNS };
```

Notes:
- The code uses `iterate()` plus a generator, so the export streams instead of building the whole file in memory. That's fine at current size and still safe if the table grows.
- It uses `LEFT JOIN`, so an order whose user was deleted still appears, with empty name and email columns.
- All filters are bound parameters, so there's no SQL injection.
- Money is formatted from integer cents. No float arithmetic happens before display.

### 3. `src/server.js`: wire it up and protect `/admin`

```js
const { requireAdmin } = require('./admin/auth');
const { ordersCsvLines } = require('./admin/ordersExport');
const { Readable } = require('stream');

app.use('/admin', requireAdmin);   // must come before the admin routes, so it covers the existing import endpoint too

app.get('/admin/orders.csv', (req, res) => {
  const { status, since, until } = req.query;
  const stamp = new Date().toISOString().slice(0, 10);
  res.set('Content-Type', 'text/csv; charset=utf-8');
  res.set('Content-Disposition', `attachment; filename="orders-${stamp}.csv"`);
  res.set('Cache-Control', 'no-store');
  Readable.from(ordersCsvLines({ status, since, until })).pipe(res);
});
```

I'd use `clock.now()` rather than `new Date()` for the filename stamp, to stay consistent with the injectable clock.

I'd validate `since`/`until` as ISO dates and `status` against the known values (`placed`, `shipped`). Bad input gets a 400.

### 4. Tests: `test/adminExport.test.js` (new)

These follow the existing style (`node:test`, `DB_PATH=':memory:'`, stubbed mailer). I'd add `supertest` as a dev dependency for the HTTP-level tests. If you'd rather not add a dependency, I'd start the app on an ephemeral port and use `fetch` instead.

- Without a token you get 401. With `ADMIN_TOKEN` unset you get 503. The existing import endpoint is also rejected without a token, which is a regression guard for the new protection.
- With a token you get 200, `text/csv`, an attachment filename, a BOM and a header row.
- Rows contain the expected values, and `total_cents: 1050` becomes `10.50`.
- Escaping: a name with a comma or quote, and one starting with `=`, come out quoted or prefixed as expected.
- `?status=placed` returns only placed orders, and an invalid `since` returns 400.
- An order with a missing user still exports.

### 5. Docs

Add the endpoint, the `ADMIN_TOKEN` variable and an example `curl -H "Authorization: Bearer $ADMIN_TOKEN" -o orders.csv http://localhost:3000/admin/orders.csv` to the README. While I'm in there I'd fix the "recieve" typo.

## Rollout note

Adding auth to `/admin` will **break whatever currently calls `POST /admin/shipments/import`** until it sends the token. Before deploying, I'd set `ADMIN_TOKEN` in the environment and update the warehouse's upload script or tool. If that has to be staged, the alternative is to protect only the new export route first and add the import endpoint in a follow-up.

## Out of scope, but I noticed

- `bulkImport.js` doesn't set `updated_at` when it marks orders shipped, so exported `updated_at` values will be stale for orders shipped by import. `markShipped` does set it. If staff sort or filter the export by date, they'll see this, so it's probably worth a one-line fix alongside this work. Tell me if you want it included.
- `bulkImport.js` also crashes on blank or malformed lines (`tracking.trim()` on `undefined`), and it doesn't use a transaction.
