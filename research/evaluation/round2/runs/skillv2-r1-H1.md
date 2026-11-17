This is a small change: one new route, `GET /admin/orders.csv`, in a new `src/admin/ordersExport.js` next to the existing import, plus a test. The part that needs care is not the CSV. The admin routes in shopmini have no authentication at all (`/admin/shipments/import` is open to anyone who can reach port 3000), and an export would hand the full order list, with customer names, to the same audience. So the new route requires a token from an `ADMIN_TOKEN` setting and refuses to serve when it is unset. I have not run this code, and the fixture is read-only, so nothing has been changed. The line most likely to be wrong is the stream handling in the route: it is synchronous, which is fine at this size but should be checked against a real order count.

## Questions I would ask

1. **How do warehouse staff reach the admin routes today (VPN, office network, a proxy that logs people in)?** Default: nothing protects them, so the export requires an `X-Admin-Token` header matching `ADMIN_TOKEN`, and returns 503 if `ADMIN_TOKEN` is not set. If a proxy already authenticates staff, the token is redundant but harmless, and can be dropped.
2. **Which columns do they need?** Default: order id, status, total (in currency units, e.g. `12.50`), tracking code, last updated, customer name. Customer email is left out because it is not needed for picking or shipping. If they need it to contact customers, it is one more column in the SELECT.
3. **All orders, or a filter (status, date range)?** Default: all orders, with an optional `?status=placed` filter, since "orders still to ship" is the likeliest warehouse use. A date range is a small addition later.

Answer first: Q1. It decides whether the token is needed at all.

## The change

`src/admin/ordersExport.js` (new):

```js
// CSV export of orders for warehouse staff.
const db = require('../db');

const COLUMNS = ['order_id', 'status', 'total', 'tracking_code', 'updated_at', 'customer_name'];

// Quote every field; neutralise spreadsheet formulas (tracking codes come from uploaded CSVs).
function cell(value) {
  if (value === null || value === undefined) return '""';
  let s = String(value);
  if (/^[=+\-@\t\r]/.test(s)) s = "'" + s;
  return '"' + s.replace(/"/g, '""') + '"';
}

function* orderRows(status) {
  const sql = `SELECT o.id, o.status, o.total_cents, o.tracking_code, o.updated_at, u.name
               FROM orders o LEFT JOIN users u ON u.id = o.user_id
               ${status ? 'WHERE o.status = ?' : ''} ORDER BY o.id`;
  const stmt = db.prepare(sql);
  for (const r of status ? stmt.iterate(status) : stmt.iterate()) {
    const total = r.total_cents == null ? null : (r.total_cents / 100).toFixed(2);
    yield [r.id, r.status, total, r.tracking_code, r.updated_at, r.name].map(cell).join(',') + '\r\n';
  }
}

function exportOrdersCsv(req, res) {
  const expected = process.env.ADMIN_TOKEN;
  if (!expected) return res.status(503).send('Export disabled: ADMIN_TOKEN not set');
  if (req.get('X-Admin-Token') !== expected) return res.status(401).send('Unauthorized');
  const status = typeof req.query.status === 'string' ? req.query.status : null;
  const date = new Date().toISOString().slice(0, 10);
  res.set('Content-Type', 'text/csv; charset=utf-8');
  res.set('Content-Disposition', `attachment; filename="orders-${date}.csv"`);
  res.set('Cache-Control', 'no-store');
  res.write('﻿' + COLUMNS.join(',') + '\r\n'); // BOM so Excel reads accents correctly
  for (const line of orderRows(status)) res.write(line);
  res.end();
}

module.exports = { exportOrdersCsv, orderRows, cell };
```

`src/server.js`, two lines:

```js
const { exportOrdersCsv } = require('./admin/ordersExport');
app.get('/admin/orders.csv', exportOrdersCsv);
```

`test/ordersExport.test.js` (new, `node:test`, no new dependency):

```js
const test = require('node:test');
const assert = require('node:assert');
process.env.DB_PATH = ':memory:';
const db = require('../src/db');
const { orderRows, cell } = require('../src/admin/ordersExport');
db.prepare("INSERT INTO users (id, email, name) VALUES (1, 'a@example.com', 'Ana \"A\", Lda')").run();
db.prepare("INSERT INTO orders (id, user_id, status, total_cents, tracking_code) VALUES (1, 1, 'shipped', 1050, '=HYPERLINK(1)')").run();
db.prepare("INSERT INTO orders (id, user_id, status, total_cents) VALUES (2, 99, 'placed', 200)").run();

test('quotes commas and quotes, neutralises formulas', () => {
  const [line] = [...orderRows('shipped')];
  assert.equal(line, '"1","shipped","10.50","\'=HYPERLINK(1)","","Ana ""A"", Lda"\r\n');
});
test('orders without a matching user still appear', () => {
  assert.equal([...orderRows(null)].length, 2);
});
test('null becomes empty field', () => assert.equal(cell(null), '""'));
```

## Failure coverage

- **Unknown caller:** token required; with no token configured the route refuses rather than opening up. Comparison is a plain `!==`; a timing attack is not a realistic risk on an internal tool, so I did not add `crypto.timingSafeEqual`.
- **Malicious cell contents:** tracking codes arrive through the CSV import, so a value starting with `=`, `+`, `-` or `@` is prefixed with `'` to stop spreadsheet formula execution. Every field is quoted, so commas, quotes and newlines in names are safe.
- **Large export / overload:** rows are read with `iterate()` rather than `all()`, so the result set is not built in memory. better-sqlite3 is synchronous, so the export blocks other requests while it runs; for a few thousand orders that is milliseconds. If the table reaches hundreds of thousands, add a date filter or move to batched reads. Check: `SELECT COUNT(*) FROM orders` in production.
- **Many callers at once:** read-only, no shared state; concurrent exports are safe.
- **Stale data / partial failure:** a single SELECT is a consistent snapshot in SQLite. If the client disconnects mid-download the writes fail harmlessly.
- **Orphaned rows:** `LEFT JOIN` keeps orders whose user is missing (customer name blank).
- **Caching:** `Cache-Control: no-store` so a proxy or browser does not keep the customer list.

## Verification

1. `npm test`: the three new tests and the existing two pass.
2. `ADMIN_TOKEN=test npm start`, then `curl -H "X-Admin-Token: test" -OJ localhost:3000/admin/orders.csv` and open the file in Excel or LibreOffice: accents in names show correctly, totals are numbers, no formula runs.
3. Same request without the header returns 401; with `ADMIN_TOKEN` unset returns 503.
4. Staff need the token given to them and a way to send the header. If they download from a browser, a header is awkward; the simplest fix is for the admin page (if one exists) to send it, or Q1 resolves it.

## Found, not touched

- `/admin/shipments/import` has no authentication and can mark any order shipped. The same token check should go on it; it is a one-line change once Q1 is answered.
- `importShipments` throws on a malformed line (`tracking` undefined), and there is no transaction, so a bad line halfway leaves earlier rows updated and later ones not.
- `importShipments` does not set `updated_at`, so imported shipments show a stale "last updated" in the export.
- Order confirmation e-mail is sent inside the request; a slow SMTP server slows every order.
- `GET /orders/:id` has no authentication and uses sequential IDs, so any order can be read by guessing.
- README typo: "recieve".
