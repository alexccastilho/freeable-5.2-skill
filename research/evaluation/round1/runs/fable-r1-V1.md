I couldn't edit the repo, so below are the exact edits I would make. None of it has been run.

The main finding: orders become "shipped" in two places, and the one the warehouse uses daily (`src/admin/bulkImport.js`, the end-of-day CSV) writes to the `orders` table directly and bypasses `orderService`. Adding the e-mail only to `markShipped` would leave most customers still uninformed, so both paths go through one function.

## Behaviour after the change

- **When it sends:** a customer gets one "your order has shipped" e-mail, with the tracking code, the first time an order becomes `shipped`, whether via `POST /orders/:id/ship` or the CSV import.
- **No duplicates:** re-uploading the same CSV or re-shipping an order updates the tracking code but does not e-mail again.
- **Single ship route:** it waits for the e-mail before responding, as order placement does today.
- **CSV import:** it responds as soon as the rows are updated and sends the e-mails in the background, so a few hundred SMTP calls don't hold the request open.
- **Already shipped orders:** nothing is sent for them; there is no backfill.
- **Opt-in:** `marketing_opt_in` is ignored, because this is a transactional e-mail.

## Edits

### `src/notifications/mailer.js`: add the template

```js
const templates = {
  orderConfirmation: (order, user) => ({
    subject: `Order #${order.id} confirmed`,
    text: `Hi ${user.name}, we received your order #${order.id}.`,
  }),
  orderShipped: (order, user) => ({
    subject: `Order #${order.id} has shipped`,
    text: `Hi ${user.name}, your order #${order.id} is on its way.`
      + (order.tracking_code ? ` Tracking code: ${order.tracking_code}.` : ''),
  }),
};
```

### `src/orders/orderService.js`: one place that ships and notifies

Replace `markShipped` and the exports with:

```js
// DB only. Reports whether this call moved the order to 'shipped' for the first time.
function applyShipment(id, trackingCode) {
  const before = getOrder(id);
  if (!before) return { order: undefined, newlyShipped: false };
  db.prepare('UPDATE orders SET status = ?, tracking_code = ?, updated_at = ? WHERE id = ?')
    .run('shipped', trackingCode, clock.now().toISOString(), id);
  return { order: getOrder(id), newlyShipped: before.status !== 'shipped' };
}
async function notifyShipped(order) {
  try {
    const user = getUser(order.user_id);
    if (!user) { console.error(`order ${order.id}: no user, shipping e-mail not sent`); return; }
    await mailer.send('orderShipped', order, user);
  } catch (e) { console.error(`order ${order.id}: shipping e-mail failed`, e.message); }
}
async function markShipped(id, trackingCode) {
  const { order, newlyShipped } = applyShipment(id, trackingCode);
  if (newlyShipped) await notifyShipped(order);
  return order;
}
module.exports = { placeOrder, getOrder, markShipped, applyShipment, notifyShipped };
```

`markShipped` is now async, so its two callers change (below).

### `src/admin/bulkImport.js`: go through the service

```js
// Warehouse uploads a CSV of "orderId,trackingCode" at end of day.
const orders = require('../orders/orderService');
function importShipments(csvText) {
  const newlyShipped = [];
  let updated = 0, skipped = 0;
  for (const line of csvText.trim().split('\n').slice(1)) {
    const [orderId, tracking] = line.split(',');
    if (!orderId || !tracking || !tracking.trim()) { skipped++; continue; }
    const r = orders.applyShipment(Number(orderId), tracking.trim());
    if (!r.order) { skipped++; continue; }
    updated++;
    if (r.newlyShipped) newlyShipped.push(r.order);
  }
  // E-mails go out after the response; one at a time to stay gentle on SMTP.
  const notified = (async () => { for (const o of newlyShipped) await orders.notifyShipped(o); })();
  return { updated, skipped, notified };
}
module.exports = { importShipments };
```

Two side effects of this rewrite change what the import reports:

- **Malformed lines:** today a bad line throws halfway through the file. With e-mails that would be worse: the rows before it are already shipped, never e-mailed, and a re-upload wouldn't e-mail them either. Bad lines are now skipped and counted.
- **Unknown order ids:** `updated` used to count every line, including ids that don't exist. It now counts real updates, and the response gains a `skipped` field.

The import also now sets `updated_at`, which it didn't before.

### `src/server.js`: the two routes

```js
app.post('/orders/:id/ship', async (req, res) => res.json(await orders.markShipped(Number(req.params.id), req.body.trackingCode)));
app.post('/admin/shipments/import', (req, res) => {
  const { updated, skipped } = importShipments(req.body);
  res.json({ updated, skipped });
});
```

### `test/orders.test.js`: replace the existing ship test, add two

Add `const { importShipments } = require('../src/admin/bulkImport');` after the mailer stub. The existing `markShipped` test needs `async`/`await`; it becomes the first test below.

```js
test('markShipped sets tracking and sends shipping e-mail once', async () => {
  const o = await orders.markShipped(1, 'TRK1');
  assert.equal(o.status, 'shipped');
  assert.equal(sent.filter(s => s[0] === 'orderShipped').length, 1);
  await orders.markShipped(1, 'TRK1b');
  assert.equal(sent.filter(s => s[0] === 'orderShipped').length, 1);
});
test('bulk import e-mails newly shipped orders only', async () => {
  const a = await orders.placeOrder(1, 500);
  const before = sent.filter(s => s[0] === 'orderShipped').length;
  const r = importShipments(`orderId,trackingCode\n1,TRK1c\n${a.id},TRK2\n999,NOPE\nbroken\n`);
  await r.notified;
  assert.equal(r.updated, 2); assert.equal(r.skipped, 2);
  const shipped = sent.filter(s => s[0] === 'orderShipped');
  assert.equal(shipped.length, before + 1);
  assert.equal(shipped.at(-1)[1].tracking_code, 'TRK2');
});
test('orderShipped template includes tracking code', () => {
  const t = mailer.templates.orderShipped({ id: 7, tracking_code: 'ABC' }, { name: 'Ana' });
  assert.match(t.text, /ABC/);
});
```

### `README.md`

Change the sentence to: "Customers receive an order confirmation e-mail when they place an order and a shipping e-mail with the tracking code when it ships."

## Known gap

`mailer.send` logs and swallows SMTP errors, and the import sends in the background. A failed send, or a process restart mid-batch, loses those e-mails with only a log line, and a re-upload won't resend them. Order confirmations have the same weakness today.

Closing it means a `shipping_email_sent_at` column plus a small retry job. I left that out to keep this change small; say if you want it included.

## Questions I would ask

1. **Is there a carrier or tracking URL to link to?** The data only has a bare tracking code. Default: the e-mail shows the code as text, with no link.
2. **Should a corrected tracking code trigger a second e-mail?** Default: no, one e-mail per order.
3. **Do you have preferred wording or a non-English audience?** Default: the short English text above, from `orders@shopmini.example`, matching the confirmation e-mail.
4. **Does anything else consume the import endpoint's response?** It now returns `{ updated, skipped }`, with `updated` counting only real orders. Default: only the warehouse tool reads it and the extra field is harmless.
