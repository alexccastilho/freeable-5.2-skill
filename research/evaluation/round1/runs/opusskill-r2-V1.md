Most orders do not ship through the code path you would expect. The warehouse marks orders shipped with an end-of-day CSV upload (`src/admin/bulkImport.js`), which writes `status = 'shipped'` straight to the database and never goes through `orderService.markShipped`. An e-mail added only to `markShipped` would miss most shipments. So the change routes both paths through one function, and that function sends the e-mail only when an order first becomes shipped. Without that check, a re-uploaded CSV would e-mail every customer on it a second time.

I have not changed the fixture, and none of this code has been run. The part most likely to be wrong is the test's wait on the mail queue (`await mailer.idle()`). It relies on `enqueue` calling `module.exports.send` at send time, so that the test's replacement `send` is the one that runs. Confirm that first when you run it.

## Questions I would ask

1. **Can your SMTP provider take the end-of-day burst?** On a big day the CSV can mark hundreds of orders shipped at once. Default: the e-mails go out one at a time from an in-process queue after the import responds. Nothing is throttled beyond that. If the provider has a per-minute or daily cap below your shipping volume, the queue needs a rate limit, or the sends need to be spread out.
2. **Do you want a carrier tracking link, or only the code?** Default: only the tracking code. The orders table stores no carrier, so the code can't build a link. If all shipments go through one carrier, the link is a one-line template change.
3. **Should a corrected tracking code trigger a second e-mail?** Default: no. Only the first move into `shipped` sends. A correction updates the row quietly, the same as it does today.
4. **Should orders already shipped before this goes live get an e-mail?** Default: no. Only shipments from deploy time onward get one, so deploying causes no flood of e-mails.

Answer first: 1. It is the only one that could make the default harmful. The others change wording or detail only.

Stated assumption: this is a transactional e-mail, so it ignores `users.marketing_opt_in`, the same as the order confirmation does.

## The change

Four files. No new dependencies.

### `src/notifications/mailer.js`: a template and a small serial queue

```js
const templates = {
  orderConfirmation: (order, user) => ({
    subject: `Order #${order.id} confirmed`,
    text: `Hi ${user.name}, we received your order #${order.id}.`,
  }),
  orderShipped: (order, user) => ({
    subject: `Order #${order.id} has shipped`,
    text: `Hi ${user.name}, your order #${order.id} is on its way. Tracking code: ${order.tracking_code}.`,
  }),
};

// ... send() unchanged ...

// Sends one message at a time, outside the request path. In memory only:
// messages still queued when the process stops are lost (see "Found, not touched").
let queue = Promise.resolve();
function enqueue(templateName, order, user) {
  queue = queue
    .then(() => module.exports.send(templateName, order, user))
    .catch((e) => console.error('mail failed', templateName, order.id, e.message));
  return queue;
}

module.exports = { send, enqueue, idle: () => queue, templates };
```

The `.catch` is there because `send` builds the template outside its own `try`. A missing user would otherwise throw and stop every message queued after it.

### `src/orders/orderService.js`: one place where orders become shipped

```js
// The only place an order becomes 'shipped'. E-mails the customer only on the
// first transition, so CSV re-uploads and tracking corrections send nothing.
// better-sqlite3 is synchronous, so the read and the update cannot interleave
// within this process.
function shipOrder(id, trackingCode) {
  const before = getOrder(id);
  if (!before) return false;
  db.prepare('UPDATE orders SET status = ?, tracking_code = ?, updated_at = ? WHERE id = ?')
    .run('shipped', trackingCode, clock.now().toISOString(), id);
  const firstShipment = before.status !== 'shipped';
  if (firstShipment && process.env.SHIPPING_EMAILS !== 'off') {
    mailer.enqueue('orderShipped', getOrder(id), getUser(before.user_id));
  }
  return firstShipment;
}

function markShipped(id, trackingCode) {
  shipOrder(id, trackingCode);
  return getOrder(id);
}

