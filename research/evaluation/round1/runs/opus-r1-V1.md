# Shipping-notification e-mail for shopmini

I read the whole repo before planning, since it's small. One finding changes the plan: **orders get marked as shipped in two places, and the obvious one is probably not the one that matters most.**

- `POST /orders/:id/ship` → `orderService.markShipped()`. This is the clean path.
- `POST /admin/shipments/import` → `admin/bulkImport.js`. The warehouse uploads a CSV at the end of the day, and this code runs `UPDATE orders SET status='shipped' ...` directly, skipping the service. It doesn't set `updated_at` either.

If I only added the e-mail to `markShipped()`, the tests would pass and the demo would work. But every order shipped through the end-of-day CSV, which is likely most of them, would still send nothing. So the fix has to cover both paths. The cleanest way is to make bulk import go through the same service code.

Other things in the code that shape the design:

- `mailer.send()` logs errors and swallows them, and it returns nothing. We currently can't tell whether a mail went out.
- Mail is sent inline in the request. That's fine for one order. For a CSV of a few hundred rows, sending one mail after another inside the HTTP request is slow and could time out.
- Nothing stops a duplicate send. Re-uploading the same CSV, or calling `/ship` twice, would e-mail the customer again.
- `db.js` uses `CREATE TABLE IF NOT EXISTS`, so a new column added there never reaches an existing `shopmini.db`. It needs a small migration.

## Questions I would ask

1. **Should the CSV bulk import send e-mails too?** Default: **yes**. That's the path the warehouse uses every day, so leaving it out wouldn't fix the complaint.
2. **Do you want a carrier tracking link, or just the tracking code?** The data only holds `tracking_code`, with no carrier. Default: **put the code in the text, no link**. A link can come later once we store the carrier.
3. **If an order is shipped again with a different tracking code (a correction), should the customer get a second e-mail?** Default: **no, only the first shipment triggers one**. Corrections can be a separate feature.
4. **What about orders that are already shipped when this goes live?** Default: **don't e-mail them**. The migration marks them as already notified.
5. **Is there a staging SMTP or a mail catcher to test against?** Default: I verify with unit tests that stub the mailer, and you do one manual send in staging before release.

## Plan

### 1. Schema: record that the notification was sent (`src/db.js`)

Add a `shipping_notified_at TEXT` column to `orders`. Because of `CREATE TABLE IF NOT EXISTS`, also add a guarded migration that runs on startup:

```js
const cols = db.prepare("PRAGMA table_info(orders)").all().map(c => c.name);
if (!cols.includes('shipping_notified_at')) {
  db.exec("ALTER TABLE orders ADD COLUMN shipping_notified_at TEXT");
  // Orders already shipped before this release are treated as notified,
  // so nothing ever e-mails customers about old shipments.
  db.exec("UPDATE orders SET shipping_notified_at = 'pre-migration' WHERE status = 'shipped'");
}
```

This column is the duplicate guard. It's also how support can answer "did we e-mail this customer?"

### 2. Template + success signal (`src/notifications/mailer.js`)

- Add a `shippingNotification` template next to `orderConfirmation`:
  ```js
  shippingNotification: (order, user) => ({
    subject: `Your order #${order.id} has shipped`,
    text: `Hi ${user.name}, good news: your order #${order.id} is on its way.\n` +
          `Tracking code: ${order.tracking_code}`,
  }),
  ```
- Make `send()` return `true` on success and `false` on failure. It still logs and swallows errors, so `placeOrder` keeps working as before. This is a backwards-compatible change: today nobody reads the return value.

### 3. One shipping function used by both paths (`src/orders/orderService.js`)

- Keep `markShipped(id, trackingCode)` as the single place that changes an order to shipped. It also sets `updated_at`, which bulk import currently skips.
- Add `notifyShipped(id)`:
  1. Claim the notification atomically:
     `UPDATE orders SET shipping_notified_at = ? WHERE id = ? AND status = 'shipped' AND shipping_notified_at IS NULL`.
     If `changes === 0`, return without sending: it was already notified, or the order isn't shipped.
  2. Load the order and user, then call `mailer.send('shippingNotification', order, user)`.
  3. If the send returns `false`, set `shipping_notified_at` back to `NULL` so a retry can pick the order up, and log the order id.
  4. If the user is missing or has no e-mail, log it and leave the claim in place. Retrying won't help.
- `markShipped` becomes `async` and awaits `notifyShipped(id)` after the update. The `/orders/:id/ship` route is already a plain handler, so I change it to `async` the same way `POST /orders` works. An e-mail failure never fails the ship request, because the shipping update has already been committed.

### 4. Route bulk import through the service (`src/admin/bulkImport.js`)

- Parse the CSV as today. Ignore blank lines and handle `\r\n`. Right now one malformed line throws halfway through the file, leaving it partly applied.
- Do all status updates inside one `db.transaction(...)`, using the same update as `markShipped`, minus the e-mail. Then send the e-mails **after** the transaction commits, so a rolled-back import never e-mails anyone.
- Send outside the request: the route returns `{ updated: n }` right away, and the e-mails go out one after another in the background (`setImmediate` loop over `notifyShipped(id)`). Because of the duplicate guard, a re-uploaded CSV or a crash in the middle is safe: already-notified orders are skipped.
- Optional, small, and worth doing: `notifyPendingShipments()` sends to every `status='shipped' AND shipping_notified_at IS NULL` row. It covers failed sends and anything shipped by some other route, and can run at startup or from a cron/admin endpoint. I'd add the function now and leave scheduling to you.

### 5. Tests (`test/orders.test.js`)

The existing test already stubs `mailer.send`. I make the stub return `true` and add these tests:

- `markShipped` sends exactly one `shippingNotification` with the tracking code in the e-mail.
- Calling `markShipped` twice sends **one** e-mail.
- Bulk import of a 2-row CSV marks both orders shipped and sends 2 e-mails. Re-importing the same CSV sends 0 more.
- A send that fails (stub returns `false`) leaves `shipping_notified_at` NULL, and a later `notifyShipped` retries it.
- The migration on a DB with an existing shipped order marks that order as notified, and it gets no e-mail.
- The existing `markShipped sets tracking` test is updated to `await`.

Then `npm test`. Before release, one manual end-to-end send in staging: place an order, ship it via `/ship`, ship another via CSV, and check both inboxes.

### 6. Small extras

- README: mention the shipping e-mail next to the confirmation e-mail, and fix the "recieve" typo while I'm there.
- Not doing in this change, but flagging: mail is sent through a bare SMTP transport with no queue. If volume grows, a proper job queue or outbox table is the next step. The `shipping_notified_at` design moves to that without schema changes.

## Files touched

| File | Change |
|---|---|
| `src/db.js` | `shipping_notified_at` column + guarded migration and backfill |
| `src/notifications/mailer.js` | `shippingNotification` template; `send()` returns success boolean |
| `src/orders/orderService.js` | `notifyShipped`, `markShipped` async + notifies, `notifyPendingShipments` |
| `src/admin/bulkImport.js` | goes through the service logic in a transaction; e-mails after commit, in background; sturdier CSV parsing |
| `src/server.js` | `/orders/:id/ship` handler becomes async |
| `test/orders.test.js` | new tests listed above |
| `README.md` | document the new e-mail |

**Main risk:** the bulk-import change alters warehouse behavior. Imports become transactional, so a bad line now rejects the whole file instead of applying it halfway. I think that's better, but it is a behavior change the warehouse team should hear about before it ships.
