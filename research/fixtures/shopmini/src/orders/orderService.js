const db = require('../db');
const clock = require('../clock');
const mailer = require('../notifications/mailer');
const { getUser } = require('../users/userService');

async function placeOrder(userId, totalCents) {
  const info = db.prepare('INSERT INTO orders (user_id, status, total_cents, updated_at) VALUES (?, ?, ?, ?)')
    .run(userId, 'placed', totalCents, clock.now().toISOString());
  const order = getOrder(info.lastInsertRowid);
  await mailer.send('orderConfirmation', order, getUser(userId));
  return order;
}
function getOrder(id) { return db.prepare('SELECT * FROM orders WHERE id = ?').get(id); }
function markShipped(id, trackingCode) {
  db.prepare('UPDATE orders SET status = ?, tracking_code = ?, updated_at = ? WHERE id = ?')
    .run('shipped', trackingCode, clock.now().toISOString(), id);
  return getOrder(id);
}
module.exports = { placeOrder, getOrder, markShipped };
