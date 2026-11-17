const Database = require('better-sqlite3');
const db = new Database(process.env.DB_PATH || 'shopmini.db');
db.exec(`
  CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, email TEXT UNIQUE, name TEXT, marketing_opt_in INTEGER DEFAULT 0);
  CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id), status TEXT, total_cents INTEGER, tracking_code TEXT, updated_at TEXT);
`);
module.exports = db;
