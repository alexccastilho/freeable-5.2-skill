# Caching the product listing page

I have not seen this codebase (the only repo I have access to, shopmini, is a Node/Express app with no products), so what follows is a plan based on your description, not on your code. Nothing has been measured or changed yet.

## The one thing that must not go wrong

Logged-in B2B customers see negotiated prices. Any cache that stores a rendered page or a price under a key that does not include the customer will eventually show customer A's prices to customer B. That is a commercial leak, not a staleness bug. So the design rule is:

- **The shared cache holds only data that is identical for everyone** (product name, SKU, image, category, list price).
- **Customer-specific prices are either fetched per request or cached under a key that includes the customer ID.**
- No `cache_page` and no CDN or reverse-proxy caching on the logged-in listing. Responses for logged-in users go out with `Cache-Control: private`.

## Step 0: find out why it is slow (about half a day, before any caching)

50k rows is small for Postgres; a paginated listing should take a few milliseconds. A slow one usually has a cause that caching would only hide, and that would come back on every cache miss:

- N+1 queries (a price, image or category lookup per product row). The fix is `select_related` / `prefetch_related`, and fetching all negotiated prices for the page in one query.
- No pagination, or deep `OFFSET` pagination.
- `COUNT(*)` for the paginator over a filtered or joined queryset.
- Missing indexes on the filter and sort columns, or on `(customer_id, product_id)` in the negotiated-price table.
- Template rendering of a very large page.

I would use Django Debug Toolbar or `django-silk` on the page plus `EXPLAIN ANALYZE` on the top queries, and record query count and p50/p95 response time as the baseline. If this step alone gets the page to an acceptable time, I would tell you so and propose a smaller caching layer or none.

## Step 1: cache design

**Backend.** Redis through Django's built-in `django.core.cache.backends.redis.RedisCache`. Local-memory cache is not usable with more than one worker process, because invalidation would not reach them all.

**Invalidation: a catalog version number, not per-key deletes.** One Redis key, `catalog:version`. Every cache key includes it. The hourly import increments it as its last step, after its transaction commits (`transaction.on_commit`). All old entries become unreachable at once and expire by TTL. This avoids tracking which listing pages contain which products. Admin edits to a product bump the same version through a `post_save` signal or the admin save hook.

**Layer A, shared catalog data.** Key: `plist:v{version}:{category}:{filters hash}:{sort}:{page}`. Value: the product IDs for that page, the display fields, and the total count. TTL 2 hours as a safety net: longer than the import interval, so the version bump does the invalidating and the TTL only cleans up.

**Layer B, prices.**
- Anonymous visitors and customers without negotiated prices: the list price is part of layer A.
- B2B customers: for the 20 to 50 product IDs on the page, one indexed query, `WHERE customer_id = %s AND product_id IN (...)`. This is cheap, and I would start by **not caching it at all**. If measurement shows it still matters, cache it under `cprice:v{version}:{customer_id}:{page key}` with a short TTL.

**Rendering.** The view merges A and B and renders. If template rendering turns out to be a significant share of the time, cache the price-independent part of each product card with `{% cache %}`, keyed by product ID and version, and leave the price outside the cached fragment.

**Stampede after the hourly bump.** Right after the import, every key misses at once. Two inexpensive mitigations: the import job warms the most-visited listing pages (first pages of the top categories) after bumping the version, and cache fills take a short lock (`cache.add` as a mutex) so that one request computes while the others wait briefly or take the uncached path.

**Failure behaviour.** If Redis is unreachable, the view falls back to the database and logs it. The page gets slow, not broken.

## Step 2: tests

- Customer A and customer B request the same listing in sequence, and each sees their own prices. This test guards against the leak, and it runs against the real cache backend, not a dummy one.
- An anonymous request after a logged-in request shows list prices, and the reverse.
- After the import bumps the version, the next request shows the new prices.
- A negotiated price changed outside the import is visible on the next request. This holds by construction while layer B is uncached, and needs an explicit bump if it is cached.
- Query count on a warm listing page is bounded (`assertNumQueries`).
- With the cache backend down, the page still renders.

## Step 3: rollout

- Behind a settings flag, so it can be turned off without a deploy.
- Staging first, with the import job run against it at least once.
- Compare p50/p95 and query count with the Step 0 baseline, and watch the hit rate and Redis memory for the first few import cycles.

## Questions I would ask

1. **Can I see the listing view, its template, the product and price models, and the import job?** Default: proceed with the design above and adjust once I have read them.
2. **How slow is it, and what is the target?** Default: under 300 ms server time at p95 for a warm page, under 1 s cold.
3. **Is it slow for everyone or mainly for logged-in B2B customers?** Default: both. If it is only B2B, the negotiated-price lookup is the first suspect and layer A matters less.
4. **Is Redis or Memcached already deployed?** Default: Redis is available or may be added. If neither is possible, the fallback is Django's database cache, which helps less.
5. **Do negotiated prices change only in the hourly import, or can account managers edit them at any time?** Default: at any time, which is another reason to keep layer B uncached at first.
6. **How stale may prices be?** Default: list prices are correct within seconds of the import finishing; negotiated prices are never stale.
7. **Is there a CDN or reverse proxy (Cloudflare, Varnish, nginx cache) in front of the app?** Default: yes, so I set `Cache-Control: private` on logged-in responses and verify it. If one already caches this page, that needs checking today, independently of this work.
8. **Does the listing vary per customer in any other way: product visibility, assortments, stock by warehouse, currency, language?** Default: only price varies. If visibility varies, the ID list in layer A needs the customer group in its key.
9. **Is it a server-rendered template or a DRF API behind a frontend?** Default: a server-rendered template. The design is the same for an API, minus fragment caching.

## What you get at the end

A before/after measurement, the caching code behind a flag, the tests above, the one-line change to the import job, and a short note on how to invalidate manually (`cache.incr("catalog:version")`).
