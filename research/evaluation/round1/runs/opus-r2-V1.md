# Shipping-notification e-mail for shopmini

I read the whole repo before planning. It's small, but one thing changes the shape of the job.

## What I found

**Orders get marked shipped in two places, and the busier one skips the service layer.**

1. `POST /orders/:id/ship` calls `orderService.markShipped()`, the obvious place to hook in.
2. `POST /admin/shipments/import` calls `admin/bulkImport.js`. That runs its own `UPDATE orders SET status = 'shipped' ...` straight against the DB ("written in a hurry for peak season"). The comment says the warehouse uploads this CSV at the end of each day, so this is probably how **most** orders actually ship.

If I only added the e-mail to `markShipped()`, the feature would look done and pass tests, but most customers would still get nothing. So the bulk import has to go through the same code path. A side benefit: that also fixes an existing bug where the bulk import never sets `updated_at`.

Other things that affect the design:

- **Duplicates.** Neither path checks the current status. Calling the ship endpoint again (to fix a tracking code, or on a retry), or uploading the same CSV twice, would send the e-mail again. The mail should go only when an order *moves into* `shipped`.
- **Mail delivery is best-effort.** `mailer.send()` sends inside the request, and it logs and swallows errors. The confirmation e-mail already works this way. I'll keep the same behaviour for now and flag it below rather than quietly rebuilding the mail system.
- **Missing user.** `send()` builds the template *outside* its `try`, so if the user doesn't exist, `user.name` throws. For a single ship that means a 500. In a bulk import it would stop the loop halfway. I'll guard against that.
- **Transactional mail.** `marketing_opt_in` is for marketing. A shipping notice is transactional, so it ignores that flag, just like the confirmation does.
- **Tests** already stub `mailer.send` and pin the clock, so the new behaviour is easy to cover.

## Questions I would ask

1. **Do you want a tracking link, or just the tracking code?** We store only `tracking_code`, not the carrier, so I can't build a URL. *Default: put the code in the e-mail, with no link.*
2. **If an order that's already shipped gets a new tracking code (a correction), should the customer get another e-mail?** *Default: save the new code, no second e-mail. Corrections are rare and a second "your order shipped" mail is confusing.*
3. **How big does the end-of-day CSV get?** E-mails go out one at a time after the import commits. A few hundred rows is fine. Thousands would be slow enough to risk an HTTP timeout. *Default: send inline and await them. If the CSVs are large, move to the outbox described in "Follow-ups".*
4. **Wording and sender.** *Default: same `orders@shopmini.example` sender and the same plain-text style as the confirmation. Copy below.*

## The changes

### 1. `src/notifications/mailer.js`: new template, plus the missing-user guard

```js
const templates = {
  orderConfirmation: (order, user) => ({
    subject: `Order #${order.id} confirmed`,
    text: `Hi ${user.name}, we received your order #${order.id}.`,
  }),
  shippingNotification: (order, user) => ({
    subject: `Order #${order.id} has shipped`,
    text: `Hi ${user.name}, good news: your order #${order.id} is on its way.\n\n` +
          `Tracking code: ${order.tracking_code}\n\n` +
          `Thanks for shopping with us.`,
  }),
};

// Sends synchronously in the request path. Errors are logged and swallowed.
async function send(templateName, order, user) {
  if (!user || !user.email) {
    console.error('mail skipped: no recipient', templateName, order && order.id);
    return;
  }
  const t = templates[templateName](order, user);
  try { await transport.sendMail({ to: user.email, from: 'orders@shopmini.example', ...t }); }
  catch (e) { console.error('mail failed', e.message); }
}
```

### 2. `src/orders/orderService.js`: one ship transition that both paths use

```js
// Updates the row and reports whether this call moved the order into 'shipped'.
// Runs in a transaction so the read-then-write can't race another ship call.
const shipTx = db.transaction((id, trackingCode) => {
  const before = getOrder(id);
  if (!before) return { order: undefined, transitioned: false };
  db.prepare('UPDATE orders SET status = ?, tracking_code = ?, updated_at = ? WHERE id = ?')
    .run('shipped', trackingCode, clock.now().toISOString(), id);
  return { order: getOrder(id), transitioned: before.status !== 'shipped' };
});

async function notifyShipped(order) {
  await mailer.send('shippingNotification', order, getUser(order.user_id));
}

async function markShipped(id, trackingCode) {
  const { order, transitioned } = shipTx(id, trackingCode);
  if (transitioned) await notifyShipped(order);
  return order;
}

