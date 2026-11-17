const test = require('node:test');
const assert = require('node:assert');
process.env.DB_PATH = ':memory:';
const clock = require('../src/clock');
const mailer = require('../src/notifications/mailer');
const db = require('../src/db');
const orders = require('../src/orders/orderService');
const sent = []; mailer.send = async (...a) => { sent.push(a); };
clock._setNow(() => new Date('2026-01-01T00:00:00Z'));
db.prepare("INSERT INTO users (id, email, name) VALUES (1, 'a@example.com', 'Ana')").run();
test('placing an order sends confirmation', async () => {
  const o = await orders.placeOrder(1, 1000);
  assert.equal(o.status, 'placed'); assert.equal(sent[0][0], 'orderConfirmation');
});
test('markShipped sets tracking', () => {
  const o = orders.markShipped(1, 'TRK1'); assert.equal(o.status, 'shipped');
});
