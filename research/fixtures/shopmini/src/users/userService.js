const db = require('../db');
function getUser(id) { return db.prepare('SELECT * FROM users WHERE id = ?').get(id); }
function getUserByEmail(email) { return db.prepare('SELECT * FROM users WHERE email = ?').get(email); }
module.exports = { getUser, getUserByEmail };
