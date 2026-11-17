# Orders CSV export for warehouse staff

I would add a `GET /admin/orders.csv` endpoint that downloads every order as a CSV file. Nothing has been changed or run: the repository is read-only for me, so the code below is untested.

Two things in the repository shape this:

- **There is no admin screen.** shopmini is an API only; "admin" is the single route `POST /admin/shipments/import`. So the download is a URL staff open in a browser (or a link from whatever tool they use), not a button on a page.
- **The admin routes have no authentication.** Anyone who can reach the server can already call the shipment import, and would be able to download this file too. For that reason I left customer names and e-mails out of the export.

## Edits

### New file: `src/admin/orderExport.js`

```js
// Warehouse downloads the order list as CSV (GET /admin/orders.csv).
const db = require('../db');

const HEADER = 'order_id,status,total,tracking_code,updated_at';

function quote(s) {
  return /[",\r\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
}
// Free-text fields: a leading = + - @ would run as a formula in Excel, so prefix it with '.
function text(v) {
  if (v === null || v === undefined) return '';
  const s = String(v);
  return quote(/^[=+\-@\t\r]/.test(s) ? "'" + s : s);
}
function money(cents) {
  return Number.isInteger(cents) ? (cents / 100).toFixed(2) : '';
}

function exportOrdersCsv({ status } = {}) {
  const sql = 'SELECT id, status, total_cents, tracking_code, updated_at FROM orders';
  const rows = status
    ? db.prepare(sql + ' WHERE status = ? ORDER BY id').all(status)
    : db.prepare(sql + ' ORDER BY id').all();
  const lines = rows.map((o) =>
    [o.id, text(o.status), money(o.total_cents), text(o.tracking_code), text(o.updated_at)].join(','));
  return [HEADER, ...lines].join('\r\n') + '\r\n';
}

module.exports = { exportOrdersCsv };
```

### `src/server.js`

Add two requires next to the existing ones:

```js
const clock = require('./clock');
const { exportOrdersCsv } = require('./admin/orderExport');
```

Add the route after the shipment import route:

```js
app.get('/admin/orders.csv', (req, res) => {
  const status = typeof req.query.status === 'string' ? req.query.status : undefined;
  const day = clock.now().toISOString().slice(0, 10);
  res.set('Content-Type', 'text/csv; charset=utf-8');
  res.set('Content-Disposition', `attachment; filename="orders-${day}.csv"`);
  res.send(exportOrdersCsv({ status }));
});
```

### New file: `test/orderExport.test.js`

`node --test` runs each test file in its own process, so this gets its own in-memory database.

```js
const test = require('node:test');
const assert = require('node:assert');
process.env.DB_PATH = ':memory:';
const db = require('../src/db');
const { exportOrdersCsv } = require('../src/admin/orderExport');

const insert = db.prepare('INSERT INTO orders (id, user_id, status, total_cents, tracking_code, updated_at) VALUES (?, ?, ?, ?, ?, ?)');
insert.run(1, null, 'placed', 1000, null, '2026-01-01T00:00:00.000Z');
insert.run(2, null, 'shipped', 2550, 'TRK,"2"', '2026-01-02T00:00:00.000Z');
insert.run(3, null, 'shipped', 5, '=HYPERLINK("x")', '2026-01-03T00:00:00.000Z');

test('exports all orders with a header row', () => {
  assert.equal(exportOrdersCsv(), [
    'order_id,status,total,tracking_code,updated_at',
    '1,placed,10.00,,2026-01-01T00:00:00.000Z',
    '2,shipped,25.50,"TRK,""2""",2026-01-02T00:00:00.000Z',
    '3,shipped,0.05,"\'=HYPERLINK(""x"")",2026-01-03T00:00:00.000Z',
    '',
  ].join('\r\n'));
});
test('filters by status', () => {
  const lines = exportOrdersCsv({ status: 'placed' }).trim().split('\r\n');
  assert.equal(lines.length, 2);
  assert.ok(lines[1].startsWith('1,placed,'));
});
test('no orders gives just the header', () => {
  assert.equal(exportOrdersCsv({ status: 'nope' }), 'order_id,status,total,tracking_code,updated_at\r\n');
});
```

### `README.md`

Add under "Running":

```
Warehouse staff can download the order list at /admin/orders.csv
(add ?status=placed to get only orders still to ship).
```

## What the file contains

| Column | Source | Note |
|---|---|---|
| `order_id` | `orders.id` | |
| `status` | `orders.status` | `placed` or `shipped` |
| `total` | `orders.total_cents` | Written as `10.00`; no currency column exists |
| `tracking_code` | `orders.tracking_code` | Empty until shipped |
| `updated_at` | `orders.updated_at` | ISO timestamp, UTC |

- **`updated_at` is not reliably the ship time.** The bulk shipment import does not touch it, so orders shipped that way still show the time they were placed. There is also no "created at" column, so the export cannot show an order date. I did not change either.
- **No items or addresses.** The database stores neither, so the export cannot be used as a pick list.
- **The status filter is an addition.** `?status=placed` pairs with the existing shipment import (download what is unshipped, upload tracking codes). Drop the four lines if you want the plain list only.
- **The whole list is built in memory.** That is fine for a small shop; if the table reaches hundreds of thousands of rows it should stream instead.

## Questions I would ask

1. **Which columns do staff need, and should customer name or e-mail be included?**
   Default: the five columns above, no customer data, because the endpoint is unauthenticated.
2. **Is the server reachable only from an internal network, or should the admin routes get authentication first?**
   Default: internal only, so I match the existing admin route and add no auth. If it is exposed, auth for `/admin/*` should come before this ships.
3. **All orders, or only a subset (unshipped, a date range)?**
   Default: all orders, with the optional `status` filter.
4. **Will the file be opened in Excel with a locale that expects `;` separators or decimal commas?**
   Default: comma-separated, `.` decimals, UTF-8, CRLF line endings.
