The biggest risk here is that B2B customers get negotiated prices that are theirs alone, and the cache must never serve one customer's prices to another. So the plan never caches whole pages or HTTP responses for anyone who is logged in. Instead it splits the listing in two:
- **The catalogue part.** Which products match, in what order, and their names, images and stock. This is the same for everyone, so it's cached.
- **The prices.** Looked up per request, for just the products on the page.

The cache is cleared by a version number that the hourly import bumps once its prices are committed. That way nobody sees the old prices for an hour after an import.

The second thing that shapes the plan: "slow" hasn't been measured yet. With 50k products, a listing is often slow because of one fixable query (N+1 queries per product, a missing index, a `COUNT(*)` for pagination). Caching would only hide that, and it would come back on every cache miss and after every import. So step 1 measures first.

I haven't seen your code or your cache setup. The plan rests on the defaults below, and nothing in it has been run.

## Questions I would ask

**Q1. How long after an import can the old prices still show?** Default: no longer than the import itself takes. The cache keys carry a version number that the import bumps after it commits. If up to an hour is fine, a plain one-hour TTL is enough, and the import job doesn't change.

**Q2. Who sees which price, and does a negotiated price depend on anything besides (customer, product), such as quantity breaks or contract dates?** Default: there is one negotiated price per (customer, product), and everyone else sees the list price. If prices also depend on quantity or date, the price lookup takes those as inputs, and prices are never cached beyond one request.

**Q3. Which requests are slow, for whom, and by how much?** Default: unknown, so step 1 measures anonymous and B2B requests separately. If only B2B requests are slow, the negotiated-price lookup is the cost, and caching the catalogue won't help much.

**Q4. Does anything besides the hourly import change prices or products (admin edits, contract changes)?** Default: yes. A save signal on those models also bumps the version.

**Q5. Is there a shared cache (Redis or Memcached), and is there more than one app process?** Default: Redis, several processes. If it's only `LocMemCache`, each process holds its own copy and the version bump won't reach the others, so a shared backend comes first.

Answer first: **Q3 and Q2**. Q3 may show that a query fix is enough. Q2 decides how much of the price data can safely be cached at all.

## Plan

**Step 1. Measure (half a day).**
- Count queries and time for the listing, for an anonymous user and for a B2B user, at a typical page and filter, using django-debug-toolbar or silk in staging.
- Run `EXPLAIN ANALYZE` on the slowest statements.
- Check `pg_stat_statements` in production for the listing queries.

Gate: if one query fix (`select_related`/`prefetch_related`, an index, replacing the exact count) gets the page to an acceptable p95, ship that first. Caching then applies only to the part that is still slow, and it's dropped if nothing is.

**Step 2. Cache the catalogue part.**
- Key: `listing:v{catalog_version}:{hash(filters, sort, page)}`.
- Value: the product IDs for that page, plus the rendered price-free product cards, or the serialised card data.
- TTL of 2 hours as a safety net.
- Use a cache key normalised from the parsed filter values, not the raw query string. Otherwise junk parameters create endless distinct keys (overload).

Failure modes:
- *Many requests miss at once after a version bump:* at the end of the import, warm the first 2 to 3 pages of the top categories. The rest fill on demand, and each miss costs only what one request costs today.
- *Cache down:* reads fall back to the database instead of erroring. Django's built-in `RedisCache` raises errors by default, and `django-redis` has an `IGNORE_EXCEPTIONS` option. I'd check which backend you use and wrap the cache calls if needed. This is from memory.
- *Cache memory:* keys are bounded by TTL and LRU eviction (`maxmemory-policy allkeys-lru` on Redis).

**Step 3. Prices per request.**
- Anonymous users and those without a contract: the list price, which comes with the product data and can be cached under the same version.
- B2B: one query for the negotiated prices of the 20 to 50 products on the page (`WHERE customer_id = %s AND product_id IN (...)`), backed by an index on `(customer_id, product_id)`.
- Merge the prices into the cached cards at render time.
- Only if step 1 shows this query is slow: cache a per-customer price map, keyed `prices:v{price_version}:{customer_id}`.

Leak protection:
- No `cache_page` or full-page cache on this view.
- `Cache-Control: private` for logged-in responses, so a CDN or proxy can't store them.
- A test asserts that customers A and B, requesting the same URL, see their own different prices, and that anonymous users see list prices.

**Step 4. Invalidation in the import.**
- The import bumps `catalog_version`/`price_version` with `cache.incr`, after its transaction commits (`transaction.on_commit`).
- *Partial failure:* an import that rolls back never bumps the version, so the cache keeps serving the last good prices.
- *Overlapping imports:* the increment is atomic, so both runs bump it and nothing is lost.
- *Other writers:* the Q4 signals bump the version too.

**Step 5. Roll out.**
- Put caching behind a setting (`LISTING_CACHE_ENABLED`).
- Turn it on in staging, then in production.
- Log hit rate and p95 per user type for a week.

Verification:
- The leak test from step 3.
- After a test import, a listing shows the new price on its next request.
- p95 is compared with step 1's baseline.

Revert rule: a wrong price seen by a customer, or no p95 improvement, means turning the setting off.

## Found, not touched
- If anonymous users only ever see list prices, their pages could be cached whole as well. That's left out for now and can come later once the split cache is proven.
