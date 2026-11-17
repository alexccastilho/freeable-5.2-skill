The CSV itself is about 30 lines. The part that matters is that shopmini has no authentication anywhere: `/admin/shipments/import` and every other route in `src/server.js` are open to anyone who can reach the server. A plain `GET /admin/orders.csv` would hand the whole order list, with customer names, to anyone who guesses the URL. So the export ships behind a password check, and that check fails closed: if no password is configured, the route refuses to serve. There is also no admin UI in the repository, so "the admin area" here means a URL staff open in a browser. That is why I use HTTP Basic auth: the browser shows its own login box, and after that the link downloads normally. I can't modify the repository, so the edits below have not been run. The line most likely to be wrong is the `fetch` call in the test, which assumes Node 18 or newer.

## Questions I would ask

1. **What is "the admin area" today: a web page I can't see, a tool staff use, or just URLs?** Default: just URLs, opened in a browser, with Basic auth. If there is an admin front end with its own login, the route should use that session instead, and the Basic-auth middleware goes away.
2. **Which columns do the staff need?** Default: order id, status, total, tracking code, last updated, customer id, customer name. Email is left out because the schema has no address to ship to, and it keeps personal data in the file to a minimum. Adding a column is a one-line change.
3. **Is the server reached over HTTPS?** Default: yes, through a proxy or load balancer. If it is plain HTTP, Basic auth sends the password in a form anyone on the network can read, and HTTPS has to come first.
4. **All orders, or a filter (today's, unshipped only)?** Default: all orders, sorted by id. If they want "unshipped today", I add a `?status=` parameter and leave out the rest.

Answer first: 1 and 3. They decide whether this auth approach is the right one.

## Edits

**New file `src/admin/ordersExport.js`**

```js
// CSV export of orders for warehouse staff.
const db = require('../db');

const COLUMNS = ['id', 'status', 'total_cents', 'tracking_code', 'updated_at', 'user_id', 'customer_name'];

function cell(v) {
  if (v === null || v === undefined) return '';
  let s = String(v);
  // Stop spreadsheet formula injection from text fields (names, tracking codes).
  if (typeof v === 'string' && /^[=+\-@\t\r]/.test(s)) s = "'" + s;
  return /[",\r\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
}

function ordersCsv() {
  const rows = db.prepare(`
    SELECT o.id, o.status, o.total_cents, o.tracking_code, o.updated_at, o.user_id, u.name AS customer_name
    FROM orders o LEFT JOIN users u ON u.id = o.user_id
    ORDER BY o.id`).all();
  const lines = [COLUMNS.join(',')];
  for (const r of rows) lines.push(COLUMNS.map((c) => cell(r[c])).join(','));
  return '﻿' + lines.join('\r\n') + '\r\n'; // BOM so Excel reads UTF-8 names correctly
}

module.exports = { ordersCsv, cell };
```

**`src/server.js`**: add after the existing requires and the import route:

```js
const crypto = require('crypto');
const clock = require('./clock');
const { ordersCsv } = require('./admin/ordersExport');

// Basic auth for admin downloads. Any username; the password is ADMIN_PASSWORD.
function requireAdmin(req, res, next) {
  const expected = process.env.ADMIN_PASSWORD;
  if (!expected) return res.status(503).send('Admin export disabled: ADMIN_PASSWORD is not set');
  const [scheme, encoded] = (req.get('authorization') || '').split(' ');
  const password = scheme === 'Basic' && encoded
    ? Buffer.from(encoded, 'base64').toString().split(':').slice(1).join(':') : '';
  const a = crypto.createHash('sha256').update(password).digest();
  const b = crypto.createHash('sha256').update(expected).digest();
  if (!crypto.timingSafeEqual(a, b)) {
    return res.set('WWW-Authenticate', 'Basic realm="shopmini admin"').status(401).end();
  }
  next();
}

app.get('/admin/orders.csv', requireAdmin, (req, res) => {
  const day = clock.now().toISOString().slice(0, 10);
  res.set({
    'Content-Type': 'text/csv; charset=utf-8',
    'Content-Disposition': `attachment; filename="orders-${day}.csv"`,
    'Cache-Control': 'no-store',
  });
  res.send(ordersCsv());
});
```

**New file `test/adminExport.test.js`**

```js
const test = require('node:test');
const assert = require('node:assert');
process.env.DB_PATH = ':memory:';
process.env.ADMIN_PASSWORD = 'secret';
const db = require('../src/db');
const { cell } = require('../src/admin/ordersExport');
const app = require('../src/server');

db.prepare("INSERT INTO users (id, email, name) VALUES (1, 'a@example.com', 'Silva, \"Ana\"')").run();
db.prepare("INSERT INTO orders (user_id, status, total_cents) VALUES (1, 'placed', 1000)").run();

const auth = (p) => ({ authorization: 'Basic ' + Buffer.from('staff:' + p).toString('base64') });

test('export requires the password', async (t) => {
  const srv = app.listen(0); t.after(() => srv.close());
  const url = `http://127.0.0.1:${srv.address().port}/admin/orders.csv`;
  assert.equal((await fetch(url)).status, 401);
  assert.equal((await fetch(url, { headers: auth('wrong') })).status, 401);
  const ok = await fetch(url, { headers: auth('secret') });
  assert.equal(ok.status, 200);
  const body = await ok.text();
  assert.match(body, /^﻿?id,status,total_cents/);
  assert.match(body, /"Silva, ""Ana"""/);
  assert.doesNotMatch(body, /a@example\.com/);
});

test('cells are escaped and formula-safe', () => {
  assert.equal(cell('=HYPERLINK("x")'), '"\'=HYPERLINK(""x"")"');
  assert.equal(cell(-500), '-500');
  assert.equal(cell(null), '');
});
```

## Failure modes covered

- **Unknown caller:** Basic auth, and a missing `ADMIN_PASSWORD` gives 503 rather than an open route. The comparison is constant-time.
- **Malicious data in the file:** quoting handles commas, quotes and newlines in names. Text cells that start with `= + - @` get a `'` prefix so Excel won't run them as formulas. Numbers are left alone, so a negative total stays numeric.
- **Partial failure:** the file is built in full before any byte is sent. A database error gives a 500, not a truncated CSV that looks complete.
- **Many callers at once / overload:** `better-sqlite3` is synchronous, so a big export blocks the process while it runs. That is fine for a warehouse-sized table of a few tens of thousands of rows. It would become a problem at hundreds of thousands, and then the fix is a date filter, not streaming.
- **Stale data:** the file is a snapshot taken when it is requested. `no-store` stops a proxy or browser from serving yesterday's file.
- **Several instances:** doesn't apply. There is no shared state beyond the database.

## Verification

`npm test`, then on the deployed server: set `ADMIN_PASSWORD`, open `/admin/orders.csv` in a browser, confirm the login prompt appears, and confirm the file opens in Excel with names intact and one row per order.

## Found, not touched

- `/admin/shipments/import` and `POST /orders/:id/ship` have no authentication. Anyone can mark orders shipped. `requireAdmin` can be put in front of both with one word each. Say if you want that.
- `importShipments` doesn't set `updated_at`, counts lines rather than rows actually updated (unknown order ids still count as "updated"), and crashes on a blank or short line (`tracking.trim()` on undefined).
- `GET /orders/:id` returns any order to anyone by sequential id.
- `mailer.send` runs inside the request and swallows errors, so a slow SMTP server slows down order placement.
- README typo: "recieve".
