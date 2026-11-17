The repository is read-only for me, so nothing in it has changed. The full change is the patch at the end, ready to apply with `git apply`.

I applied it to a scratch copy and the test suite passes there (7 tests, 5 of them new), with two limits:

- **Database driver:** `better-sqlite3` would not compile on this machine (Node 26), so the tests ran against a small stand-in built on `node:sqlite`. Run `npm test` once on your normal setup.
- **Real delivery:** the tests replace the mailer, as the existing ones do, so no message has gone through your SMTP provider.

## What the patch does

Customers get an "Order #N has shipped" e-mail with the tracking code when an order becomes shipped, by either route:

- **Single order:** `POST /orders/:id/ship` sends the e-mail before it responds, the same way the confirmation e-mail works today.
- **Warehouse CSV import:** `POST /admin/shipments/import` bypasses the order service and writes to the table directly, so it would have sent nothing. It now sends one e-mail per imported order, after the response, one at a time, so a large file does not hold the upload open.

Each order gets the e-mail at most once. A new column `orders.shipping_email_sent_at` records it, so re-shipping an order or re-uploading the same CSV does not e-mail the customer again. If a send fails, the column stays empty and the next ship call or import for that order tries again.

## Behaviour you should know about

- **Existing shipped orders:** on first start the column is added, and orders already shipped are stamped as done. Without that, re-importing an old CSV would e-mail customers about orders that shipped weeks ago.
- **No automatic retry:** a failed send is logged and only retried when that order is shipped or imported again. To find the ones still owed: `SELECT id FROM orders WHERE status = 'shipped' AND shipping_email_sent_at IS NULL`.
- **Restart during an import:** e-mails not yet sent for that file are lost until the same CSV is uploaded again.
- **`markShipped` is now async:** the route and the existing test are updated; there are no other callers in the repo.
- **`mailer.send` now resolves to `true` or `false`:** it used to resolve to nothing. The confirmation e-mail path ignores the value, so it behaves as before.
- **Marketing opt-in:** I did not check `marketing_opt_in`, because this is a transactional message like the order confirmation.

## Questions I would ask

1. **Should the e-mail carry a tracking link or carrier name?** The data only has a bare tracking code. Default assumed: plain text with the code, no link.
2. **If the tracking code is corrected after the e-mail went out, should the customer get a second e-mail?** Default assumed: no, one e-mail per order.
3. **Is the wording acceptable?** Default assumed: subject "Order #12 has shipped", body "Hi Ana, your order #12 is on its way. Tracking code: TRK1." in the style of the confirmation e-mail.
4. **Is sending bulk-import e-mails after the response acceptable?** The alternative is to make the upload wait until every e-mail is sent, which is safer against restarts but slow for big files. Default assumed: after the response.

## Problems I noticed and left alone

- **No authentication:** the ship and import endpoints are open to anyone who can reach the service, and they now trigger customer e-mail (once per order).
- **Bad CSV line:** a malformed line makes the import fail with a 500 halfway, leaving earlier rows shipped. Those rows do still get their e-mail.
- **Import count:** the `updated` number counts CSV lines, including ones whose order id does not exist.
- **`updated_at`:** the import does not set it.

Say if you want any of these fixed.

## Patch

```diff
--- a/README.md
+++ b/README.md
@@ -8,7 +8,9 @@
     npm start        # http://localhost:3000
     npm test
 
-Customers recieve an order confirmation e-mail when they place an order.
+Customers recieve an order confirmation e-mail when they place an order,
+and a shipping e-mail with the tracking code when the order is marked shipped (single-order
+endpoint or warehouse CSV import).
 
 ## Layout
 
--- a/src/admin/bulkImport.js
+++ b/src/admin/bulkImport.js
@@ -1,12 +1,21 @@
 // Warehouse uploads a CSV of "orderId,trackingCode" at end of day.
 // Written in a hurry for peak season; updates rows directly for speed.
 const db = require('../db');
+const orders = require('../orders/orderService');
 function importShipments(csvText) {
   const stmt = db.prepare("UPDATE orders SET status = 'shipped', tracking_code = ? WHERE id = ?");
   let n = 0;
-  for (const line of csvText.trim().split('\n').slice(1)) {
-    const [orderId, tracking] = line.split(',');
-    stmt.run(tracking.trim(), Number(orderId)); n++;
+  const ids = [];
+  try {
+    for (const line of csvText.trim().split('\n').slice(1)) {
+      const [orderId, tracking] = line.split(',');
+      stmt.run(tracking.trim(), Number(orderId)); n++;
+      ids.push(Number(orderId));
+    }
+  } finally {
+    // Not awaited: shipping e-mails go out after the response, one at a time, so a large file
+    // does not hold the upload open on SMTP. Rows imported before a bad line still get theirs.
+    orders.notifyShippedMany(ids);
   }
   return n;
 }
--- a/src/db.js
+++ b/src/db.js
@@ -4,4 +4,12 @@
   CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, email TEXT UNIQUE, name TEXT, marketing_opt_in INTEGER DEFAULT 0);
   CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id), status TEXT, total_cents INTEGER, tracking_code TEXT, updated_at TEXT);
 `);
