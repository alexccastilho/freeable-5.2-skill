Fixed. The typo appears once, on line 11 of `README.md`:

```diff
--- a/README.md
+++ b/README.md
@@ -8,7 +8,7 @@
     npm start        # http://localhost:3000
     npm test

-Customers recieve an order confirmation e-mail when they place an order.
+Customers receive an order confirmation e-mail when they place an order.

 ## Layout
```

What I checked: I searched the whole repository for `recieve`/`reciev` and this was the only hit. The e-mail template in `src/notifications/mailer.js` already spells it correctly ("we received your order"), so no customer-facing text changes.

Verification: this only touches documentation, so there are no tests to run. `grep -rn "recieve" .` now returns nothing.