module.exports = { placeOrder, getOrder, markShipped, shipOrder };
```

`markShipped` stays synchronous and returns what it returned before, so the route and the existing test don't change. `SHIPPING_EMAILS=off` is a kill switch that needs only a restart, not a code change.

### `src/admin/bulkImport.js`: use the shared function

```js
// Warehouse uploads a CSV of "orderId,trackingCode" at end of day.
const { shipOrder } = require('../orders/orderService');
function importShipments(csvText) {
  let n = 0;
  for (const line of csvText.trim().split('\n').slice(1)) {
    const [orderId, tracking] = line.split(',');
    shipOrder(Number(orderId), tracking.trim()); n++;
  }
  return n;
}
module.exports = { importShipments };
```

The response stays `{ updated: n }`, with the same meaning as today. The import now also sets `updated_at`, which it used to skip. Each row now does one extra lookup and prepares its statements per call. For an end-of-day file that cost is trivial. If imports reach tens of thousands of rows, move the prepared statements to module level.

### `test/orders.test.js`: add tests

```js
const { importShipments } = require('../src/admin/bulkImport');

test('first shipment sends one shipped e-mail; a tracking correction sends none', async () => {
  const o = await orders.placeOrder(1, 500);
  sent.length = 0;
  orders.markShipped(o.id, 'TRK-A');
  orders.markShipped(o.id, 'TRK-B');
  await mailer.idle();
  assert.equal(sent.length, 1);
  assert.equal(sent[0][0], 'orderShipped');
  assert.equal(sent[0][1].tracking_code, 'TRK-A');
  assert.equal(orders.getOrder(o.id).tracking_code, 'TRK-B');
});

test('CSV import e-mails newly shipped orders only, and a re-upload sends nothing', async () => {
  const a = await orders.placeOrder(1, 100);
  const b = await orders.placeOrder(1, 200);
  orders.markShipped(b.id, 'OLD');
  await mailer.idle(); sent.length = 0;
  const csv = `orderId,trackingCode\n${a.id},TRK-1\n${b.id},TRK-2\n`;
  importShipments(csv);
  await mailer.idle();
  assert.deepEqual(sent.map((s) => s[1].id), [a.id]);
  importShipments(csv);
  await mailer.idle();
  assert.equal(sent.length, 1);
});
```

The existing test replaces `mailer.send` before anything is sent. `enqueue` looks `send` up at send time, so these tests catch the replacement, not real SMTP.

## Verification

1. Run `npm test`. All four tests should pass. I could not run them, because the fixture has no installed dependencies and is read-only.
2. Local end-to-end check: point `SMTP_HOST` at a local mail catcher. Place three orders, ship one with `POST /orders/:id/ship`, then post a CSV covering all three to `/admin/shipments/import`. Expect exactly three shipped e-mails in total: one from the single ship and two from the CSV. Post the same CSV again and expect none.
3. Production gate: watch the first end-of-day import after deploy. Compare the `mail failed` log lines with that day's number of newly shipped orders. If more than 5% fail, or any customer reports a duplicate, set `SHIPPING_EMAILS=off` and restart, then investigate. Orders keep shipping normally while e-mail is off.

## Found, not touched

- **No authentication on `/orders/:id/ship` or `/admin/shipments/import`.** This change raises the stakes, because anyone who can reach the API can now make it e-mail your customers. This is the most important item on this list, and it deserves its own change.
- **The import stops halfway on a malformed line.** A line without a comma makes `tracking.trim()` throw. The rows before it stay shipped (and are now e-mailed), and the rows after it are skipped. There is no transaction and no per-line error report.
- **Queued e-mails are lost if the process restarts mid-send, and failures are logged then dropped.** A durable outbox table with retries is the next step if a missed e-mail matters.
- **`express.text()` has a default body limit,** which I recall as 100 kB (check the Express version you have installed). A large end-of-day CSV may be rejected with a 413 error before any of this code runs.
- **The order confirmation is still awaited inside `POST /orders`,** so a slow SMTP server slows down placing orders.
- **README typo:** "recieve".
