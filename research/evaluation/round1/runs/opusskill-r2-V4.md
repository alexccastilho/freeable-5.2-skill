Fixed in `README.md`, line 11:

```diff
-Customers recieve an order confirmation e-mail when they place an order.
+Customers receive an order confirmation e-mail when they place an order.
```

What I checked: I searched the whole repository for `recieve` and `reciev*`. This is the only occurrence. It does not appear in code, tests, identifiers or e-mail templates, so nothing else needs to change.

Verification: a fresh search for `recieve` returns no matches. It's a docs-only change, so there are no tests to run.
