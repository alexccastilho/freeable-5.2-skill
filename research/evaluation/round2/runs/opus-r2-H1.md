# Orders CSV export for shopmini's admin area

I read the whole repo. It's small: one Express app (`src/server.js`), SQLite through better-sqlite3, and one existing admin endpoint, `POST /admin/shipments/import`. Four things in the code shape the plan:

1. **There's no admin UI and no authentication.** The "admin area" is just routes under `/admin/`, and nothing protects them. Today anyone who can reach port 3000 can mark orders as shipped. A CSV export would make this worse, because it would let anyone download every order, and the orders are linked to customer names and emails. I won't ship the export without an auth check.
2. **The `orders` table has no `created_at` column.** It only has `updated_at`, which changes whenever an order is shipped. So "orders placed this week" can't be answered exactly from the data we have. I'll export `updated_at` and say clearly what it means. I won't pretend it's an order date.
3. **There are no shipping addresses in the schema.** The `users` table only has `email` and `name`. If warehouse staff want the CSV for picking and packing, the data they'd need isn't stored here.
4. **Tracking codes come in from an uploaded CSV** (`bulkImport.js`), so they're external input. If an export writes them out unchanged, a value like `=HYPERLINK(...)` would run as a formula when someone opens the file in Excel. The export needs to escape these values.

## Questions I would ask

1. **Which columns do they need? In particular, should customer email be included?**
   Default: `order_id, status, total (as a decimal like 12.50), tracking_code, last_updated (ISO-8601 UTC), customer_name`. I'd leave email out unless they ask for it, since the warehouse doesn't usually need it to ship.
2. **Should they be able to filter, by status or by date?**
   Default: an optional `?status=placed|shipped` filter. Without it, they get all orders. No date filter for now, because there's no reliable order-date column (see point 2 above).
3. **How do warehouse staff log in today? Is there a proxy, VPN, or SSO in front of the app?**
   Default: assume nothing protects it. I'd add HTTP Basic auth using credentials from environment variables (`ADMIN_USER`, `ADMIN_PASSWORD`). The browser shows its own login prompt, so a plain "Download CSV" link or bookmark works with no UI code. If no credentials are configured, the endpoint refuses every request rather than staying open.
4. **Should the same auth protect the existing `/admin/shipments/import` endpoint?**
   It's unprotected too, and I'd strongly recommend yes. But adding auth would break whatever script uploads to it now. Default: protect only the new endpoint in this change, and flag the import endpoint as a follow-up to do once whoever runs that upload is ready.
5. **Is there a real admin web page where a button should appear?**
   Default: there isn't one in this repo, so the deliverable is a URL (`/admin/orders.csv`) staff can bookmark.

## Plan (under those defaults)

1. **`src/admin/adminAuth.js`** (new): Basic-auth middleware.
   - Reads `ADMIN_USER` and `ADMIN_PASSWORD` from the environment.
   - Compares credentials with `crypto.timingSafeEqual`.
   - Returns `401` with a `WWW-Authenticate` header so the browser prompts for a login.
   - Returns `503` if the variables aren't set, so it never fails open.
2. **`src/admin/ordersExport.js`** (new): builds the CSV.
   - One query: `orders LEFT JOIN users`, ordered by `id`.
   - Reads rows with `stmt.iterate()` and writes them to the response as it goes, so a large table isn't loaded into memory all at once.
   - RFC 4180 quoting: values containing commas, quotes or newlines are wrapped in quotes, with inner quotes doubled.
   - Formula-injection guard: text cells starting with `=`, `+`, `-`, `@`, tab or carriage return get a leading `'`.
   - UTF-8 BOM and CRLF line endings, so Excel shows names with accents correctly.
   - `total_cents` is converted to a decimal string with integer math, not floats.
3. **`src/server.js`**: add `GET /admin/orders.csv` behind `adminAuth`. It sets `Content-Type: text/csv; charset=utf-8` and `Content-Disposition: attachment; filename="orders-YYYY-MM-DD.csv"`, with the date taken from `clock.now()` so tests can control it. It returns `400` for an unknown `status` value.
4. **`test/ordersExport.test.js`** (new): uses the same in-memory DB and clock setup as `orders.test.js`. Covers:
   - the header row and the shape of each row
   - escaping of commas, quotes and newlines
   - the formula-injection guard
   - the status filter
   - money formatting
   - auth: 401 without credentials, 503 when not configured, 200 with correct credentials

   The HTTP tests start `app.listen(0)` and call it with Node's built-in `fetch`, so no new dependencies are needed.