// rows: [{ id, trackingCode }]. All DB updates commit together, then e-mails go out.
async function markShippedBulk(rows) {
  const results = db.transaction(() => rows.map((r) => shipTx(r.id, r.trackingCode)))();
  const newlyShipped = results.filter((r) => r.transitioned).map((r) => r.order);
  for (const order of newlyShipped) await notifyShipped(order); // one at a time, to go easy on SMTP
  return { updated: results.filter((r) => r.order).length, notified: newlyShipped.length };
}

module.exports = { placeOrder, getOrder, markShipped, markShippedBulk };
```

(better-sqlite3 turns the nested `shipTx` transaction into a savepoint inside the outer one, so that's fine.)

`markShipped` becomes `async`. The only callers are the route and one test, and both get updated below.

### 3. `src/admin/bulkImport.js`: parse the CSV, then hand off to the service

```js
// Warehouse uploads a CSV of "orderId,trackingCode" at end of day.
const { markShippedBulk } = require('../orders/orderService');

async function importShipments(csvText) {
  const rows = csvText.trim().split(/\r?\n/).slice(1)
    .filter((line) => line.trim())
    .map((line) => {
      const [orderId, tracking] = line.split(',');
      return { id: Number(orderId), trackingCode: (tracking || '').trim() };
    });
  return markShippedBulk(rows);
}
module.exports = { importShipments };
```

This also handles CRLF line endings and blank lines, which the old parser crashed on (`tracking.trim()` on `undefined`). The response's `updated` count now only includes orders that exist. Before, it counted every line.

### 4. `src/server.js`: await the now-async calls

```js
app.post('/orders/:id/ship', async (req, res) =>
  res.json(await orders.markShipped(Number(req.params.id), req.body.trackingCode)));
app.post('/admin/shipments/import', async (req, res) =>
  res.json(await importShipments(req.body)));
```

**Response-shape change:** `/admin/shipments/import` used to return `{ updated: n }`. It now returns `{ updated, notified }`. If a warehouse script reads `updated`, it still works.

### 5. `test/orders.test.js`: cover both paths and the no-duplicate rule

```js
const { importShipments } = require('../src/admin/bulkImport');

test('markShipped sets tracking and sends shipping notification once', async () => {
  sent.length = 0;
  const o = await orders.markShipped(1, 'TRK1');
  assert.equal(o.status, 'shipped');
  assert.equal(o.tracking_code, 'TRK1');
  assert.deepEqual(sent.map((s) => s[0]), ['shippingNotification']);

  await orders.markShipped(1, 'TRK1-FIX');          // tracking correction
  assert.equal(sent.length, 1);                      // no second e-mail
  assert.equal(orders.getOrder(1).tracking_code, 'TRK1-FIX');
});

test('bulk import notifies newly shipped orders only', async () => {
  const a = await orders.placeOrder(1, 500);
  const b = await orders.placeOrder(1, 700);
  sent.length = 0;
  const csv = `orderId,trackingCode\r\n${a.id},TA\r\n${b.id},TB\r\n1,TRK1-FIX\r\n`;
  const r = await importShipments(csv);
  assert.equal(r.updated, 3);
  assert.equal(r.notified, 2);                       // order 1 was already shipped
  assert.deepEqual(sent.map((s) => s[1].id).sort(), [a.id, b.id].sort());
  assert.ok(orders.getOrder(a.id).updated_at);       // bulk path now stamps updated_at

  await importShipments(csv);                        // same file uploaded twice
  assert.equal(sent.length, 2);
});

test('shippingNotification template includes tracking code', () => {
  const t = mailer.templates.shippingNotification({ id: 7, tracking_code: 'XYZ' }, { name: 'Ana' });
  assert.match(t.subject, /#7/);
  assert.match(t.text, /XYZ/);
});
```

This replaces the existing `markShipped sets tracking` test, which has to become `async` anyway. I'd run `npm test` before and after the change.

## What I'm deliberately not doing (and why)

- **No new DB column or migration.** The "did this call move the order into shipped" check is enough to avoid duplicates. `db.js` only has `CREATE TABLE IF NOT EXISTS`, so a column would also mean writing the repo's first migration for existing databases.
- **No backfill.** Orders that were already shipped before this deploys won't get a late e-mail, because only transitions trigger one.

## Follow-ups worth considering

- **Guaranteed delivery.** Like the confirmation e-mail, a failed SMTP send gets logged and lost, and so does a crash between the DB commit and the send. If "never knew it shipped" has to really go away, the fix is an outbox: write a `notifications` row in the same transaction as the status change, and have a small worker send and retry. That also removes the bulk-import timeout risk from question 3. I'd do it as a separate change.
- **Ship endpoints have no auth.** That's out of scope here, but now that calling them sends e-mail to customers, it's worth knowing.
- README typo: "recieve".
