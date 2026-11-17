The e-mail itself is a few lines. The real work is that most orders are probably not marked shipped through `markShipped`. The warehouse's end-of-day CSV upload (`POST /admin/shipments/import` → `src/admin/bulkImport.js`) runs a raw `UPDATE` that skips the order service. A hook placed only in `markShipped` would miss exactly the orders customers are complaining about. So the change sends the e-mail from both paths, and only when an order first changes to `shipped`. That way a re-uploaded CSV or a corrected tracking code does not e-mail the customer again.

I have not changed anything and have not run this code: the fixture is read-only and has no installed dependencies. The assertion most likely to be wrong is the timing in the bulk-import test (it waits one `setImmediate` for the background sends). Check that one first.

## Questions I would ask

1. **How do your shipments actually get marked: the CSV import, the per-order endpoint, or both?** Default: both send the e-mail. If only one path is used, the change stays the same, because the other path costs nothing.
2. **How many orders does a typical end-of-day CSV hold, and can you live with a few shipping e-mails being lost if the server restarts mid-batch?** Default: e-mails go out one at a time in the background after the import responds, with no retry. A failure is logged with the order id. If volumes are in the hundreds or more, or a lost e-mail is not acceptable, add a `shipped_email_sent_at` column and a small retry sweep. That is a schema change, a larger piece of work, and I would do it as a follow-up.
3. **Should a later tracking-code correction send a second e-mail?** Default: no. Only the first change to `shipped` sends.
4. **Do you know the carrier, so the e-mail can carry a tracking link?** Default: the e-mail shows the tracking code as plain text. The schema has no carrier field. If you have one carrier, I add its URL pattern to the template.

Answer first: 1 and 2. Question 2 decides whether this stays a three-file change or needs a column and a retry job.

Stated assumptions, not questions:
- Shipping notices are transactional, so they ignore `marketing_opt_in`.
- Orders already shipped before the deploy get no e-mail.

## The change

Three source files, one test file and one README line. No new dependencies and no schema change.

### `src/notifications/mailer.js`: add the template

```diff
 const templates = {
   orderConfirmation: (order, user) => ({
     subject: `Order #${order.id} confirmed`,
     text: `Hi ${user.name}, we received your order #${order.id}.`,
   }),
+  orderShipped: (order, user) => ({
+    subject: `Order #${order.id} has shipped`,
+    text: `Hi ${user.name || 'there'}, your order #${order.id} is on its way.`
+      + (order.tracking_code ? ` Tracking code: ${order.tracking_code}.` : ''),
+  }),
 };
```

### `src/orders/orderService.js`: send on the first change to `shipped`

```diff
 function getOrder(id) { return db.prepare('SELECT * FROM orders WHERE id = ?').get(id); }
+
+// Fire-and-forget: shipping must not fail or slow down because SMTP is slow or down.
+// Returns a promise that never rejects, so callers may await it to send sequentially.
+function notifyShipped(order) {
+  const user = order && getUser(order.user_id);
+  if (!user || !user.email) {
+    console.error('shipping mail skipped: no recipient for order', order && order.id);
+    return Promise.resolve();
+  }
+  return mailer.send('orderShipped', order, user)
+    .catch((e) => console.error('shipping mail failed for order', order.id, e.message));
+}
+
 function markShipped(id, trackingCode) {
+  const before = getOrder(id);
   db.prepare('UPDATE orders SET status = ?, tracking_code = ?, updated_at = ? WHERE id = ?')
     .run('shipped', trackingCode, clock.now().toISOString(), id);
-  return getOrder(id);
+  const order = getOrder(id);
+  if (before && before.status !== 'shipped') notifyShipped(order);
+  return order;
 }
-module.exports = { placeOrder, getOrder, markShipped };
+module.exports = { placeOrder, getOrder, markShipped, notifyShipped };
```

`markShipped` stays synchronous, so `server.js` and the existing test are unchanged. Reading `before` and then updating cannot interleave with another request, because better-sqlite3 is synchronous and the process is single-threaded. The `.catch` matters: `mailer.send` builds the template outside its own `try`. A missing user would otherwise become an unhandled rejection, which crashes current Node versions.

### `src/admin/bulkImport.js`: same rule for the CSV path

```diff
 const db = require('../db');
