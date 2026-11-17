I couldn't modify the repository, so nothing below has been applied or run. These are the edits I would make: a new `GET /admin/orders/export` endpoint that returns all orders as a CSV download.

One thing to decide before this ships: **nothing under `/admin` is authenticated today**, and neither is the rest of the API. The export would put every order, with customer names, behind a URL that anyone who can reach the server can fetch. I've followed the existing pattern and added no auth, which is only acceptable if the service is reachable solely from your internal network.

## What "admin area" means here

shopmini has no admin UI. The admin area is the single endpoint `POST /admin/shipments/import` in `src/server.js`. So the download is a URL that staff open in a browser, or that a back-office page links to. If there is an admin frontend in another repository, it needs a link to this URL.

## The CSV

One row per order, sorted by order id:

| Column | Source | Notes |
|---|---|---|
| `order_id` | `orders.id` | |
| `status` | `orders.status` | `placed` or `shipped` |
| `total` | `orders.total_cents` | Written as `10.00`, not cents |
| `tracking_code` | `orders.tracking_code` | Empty until shipped |
| `updated_at` | `orders.updated_at` | ISO timestamp, UTC |
| `customer_name` | `users.name` | Empty if the user row is missing |

- **Filter:** `?status=placed` limits the export to one status. With no filter, you get every order.
- **Excel:** the file starts with a UTF-8 byte-order mark and uses CRLF line endings, so accented names open correctly.
- **Formula injection:** customer names and tracking codes that start with `=`, `+`, `-` or `@` get a leading apostrophe so a spreadsheet won't execute them.
- **File name:** `orders-YYYY-MM-DD.csv`, dated from the injectable clock.

## Edits

### New file `src/admin/orderExport.js`

```js
// Warehouse downloads the order list as a CSV.
const db = require('../db');

const HEADER = ['order_id', 'status', 'total', 'tracking_code', 'updated_at', 'customer_name'];

// Free text that a spreadsheet would treat as a formula gets a leading apostrophe.
function text(value) {
  const s = value == null ? '' : String(value);
  return /^[=+\-@\t\r]/.test(s) ? `'${s}` : s;
}
function cell(value) {
  const s = value == null ? '' : String(value);
  return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

function exportOrdersCsv({ status } = {}) {
  const sql = `SELECT o.id, o.status, o.total_cents, o.tracking_code, o.updated_at, u.name
    FROM orders o LEFT JOIN users u ON u.id = o.user_id
    ${status ? 'WHERE o.status = ?' : ''} ORDER BY o.id`;
  const rows = status ? db.prepare(sql).all(status) : db.prepare(sql).all();
  const lines = [HEADER.join(',')];
  for (const r of rows) {
    lines.push([
      r.id,
      r.status,
      r.total_cents == null ? '' : (r.total_cents / 100).toFixed(2),
      text(r.tracking_code),
      r.updated_at,
      text(r.name),
    ].map(cell).join(','));
  }
  return lines.join('\r\n') + '\r\n';
}
module.exports = { exportOrdersCsv };
```

### `src/server.js`

Add two requires next to the existing ones:

```js
const clock = require('./clock');
const { exportOrdersCsv } = require('./admin/orderExport');
```

Add the route after the `/admin/shipments/import` line:

```js
app.get('/admin/orders/export', (req, res) => {
  const status = typeof req.query.status === 'string' ? req.query.status : undefined;
  const day = clock.now().toISOString().slice(0, 10);
  res.type('text/csv');
  res.set('Content-Disposition', `attachment; filename="orders-${day}.csv"`);
  res.send('﻿' + exportOrdersCsv({ status }));
});
```

### New file `test/orderExport.test.js`

`node --test` runs each test file in its own process, so this file gets its own in-memory database.

```js
const test = require('node:test');
const assert = require('node:assert');
process.env.DB_PATH = ':memory:';
const db = require('../src/db');
const { exportOrdersCsv } = require('../src/admin/orderExport');
const app = require('../src/server');

db.prepare("INSERT INTO users (id, email, name) VALUES (1, 'a@example.com', 'Souza, Ana'), (2, 'b@example.com', '=cmd()')").run();
db.prepare(`INSERT INTO orders (id, user_id, status, total_cents, tracking_code, updated_at) VALUES
  (1, 1, 'placed', 1000, NULL, '2026-01-01T00:00:00.000Z'),
  (2, 2, 'shipped', 2550, 'TRK2', '2026-01-02T00:00:00.000Z')`).run();

test('exports every order with a header row', () => {
  assert.equal(exportOrdersCsv(),
    'order_id,status,total,tracking_code,updated_at,customer_name\r\n' +
    '1,placed,10.00,,2026-01-01T00:00:00.000Z,"Souza, Ana"\r\n' +
    "2,shipped,25.50,TRK2,2026-01-02T00:00:00.000Z,'=cmd()\r\n");
});
test('filters by status', () => {
  const lines = exportOrdersCsv({ status: 'placed' }).trim().split('\r\n');
  assert.equal(lines.length, 2);
  assert.match(lines[1], /^1,placed,/);
});
test('GET /admin/orders/export returns a CSV attachment', async () => {
  const server = app.listen(0);
  try {
    const res = await fetch(`http://localhost:${server.address().port}/admin/orders/export?status=shipped`);
    assert.equal(res.status, 200);
    assert.match(res.headers.get('content-type'), /^text\/csv/);
    assert.match(res.headers.get('content-disposition'), /attachment; filename="orders-\d{4}-\d{2}-\d{2}\.csv"/);
    assert.match(await res.text(), /^﻿?order_id,.*\r\n2,shipped,/s);
  } finally { server.close(); }
});
```

The route test uses the global `fetch`, so it needs Node 18 or later.

### `README.md`

Add under "Running":

```
Warehouse staff can download all orders as a CSV from
http://localhost:3000/admin/orders/export (add ?status=placed for unshipped orders only).
```

## Limits you should know about

- **No order date.** The `orders` table has only `updated_at`. For an unshipped order that is the time it was placed; for a shipped one it is the time it shipped.
- **Stale `updated_at` on imported shipments.** `src/admin/bulkImport.js` marks orders shipped without touching `updated_at`, so those rows show the placement time. I left this alone; it is a one-line fix if you want it.
- **No shipping address or line items.** The schema doesn't hold them, so the export can't either.
- **Do not upload this file to the shipment import.** That endpoint reads the first two columns as order id and tracking code, so it would mark every listed order as shipped and overwrite its tracking code with the status text.
- **Size.** The whole export is built in memory. That is fine for tens of thousands of orders; beyond that it should stream.

## Questions I would ask

1. **Is the service reachable only from an internal network?** Default assumed: yes, so no auth was added. If not, I would put a shared-secret or session check in front of all `/admin` routes before shipping this.
2. **Which columns do staff need?** Default assumed: the six above, with customer name but without e-mail, to keep personal data in the file to a minimum.
3. **All orders, or only those waiting to ship?** Default assumed: all, with `?status=` as the opt-in filter.
4. **Is there an admin frontend elsewhere that should get a "Download CSV" button?** Default assumed: no, staff use the URL directly.