5. **README**: add one line under Layout for the new endpoint and the two environment variables. While I'm there, fix the typo "recieve" → "receive".
6. **Verify**: run `npm test`. Then start the app with credentials set, open `/admin/orders.csv` in a browser, and check that the file opens cleanly in Excel or LibreOffice.

## The edits

`src/admin/adminAuth.js`
```js
const crypto = require('crypto');

function safeEqual(a, b) {
  const ab = Buffer.from(a), bb = Buffer.from(b);
  return ab.length === bb.length && crypto.timingSafeEqual(ab, bb);
}

// HTTP Basic auth for back-office routes. Fails closed if not configured.
function adminAuth(req, res, next) {
  const user = process.env.ADMIN_USER, pass = process.env.ADMIN_PASSWORD;
  if (!user || !pass) return res.status(503).send('Admin access not configured');
  const [scheme, encoded] = (req.get('authorization') || '').split(' ');
  if (scheme === 'Basic' && encoded) {
    const decoded = Buffer.from(encoded, 'base64').toString();
    const i = decoded.indexOf(':');
    if (i >= 0 && safeEqual(decoded.slice(0, i), user) && safeEqual(decoded.slice(i + 1), pass)) return next();
  }
  res.set('WWW-Authenticate', 'Basic realm="shopmini admin", charset="UTF-8"');
  res.status(401).send('Authentication required');
}

module.exports = { adminAuth };
```

`src/admin/ordersExport.js`
```js
// CSV export of orders for warehouse staff.
const db = require('../db');

const STATUSES = new Set(['placed', 'shipped']);
const HEADER = ['order_id', 'status', 'total', 'tracking_code', 'last_updated', 'customer_name'];

function formatCents(cents) {
  if (cents == null) return '';
  const sign = cents < 0 ? '-' : '';
  const abs = Math.abs(cents);
  return `${sign}${Math.floor(abs / 100)}.${String(abs % 100).padStart(2, '0')}`;
}

// RFC 4180 quoting plus a guard against spreadsheet formula injection.
function csvCell(value) {
  if (value == null) return '';
  let s = String(value);
  if (typeof value === 'string' && /^[=+\-@\t\r]/.test(s)) s = `'${s}`;
  return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

function toRow(o) {
  return [o.id, o.status, formatCents(o.total_cents), o.tracking_code, o.updated_at, o.customer_name]
    .map(csvCell).join(',') + '\r\n';
}

function* exportOrdersCsv({ status } = {}) {
  const where = status ? 'WHERE o.status = ?' : '';
  const stmt = db.prepare(`
    SELECT o.id, o.status, o.total_cents, o.tracking_code, o.updated_at, u.name AS customer_name
    FROM orders o LEFT JOIN users u ON u.id = o.user_id
    ${where} ORDER BY o.id`);
  yield '﻿' + HEADER.join(',') + '\r\n';
  for (const o of (status ? stmt.iterate(status) : stmt.iterate())) yield toRow(o);
}

module.exports = { exportOrdersCsv, csvCell, formatCents, STATUSES };
```

`src/server.js` (additions)
```js
const clock = require('./clock');
const { adminAuth } = require('./admin/adminAuth');
const { exportOrdersCsv, STATUSES } = require('./admin/ordersExport');

app.get('/admin/orders.csv', adminAuth, (req, res) => {
  const { status } = req.query;
  if (status !== undefined && !STATUSES.has(status)) return res.status(400).send('Unknown status');
  const date = clock.now().toISOString().slice(0, 10);
  res.set('Content-Type', 'text/csv; charset=utf-8');
  res.set('Content-Disposition', `attachment; filename="orders-${date}.csv"`);
  for (const chunk of exportOrdersCsv({ status })) res.write(chunk);
  res.end();
});
```
(better-sqlite3 is synchronous, so writing in a loop is fine here. If exports ever reach hundreds of thousands of rows, I'd switch to `Readable.from(generator).pipe(res)` so it respects backpressure.)

`test/ordersExport.test.js` would cover the cases listed in plan step 4. One example:
```js
test('tracking codes that look like formulas are neutralised', () => {
  assert.equal(csvCell('=HYPERLINK("http://x")'), `"'=HYPERLINK(""http://x"")"`);
});
```

## Things I'd flag but not change in this task

- **`/admin/shipments/import` has no auth** (question 4 above). It also doesn't update `updated_at`, and it crashes on any line without a comma (`tracking.trim()` on `undefined`). Worth a separate fix.
- **No order-date column.** If staff want "today's orders", the clean fix is a migration that adds `created_at`. That can't be filled in correctly for existing orders, so it's a product decision, not part of this export.
- **No shipping address in the schema.** If the CSV is meant to be a pick or pack list, it can't be one until addresses are stored.
