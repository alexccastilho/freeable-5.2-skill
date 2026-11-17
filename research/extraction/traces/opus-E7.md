# Rename `getUser` to `fetchUser` in shopmini

I searched the whole repo for `getUser`. It appears in **two files, 4 occurrences** (not counting `getUserByEmail`, which is a different function):

- `src/users/userService.js`: the definition (line 2) and the export (line 4)
- `src/orders/orderService.js`: the import (line 4) and the call in `placeOrder` (line 10)

There are no other references: not in `src/server.js`, `src/admin/bulkImport.js`, `src/notifications/mailer.js`, `test/orders.test.js` or `README.md`. There are no dynamic or string-based references either (for example `userService['getUser']`). The package is an app (`main: src/server.js`), not a published library, so there are no external callers to keep compatible.

## Questions I would ask

1. **Should `getUserByEmail` be renamed to `fetchUserByEmail` for consistency?** Default: no. You asked for `getUser` only, so I leave `getUserByEmail` unchanged and mention it here.
2. **Keep a deprecated `getUser` alias for compatibility?** Default: no. All callers are inside this repo and get updated in the same change.

## Edits

**`src/users/userService.js`**

```diff
 const db = require('../db');
-function getUser(id) { return db.prepare('SELECT * FROM users WHERE id = ?').get(id); }
+function fetchUser(id) { return db.prepare('SELECT * FROM users WHERE id = ?').get(id); }
 function getUserByEmail(email) { return db.prepare('SELECT * FROM users WHERE email = ?').get(email); }
-module.exports = { getUser, getUserByEmail };
+module.exports = { fetchUser, getUserByEmail };
```

**`src/orders/orderService.js`**

```diff
 const mailer = require('../notifications/mailer');
-const { getUser } = require('../users/userService');
+const { fetchUser } = require('../users/userService');
 
 async function placeOrder(userId, totalCents) {
   const info = db.prepare('INSERT INTO orders (user_id, status, total_cents, updated_at) VALUES (?, ?, ?, ?)')
     .run(userId, 'placed', totalCents, clock.now().toISOString());
   const order = getOrder(info.lastInsertRowid);
-  await mailer.send('orderConfirmation', order, getUser(userId));
+  await mailer.send('orderConfirmation', order, fetchUser(userId));
   return order;
 }
```

I would make these as exact-match edits on the whole word `getUser`, not a blind find-and-replace, which would also rewrite `getUserByEmail` to `fetchUserByEmail`.

## Verification

1. Re-grep to confirm nothing is left: `grep -rnw "getUser" .` should return nothing, and `grep -rn "fetchUser" .` should show the 4 new occurrences.
2. Run the tests: `npm test` (`node --test test/`). `test/orders.test.js` "placing an order sends confirmation" exercises `placeOrder`, so it calls `fetchUser` through the import. A broken import would show up there as `fetchUser is not a function`.
3. Optional smoke test: `node -e "require('./src/server')"` to confirm the modules load.

Note: shopmini is not a git repository in this checkout, so there's no commit step. Normally I'd commit this as `refactor: rename getUser to fetchUser`.

(I wasn't allowed to modify this repo, so the edits above are exactly what I would apply. I haven't applied them or run the tests.)

## Process log

1. Bash: `find . -type f -not -path "./.git/*"` in the shopmini fixture (listed 10 files) and `grep -rn "getUser" . --exclude-dir=.git`.
2. Bash: read `package.json`, `README.md`, `src/users/userService.js`, `src/orders/orderService.js`, `test/orders.test.js`, `src/admin/bulkImport.js`, `src/server.js` with `cat`; ran `grep -rni "user" . -l`; `ls -a`; `git log --oneline -3` (result: not a git repository).
3. Bash: read `src/notifications/mailer.js` and `src/db.js` with `cat`; created/listed the traces output directory.
4. Wrote this file.
