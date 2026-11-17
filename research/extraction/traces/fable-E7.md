# Rename `getUser` to `fetchUser` in shopmini

The fixture is read-only, so nothing has been applied. These are the exact edits I would make: four lines in two files.

## Edits

`src/users/userService.js` (definition and export):

```diff
 const db = require('../db');
-function getUser(id) { return db.prepare('SELECT * FROM users WHERE id = ?').get(id); }
+function fetchUser(id) { return db.prepare('SELECT * FROM users WHERE id = ?').get(id); }
 function getUserByEmail(email) { return db.prepare('SELECT * FROM users WHERE email = ?').get(email); }
-module.exports = { getUser, getUserByEmail };
+module.exports = { fetchUser, getUserByEmail };
```

`src/orders/orderService.js` (import and the one call site):

```diff
-const { getUser } = require('../users/userService');
+const { fetchUser } = require('../users/userService');
```

```diff
-  await mailer.send('orderConfirmation', order, getUser(userId));
+  await mailer.send('orderConfirmation', order, fetchUser(userId));
```

## What I checked

- A search of the whole repo for `getUser` finds only those four occurrences, plus `getUserByEmail`.
- Nothing in `test/`, `README.md`, `src/server.js` or the other modules refers to `getUser`.
- There is no existing `fetchUser` to collide with.
- The function is not accessed by string or by `userService.getUser` anywhere; the only consumer destructures it.

## What I left alone

`getUserByEmail` keeps its name, since you asked for `getUser` only. That leaves the module with one `fetch` and one `get` name. Say if you want it renamed to `fetchUserByEmail` too; nothing else calls it, so it is a two-line change in `userService.js`.

## Verification I would run after applying

1. Search for `\bgetUser\b` across the repo and expect no matches.
2. Run `npm test`. The "placing an order sends confirmation" test goes through `placeOrder`, which calls the renamed function, so it covers the import and the call site.

I have not run the tests: the fixture has no installed dependencies and I could not modify it.

## Process log

1. Bash: listed all files in the fixture (`find`), ran `grep -rn "getUser"` over the fixture, and listed the traces output directory.
2. Bash: printed the contents of `package.json`, `README.md`, `src/admin/bulkImport.js`, `src/clock.js`, `src/db.js`, `src/notifications/mailer.js`, `src/orders/orderService.js`, `src/server.js`, `src/users/userService.js` and `test/orders.test.js`; ran `ls -la` in the fixture root; ran `git status` (not a git repository); ran a case-insensitive `grep -rniE "get_?user|fetch_?user"` over the fixture; listed the traces output directory (empty).
3. Called the advisor tool once.
4. Write: `fable-E7.md`.