+// shipping_email_sent_at: NULL on a shipped order means its shipping e-mail is still owed.
+// Orders already shipped when this column is first added are stamped so they never get a late e-mail.
+if (!db.prepare("SELECT 1 FROM pragma_table_info('orders') WHERE name = 'shipping_email_sent_at'").get()) {
+  db.exec(`
+    ALTER TABLE orders ADD COLUMN shipping_email_sent_at TEXT;
+    UPDATE orders SET shipping_email_sent_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE status = 'shipped';
+  `);
+}
 module.exports = db;
--- a/src/notifications/mailer.js
+++ b/src/notifications/mailer.js
@@ -5,11 +5,17 @@
     subject: `Order #${order.id} confirmed`,
     text: `Hi ${user.name}, we received your order #${order.id}.`,
   }),
+  orderShipped: (order, user) => ({
+    subject: `Order #${order.id} has shipped`,
+    text: `Hi ${user.name}, your order #${order.id} is on its way.`
+      + (order.tracking_code ? ` Tracking code: ${order.tracking_code}.` : ''),
+  }),
 };
 // Sends synchronously in the request path. Errors are logged and swallowed.
+// Resolves to false when the send failed, so callers that care can retry later.
 async function send(templateName, order, user) {
   const t = templates[templateName](order, user);
-  try { await transport.sendMail({ to: user.email, from: 'orders@shopmini.example', ...t }); }
-  catch (e) { console.error('mail failed', e.message); }
+  try { await transport.sendMail({ to: user.email, from: 'orders@shopmini.example', ...t }); return true; }
+  catch (e) { console.error('mail failed', e.message); return false; }
 }
 module.exports = { send, templates };
--- a/src/orders/orderService.js
+++ b/src/orders/orderService.js
@@ -11,9 +11,28 @@
   return order;
 }
 function getOrder(id) { return db.prepare('SELECT * FROM orders WHERE id = ?').get(id); }
