# Caching the product listing page

The hard part is not the caching. It is that B2B customers see negotiated prices, so the usual quick fix, caching the whole page or view, will sooner or later show one customer another customer's price. That is a data leak, not a slow page. So the design splits the page in two. The catalogue part (products, names, list prices, filters, counts) is the same for everyone, changes once an hour, and is cached once and shared. The customer price part is never served from a shared entry: it is either fetched per request in a single query or cached under a key that includes the customer. The hourly import gives a clean invalidation point: the import job bumps a version number when it finishes.

**Cheaper path, worth 30 minutes first:** at 50k products, a slow listing page in Django is very often an N+1 query (a negotiated-price lookup or a related object per product row), a `COUNT(*)` on a filtered queryset for pagination, or a missing index on the filter/sort columns. Fixing those usually beats caching and leaves no stale data. Cost: one profiling session with django-debug-toolbar or `connection.queries` on the listing view as a logged-in B2B user. It is the right choice if the page runs more than a handful of queries or one query dominates. That is question 1 below, and the plan starts with that measurement either way. I plan what you asked below.

**Not seen:** I have not seen your code, models, cache backend or traffic. The model and setting names below (`Product`, `CustomerPrice`, `CATALOG_VERSION`) are placeholders for whatever you have, and none of this code has been run.

## Questions I would ask

1. **Do you want caching specifically, or a faster page by whatever works?** Default: caching, as requested, preceded by the step 1 profile. If step 1 finds an N+1 or a missing index, I fix that first and only add caching if the page is still slow.
2. **How are negotiated prices stored: a row per customer per product, a per-customer discount rule, or price lists shared by groups of customers?** Default: a `CustomerPrice(customer, product, price)` table with an override falling back to list price. If customers share price lists, the cache key uses the price-list ID instead of the customer ID, and the hit rate goes up a lot.
3. **Can anything besides the hourly import change a price or a product (admin edits, a per-customer negotiation tool)?** Default: yes, admin edits happen. They bump the same version through a `post_save` signal, so an edit shows up immediately, not up to an hour later.
4. **Which cache backend is available?** Default: Redis via Django's built-in `RedisCache` (Django 4.0+). Local-memory cache is not used for this, because each worker would hold its own copy and invalidation would not reach the others.
5. **Do anonymous visitors see the listing, and with what prices?** Default: yes, with list prices. They get the shared, fully cached page.

Answer first: 1 and 2. Question 1 may turn this into a query fix with no cache at all; question 2 decides the cache key for the price part and therefore how much the cache helps.

## Plan

**Step 1. Measure (before any change).** Profile the listing view twice: once anonymous, once as a B2B customer with negotiated prices. Record the query count, the slowest queries with `EXPLAIN ANALYZE`, and total server time. Check: you have a baseline number to compare every later step against. If there is an N+1 on prices, rewrite it as one query for the page's product IDs (`CustomerPrice.objects.filter(customer=c, product_id__in=page_ids)`) or `prefetch_related` with a filtered `Prefetch`, and re-measure before going further.

**Step 2. A catalogue version number.** Add one cache key, `catalog:version`, holding an integer. The import job increments it as its last action, after its transaction commits (`transaction.on_commit`). Bumping before commit would let a request cache the old data under the new version. A `post_save`/`post_delete` signal on `Product` and on the price model does the same for admin edits. Nothing is ever deleted from the cache; old keys stop being read and expire on their own (TTL set to 2 hours as a safety net).

**Step 3. Cache the shared part.** For each combination of filters, sort and page number, cache the list of product IDs and their display fields (name, image, list price, stock flag) plus the total count under `catalog:v{version}:list:{hash of normalised query params}`. Normalise the params (sorted, defaults removed) so equivalent URLs share an entry. Nothing in this entry depends on who is logged in. Check: a test that the entry is identical for an anonymous user and two different customers.

**Step 4. Apply customer prices on top, per request.** After reading the cached page of products, fetch the logged-in customer's prices for those IDs in one indexed query (index on `(customer_id, product_id)`; add it if missing) and merge them in. For about 25 to 100 products a page, that is one fast query. Only if step 1 shows the price calculation itself is expensive (rules, tiers, currency conversion) do I cache it too, under `catalog:v{version}:prices:{customer_or_pricelist_id}:{list key}`. The customer ID is in the key by construction, not added by a caller.

**Step 5. HTTP and template caching stay off for logged-in users.** No `cache_page` and no shared template fragment caching on this view for authenticated requests. Responses for logged-in users send `Cache-Control: private, no-store` so a CDN or proxy in front cannot store one customer's page and serve it to another. Anonymous responses can be `cache_page`-cached keyed on the full URL with `Vary: Cookie`, but that is optional.

**Step 6. Rollout behind a setting.** Wrap steps 3 and 4 in a setting `LISTING_CACHE_ENABLED` (default `False`), readable without a deploy if you have a settings/flag mechanism. Enable in staging, then production. Log cache hit/miss and server time per request.

Checks before enabling in production (all must hold):
- A test logs in as customer A, loads the listing, logs in as customer B with a different negotiated price on the same product, loads the same URL, and sees B's price. It also runs with the cache warm from A's request.
- A test runs the import (or bumps the version), and the next request shows the new price.
- Staging shows the same rendered prices with the setting on and off for a sample of at least 20 customers and 10 listing URLs.

Revert rule: if any customer reports or a log shows a price that is not theirs, turn the setting off at once. That disables the cache and the page falls back to the uncached path. If the hit rate after a day is low (most requests are unique filter combinations), or server time has not dropped measurably against the step 1 baseline, remove the cache rather than tune it. A cache that does not move the number is complexity with no return.

## What you lose, and what replaces it

| Today, free | With the cache |
|---|---|
| Every page shows the current database state | Shows the state as of the last version bump; the post-commit bump and the signals keep that gap near zero |
| A price edit is visible immediately everywhere | Same, provided every write path bumps the version. A write that bypasses the ORM (raw SQL, `queryset.update()`, which fires no signals) will be stale for up to the 2-hour TTL. List those paths and bump the version in them |
| No new infrastructure | Redis becomes part of the page's path. If it is down, the code treats a cache error as a miss and serves the uncached page |

## Found, not touched

- If the import job updates prices in place during the day, readers can see half-imported prices whether or not there is a cache. Running the import in a single transaction or swapping in a staging table fixes that. Not part of this change.
- Pagination with `COUNT(*)` on 50k filtered rows is often the single slowest query; step 3 caches it, but an index or an estimated count would make it cheap even uncached.

## Need from you

- The listing view, the product and price models, and the import job's entry point.
- Your cache backend, and whether there is a CDN or reverse proxy in front of Django.
- One logged-in B2B test account with negotiated prices, for the step 1 profile.
