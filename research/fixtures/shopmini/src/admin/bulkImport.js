// Warehouse uploads a CSV of "orderId,trackingCode" at end of day.
// Written in a hurry for peak season; updates rows directly for speed.
const db = require('../db');
function importShipments(csvText) {
  const stmt = db.prepare("UPDATE orders SET status = 'shipped', tracking_code = ? WHERE id = ?");
  let n = 0;
  for (const line of csvText.trim().split('\n').slice(1)) {
    const [orderId, tracking] = line.split(',');
    stmt.run(tracking.trim(), Number(orderId)); n++;
  }
  return n;
}
module.exports = { importShipments };