-function markShipped(id, trackingCode) {
+async function markShipped(id, trackingCode) {
   db.prepare('UPDATE orders SET status = ?, tracking_code = ?, updated_at = ? WHERE id = ?')
     .run('shipped', trackingCode, clock.now().toISOString(), id);
+  await notifyShipped(id);
   return getOrder(id);
 }
-module.exports = { placeOrder, getOrder, markShipped };
+// Sends the shipping e-mail at most once per order. Safe to call repeatedly: a no-op once the
+// e-mail went out, a retry if the previous attempt failed. Never throws.
+async function notifyShipped(id) {
+  let claimed = false; let sent = false;
+  try {
+    // Claim before the slow SMTP call so a concurrent request cannot send a second e-mail.
+    claimed = db.prepare("UPDATE orders SET shipping_email_sent_at = ? WHERE id = ? AND status = 'shipped' AND shipping_email_sent_at IS NULL")
+      .run(clock.now().toISOString(), id).changes === 1;
+    if (!claimed) return false;
+    const order = getOrder(id);
+    const user = getUser(order.user_id);
+    if (user) sent = (await mailer.send('orderShipped', order, user)) !== false;
+    else console.error('shipping mail skipped: no user for order', id);
+  } catch (e) { console.error('shipping mail failed', e.message); }
+  if (claimed && !sent) db.prepare('UPDATE orders SET shipping_email_sent_at = NULL WHERE id = ?').run(id);
+  return sent;
+}
+async function notifyShippedMany(ids) { for (const id of ids) await notifyShipped(id); }
+module.exports = { placeOrder, getOrder, markShipped, notifyShipped, notifyShippedMany };
--- a/src/server.js
+++ b/src/server.js
@@ -5,7 +5,7 @@
 app.use(express.json()); app.use(express.text());
 app.post('/orders', async (req, res) => res.json(await orders.placeOrder(req.body.userId, req.body.totalCents)));
 app.get('/orders/:id', (req, res) => res.json(orders.getOrder(Number(req.params.id))));
-app.post('/orders/:id/ship', (req, res) => res.json(orders.markShipped(Number(req.params.id), req.body.trackingCode)));
+app.post('/orders/:id/ship', async (req, res) => res.json(await orders.markShipped(Number(req.params.id), req.body.trackingCode)));
 app.post('/admin/shipments/import', (req, res) => res.json({ updated: importShipments(req.body) }));
 if (require.main === module) app.listen(3000);
 module.exports = app;
--- a/test/orders.test.js
+++ b/test/orders.test.js
@@ -5,13 +5,46 @@
 const mailer = require('../src/notifications/mailer');
 const db = require('../src/db');
 const orders = require('../src/orders/orderService');
-const sent = []; mailer.send = async (...a) => { sent.push(a); };
+const { importShipments } = require('../src/admin/bulkImport');
+const sent = []; let failSends = false;
+mailer.send = async (...a) => { if (failSends) return false; sent.push(a); return true; };
+const shippedMails = () => sent.filter((a) => a[0] === 'orderShipped');
+const backgroundMail = () => new Promise((r) => setImmediate(r));
 clock._setNow(() => new Date('2026-01-01T00:00:00Z'));
 db.prepare("INSERT INTO users (id, email, name) VALUES (1, 'a@example.com', 'Ana')").run();
 test('placing an order sends confirmation', async () => {
   const o = await orders.placeOrder(1, 1000);
   assert.equal(o.status, 'placed'); assert.equal(sent[0][0], 'orderConfirmation');
 });
-test('markShipped sets tracking', () => {
-  const o = orders.markShipped(1, 'TRK1'); assert.equal(o.status, 'shipped');
+test('markShipped sets tracking', async () => {
+  const o = await orders.markShipped(1, 'TRK1'); assert.equal(o.status, 'shipped');
+});
+test('markShipped sends one shipping e-mail with the tracking code', () => {
+  assert.equal(shippedMails().length, 1);
+  const [, order, user] = shippedMails()[0];
+  assert.equal(order.tracking_code, 'TRK1'); assert.equal(user.email, 'a@example.com');
+  assert.match(mailer.templates.orderShipped(order, user).text, /TRK1/);
+});
+test('shipping the same order again does not e-mail twice', async () => {
+  await orders.markShipped(1, 'TRK1');
+  importShipments('orderId,trackingCode\n1,TRK1'); await backgroundMail();
+  assert.equal(shippedMails().length, 1);
+});
+test('bulk import e-mails each newly shipped order and ignores unknown ids', async () => {
+  const a = await orders.placeOrder(1, 500); const b = await orders.placeOrder(1, 700);
+  const n = importShipments(`orderId,trackingCode\r\n${a.id},TRKA\r\n${b.id},TRKB\r\n999,NOPE`); await backgroundMail();
+  assert.equal(n, 3);
+  assert.deepEqual(shippedMails().slice(1).map((m) => [m[1].id, m[1].tracking_code]), [[a.id, 'TRKA'], [b.id, 'TRKB']]);
+});
+test('a bad CSV line still e-mails the rows imported before it', async () => {
+  const o = await orders.placeOrder(1, 300); const before = shippedMails().length;
+  assert.throws(() => importShipments(`orderId,trackingCode\n${o.id},TRKD\nbroken-line`)); await backgroundMail();
+  assert.equal(shippedMails().length, before + 1);
+});
+test('a failed shipping e-mail is retried on the next import of the same file', async () => {
+  const o = await orders.placeOrder(1, 900); const before = shippedMails().length;
+  failSends = true; await orders.markShipped(o.id, 'TRKC'); failSends = false;
+  assert.equal(shippedMails().length, before);
+  importShipments(`orderId,trackingCode\n${o.id},TRKC`); await backgroundMail();
+  assert.equal(shippedMails().length, before + 1);
 });
```
