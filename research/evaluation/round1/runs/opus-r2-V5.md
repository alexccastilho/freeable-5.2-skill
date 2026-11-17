Caching this page is doable. The catch is the negotiated prices: if you cache whole pages or whole responses, one B2B customer can end up seeing another customer's prices. That would be a data leak, not just a stale page. So my plan caches the parts that are the same for everyone and handles prices separately, either per customer or computed fresh on each request.

## Questions I would ask

1. **Where is the time going right now?** Is it the SQL (N+1 queries, an unindexed filter or sort, `COUNT(*)` for pagination over 50k rows), template rendering, or the price calculation? *Default:* I'd profile first (django-debug-toolbar / `EXPLAIN ANALYZE` on the listing queries). I'd fix obvious query problems before caching, because a cache in front of a bad query just hides it until the cache expires.
2. **How are negotiated prices stored and resolved?** For example a `CustomerPrice(customer, product, price)` table, price-list or tier rules, or discount percentages. *Default:* a per-customer override table, with a fallback to the list price.
3. **Is there a cache backend already?** *Default:* none. I'd add Redis through `django-redis`. Local-memory caches are per-process and can't be invalidated cleanly across workers.
4. **Do anonymous or retail visitors see the listing too, or only logged-in B2B users?** *Default:* both. Anonymous users see list prices.
5. **How stale can a price be after the hourly import?** *Default:* prices must be correct as soon as the import commits. A few minutes of staleness on non-price data (names, images, categories) is fine.

## Plan

**Step 0: Measure and fix the queries (before any caching)**
- Capture a baseline: p50/p95 response time and query count for the listing view, both anonymous and as a B2B user.
- Usual fixes: `select_related`/`prefetch_related` for category, brand and images. Indexes on the filter and sort columns. `.only()` to avoid loading large text fields. Replace exact `COUNT(*)` pagination with keyset pagination or a cached count.
- Load negotiated prices for the products on the current page in **one** query (`CustomerPrice.objects.filter(customer=c, product_id__in=page_ids)`), not one query per product.

**Step 1: Cache the shared, price-free parts**
- Cache the product-ID list for each (filter, sort, page) combination, plus the facet/category counts. Key them by query parameters plus a **catalog version** number.
- Cache the rendered product cards *without the price* (template fragment caching, `{% cache %}` keyed by product id + catalog version). The price is filled in after the fragment comes out of the cache.
- Every user shares these entries, so the hit rate will be high.

**Step 2: Handle prices safely**
- List prices: store them in the cache together with the product data, under the same catalog version.
- Negotiated prices: compute them per request from the batched query in Step 0. With an index on `(customer_id, product_id)` this is usually a few milliseconds for one page of products. Only if profiling shows it's still slow would I add a per-customer cache, keyed by `customer_id` + `price_version`.
- **Never** use `cache_page` or a CDN/proxy cache on this view for logged-in users. If anything upstream caches responses, send `Cache-Control: private` and `Vary: Cookie` for authenticated requests.

**Step 3: Invalidate on import**
- When the hourly import job commits, it bumps `price_version` (and `catalog_version` if product data changed) in Redis, inside `transaction.on_commit`. New keys include the new version, so old entries stop being used and expire on their TTL. This avoids scanning and deleting keys.
- Product edits made in the admin bump `catalog_version` too (via `post_save` signal, or explicitly in the admin save).
- Set a TTL on every entry (say 2 hours) as a safety net in case a version bump is missed.
- If negotiated prices change outside the import (for example a sales rep edits them), bump that customer's version at the time of the edit.

**Step 4: Tests and rollout**
- Tests: (a) customer A never sees customer B's negotiated price, even when B's request warmed the cache; (b) after an import, the listing shows new prices immediately; (c) anonymous users see list prices; (d) the query count stays the same no matter how many products are on the page.
- Put the caching behind a setting or feature flag. Compare against the baseline in staging, then in production. Watch the cache hit rate and p95.

## Risks
- **Price leaks across customers.** This is the main risk. Test (a) above exists to catch it, and Step 2's rule against whole-page caching for logged-in users is what prevents it.
- **Stale prices right after the import.** Prevented by bumping the version on commit rather than relying on TTLs.
- **Cache stampede at the top of the hour,** when every key misses at once after the bump. Optionally, the import job can pre-warm the most popular listing pages after it bumps the version.

If you can share the listing view, the models and the import job, I'll go from this plan to concrete code. Step 0 alone may be most of the speedup.
