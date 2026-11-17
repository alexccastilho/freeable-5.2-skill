Before I add anything, one point decides the design: **logged-in B2B customers see their own negotiated prices.** A plain page cache (`cache_page`, a CDN, or Varnish keyed only on URL) would show one customer's prices to another. That's a data leak, not just a stale-data bug. So the plan below caches the parts everyone shares, keys anything price-related by price context, and ties invalidation to the hourly import.

## Questions I would ask

1. **Where is the time going?** Have you profiled it (django-debug-toolbar, `EXPLAIN ANALYZE`, APM)? On a 50k-row listing the usual causes are N+1 queries, `COUNT(*)` for pagination, missing indexes on filter/sort columns, or template rendering. Caching on top of an N+1 hides the problem without fixing it.
   *Default:* I profile first and fix obvious query problems (`select_related`/`prefetch_related`, indexes, cheaper pagination count) in the same change, before adding caching.
2. **How are negotiated prices modeled?** One price list per customer, or price groups/tiers shared by many customers? Are they also changed by the hourly import, or edited in the admin?
   *Default:* customers map to a price list / price group (`price_list_id`). If every customer is truly unique, the price layer is keyed per customer instead, which still works but hits the cache less often.
3. **What cache backend do you have?** Is Redis or Memcached already running, and how many app servers are there?
   *Default:* Redis via `django.core.cache` (Django's built-in Redis backend). The per-process locmem cache doesn't work across several workers and can't be invalidated centrally.
4. **How fresh must prices be?** Is "up to an hour old, refreshed right after the import" acceptable? Are there manual price edits between imports that must show up immediately?
   *Default:* prices change only through the import, plus a signal that invalidates the cache on manual admin edits.
5. **Is stock/availability on the page,** and does it change more often than hourly?
   *Default:* yes, so it is left out of the long-lived cache (see below).

## Plan (under those defaults)

### 0. Measure first (small, but don't skip)
- Record a baseline: p50/p95 response time and query count for the listing, anonymous vs. logged-in B2B.
- Fix query problems I find: N+1s, missing composite indexes for common filters/sorts, and an exact `COUNT(*)` over 50k rows on every page view (cache the count, or use estimated counts or keyset pagination).

### 1. Split the page into shared and price-specific data
- **Shared across all users:** product IDs for a given filter/sort/page combination, and product display data (name, image, attributes, list price).
- **Specific to a price context:** the price shown per product. Price context = `"public"` for anonymous/retail users, or `price_list_id` for B2B users.

### 2. Cache layers
| Layer | Key | Content | TTL / invalidation |
|---|---|---|---|
| Listing query result | `plist:v{gen}:{hash(filters, sort, page)}` | ordered product IDs + total count | `catalog_gen` bump on import; TTL ~1h as a backstop |
| Product cards | `pcard:v{gen}:{product_id}` | serialized display data (no customer price) | same; fetched with `cache.get_many` |
| Prices | `price:v{gen}:{price_ctx}:{product_id}` (or one entry per ctx+page) | resolved price | `price_gen` bump on import and on admin price edits |

- Use a **generation counter** (`catalog_gen`, `price_gen` stored in the cache) in the keys instead of deleting keys one by one. The import finishes and bumps the counter, all old keys become unreachable and expire naturally. There's no pattern-delete across 50k keys and no race with readers.
- The view builds the page from: IDs (cached), cards via `get_many` (missing ones loaded in one query and written back), prices for the current context via `get_many` (missing ones resolved in one query and written back).
- **Template fragment caching** (`{% cache %}`) can wrap the price-free product-card HTML using the same generation in the key.

### 3. Full-page / HTTP caching, for anonymous users only
- For logged-out traffic, the whole rendered page can be cached (per-view cache or CDN) with the generation counter in the key, or a short TTL.
- For authenticated responses, send `Cache-Control: private` (or `no-store`) and `Vary: Cookie` so no shared proxy or CDN ever stores a B2B page. I'd add a test that asserts these headers.

### 4. Tie invalidation to the import job
- At the end of a successful hourly import (after the transaction commits, using `transaction.on_commit`), bump `price_gen` (and `catalog_gen` if product data changed).
- Optional: warm the cache for the most-visited listing pages and the largest price lists right after the bump, so the first visitors after the import don't all hit cold-cache queries at once.
- Add a `post_save`/`post_delete` signal on the price/product models for manual admin edits.

### 5. Protect against stampedes and failures
- When the generation bumps, many requests miss the cache at once. Use a short lock (`cache.add`) so only one request rebuilds a given key, or rely on warm-up plus a TTL with jitter.
- Cache errors must fall back to the database (Django's Redis backend can be configured to ignore exceptions), so a Redis outage makes the page slower but never breaks it.

### 6. Tests and verification
- **Correctness (most important):** customer A and customer B with different negotiated prices request the same listing in sequence, and each sees only their own price. Anonymous users never see B2B prices, and B2B users never see a stale public-price page.
- An import run bumps the generation, so the next request shows new prices.
- Header test: authenticated responses are `private` and never cached by shared caches.
- Performance: compare against the step-0 baseline (query count per request, p95 latency) for anonymous users, warm B2B users, and right after an import.

### What I deliberately won't do
- `@cache_page` on the listing view for all users, because it leaks negotiated prices.
- Caching the price-free cards with a long TTL and no invalidation, because hourly price/product changes would appear late.
- Caching stock levels in these layers, if stock changes more often than hourly. Load stock separately or with a short TTL.

If you can confirm (or correct) the defaults above, especially how negotiated prices are modeled and whether Redis is available, I'll start with step 0 and send the profiling results before writing the caching code.