+const { getOrder, notifyShipped } = require('../orders/orderService');
 function importShipments(csvText) {
   const stmt = db.prepare("UPDATE orders SET status = 'shipped', tracking_code = ? WHERE id = ?");
   let n = 0;
-  for (const line of csvText.trim().split('\n').slice(1)) {
-    const [orderId, tracking] = line.split(',');
-    stmt.run(tracking.trim(), Number(orderId)); n++;
-  }
+  const newlyShipped = [];
+  try {
+    for (const line of csvText.trim().split('\n').slice(1)) {
+      const [orderId, tracking] = line.split(',');
+      const before = getOrder(Number(orderId));
+      stmt.run(tracking.trim(), Number(orderId)); n++;
+      if (before && before.status !== 'shipped') newlyShipped.push(Number(orderId));
+    }
+  } finally {
+    // Rows updated before a malformed line stay updated (unchanged behaviour), so their
+    // customers are e-mailed too; otherwise a re-upload would never notify them.
+    (async () => { for (const id of newlyShipped) await notifyShipped(getOrder(id)); })();
+  }
   return n;
 }
```

Why the e-mails go out after the loop, one at a time:
- The warehouse gets its response without waiting on SMTP for every row.
- The transport is not pooled, so firing them all at once would open one SMTP connection per order.
- A slow mail server cannot hold the database loop open.

The `finally` keeps today's partial-apply behaviour on a bad line, and still notifies the rows that did apply.

### `test/orders.test.js`: append

```js
const { importShipments } = require('../src/admin/bulkImport');
const tick = () => new Promise((r) => setImmediate(r));

test('first markShipped sends one shipping e-mail; repeat does not', async () => {
  const o = await orders.placeOrder(1, 500);
  sent.length = 0;
  orders.markShipped(o.id, 'TRK2');
  orders.markShipped(o.id, 'TRK2-corrected');
  const shipped = sent.filter((a) => a[0] === 'orderShipped');
  assert.equal(shipped.length, 1);
  assert.equal(shipped[0][1].tracking_code, 'TRK2');
});

test('bulk import e-mails newly shipped orders once, not on re-upload', async () => {
  const a = await orders.placeOrder(1, 100);
  const b = await orders.placeOrder(1, 200);
  sent.length = 0;
  const csv = `orderId,trackingCode\n${a.id},T-A\n${b.id},T-B\n`;
  assert.equal(importShipments(csv), 2);
  await tick();
  assert.deepEqual(sent.map((s) => s[1].id).sort(), [a.id, b.id].sort());
  sent.length = 0;
  importShipments(csv);
  await tick();
  assert.equal(sent.length, 0);
});

test('template includes the tracking code', () => {
  const t = mailer.templates.orderShipped({ id: 7, tracking_code: 'ZX9' }, { name: 'Ana' });
  assert.match(t.text, /ZX9/);
});
```

### `README.md`, line 11

`Customers receive an order confirmation e-mail when they place an order, and a shipping e-mail with the tracking code when the order is first marked shipped (by the ship endpoint or the CSV import).`

## Verification

1. `npm test`. All five tests should pass, including the two existing ones, which need no changes.
2. Locally, point `SMTP_HOST` at a catch-all such as MailHog. Place an order for an internal address, then ship it once through `POST /orders/:id/ship` and once through the CSV import. Expect exactly one shipping e-mail per order with the right tracking code.

## Rollout

This sends e-mail to real customers, so:
- Before the first real import after deploy, ship one test order addressed to yourselves through each path.
- After that first end-of-day import, compare the number of `shipping mail failed` / `skipped` log lines with the number of orders shipped.
- Revert (one commit, no schema to undo) if any customer gets a duplicate, or if more than a handful of sends fail. Repeated failures would point at SMTP limits, which is question 2's follow-up.

## Found, not touched

- **No authentication on any route.** This includes `/admin/shipments/import` and `/orders/:id/ship`. Anyone who can reach the API can mark orders shipped, and now that also e-mails customers. This is the largest exposure and worth its own piece of work.
- **The CSV import crashes on a malformed line** (`tracking` is undefined). Rows before the bad line stay applied, with no transaction. It also counts order ids that do not exist, and never sets `updated_at`.
- **`GET /orders/:id` uses sequential ids with no access check,** so anyone can read any order's status and tracking code.
- **The mailer swallows every error.** The confirmation e-mail is also sent synchronously inside `POST /orders`, so a slow SMTP server slows order placement.
- **`markShipped` on a non-existent id** returns `undefined` with a 200.
- **README typo "recieve".** It is fixed by the line above, since that line is replaced anyway.
