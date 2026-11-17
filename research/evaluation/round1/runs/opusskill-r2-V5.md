# Caching the product listing page

The hard part is not making the page faster. It is caching without showing one B2B customer another customer's negotiated price. Rendered pages differ by customer, so any whole-page or per-view cache can serve a logged-in customer someone else's prices. Django's `cache_page`, a CDN, and template fragment caching around the price column all carry this risk. My recommendation is to cache only the part that is the same for everyone: the filtered and sorted list of product IDs and product data. Clear that cache whenever the hourly import finishes. Then look up the customer's prices for the 24 to 50 products on the current page in one query on every request. That price query stays uncached. Price lookups for one page are cheap, and caching them is where the leaks come from.

**First, a check that may make caching unnecessary.** With 50k products in Postgres, a slow listing page usually has one of three causes. The first is an N+1 query: one query per product for price, image or category. The second is `COUNT(*)` for pagination over a filtered query. The third is an index that doesn't match the filter and sort the page uses. One profiling pass costs about an hour and usually finds the cause. It needs django-debug-toolbar or `connection.queries` locally, and `EXPLAIN ANALYZE` on the slowest query. Fixing any of these causes leaves nothing new to clear and nothing that can leak, so it should come before caching. That is question 1 below. I plan the caching you asked for in full below, and step 1 is that profiling pass, since it decides what the cache needs to hold.

I have not seen your code, models or how the page is built. The plan relies on the defaults below, and none of it has been run.

## Questions I would ask

1. **Do you want a cache, or a faster page by whatever means?** Default: profile first (step 1). Add the cache only if the page is still slow after the query fixes.
2. **How are negotiated prices stored, and when do they change?** Default: a separate table (customer or price group, product, price) that the import job updates, plus occasional manual edits in admin. The plan never caches these prices, so it does not matter when they change. If prices are calculated by rules such as tiers, discounts or volume breaks, step 4 has to cache the rule inputs per customer. That needs its own cache-clearing on admin edits, and it is the riskiest part of the plan.
3. **What else on the page changes outside the import: stock levels, availability, promotions?** Default: only the import changes listing data. If stock is live, the stock badge is loaded the same way as prices, per page and uncached.
4. **Is there a shared cache backend (Redis or Memcached) in production, and how many app servers are there?** Default: Redis is available. With more than one server, a cache local to each process (`LocMemCache`) would serve different data from different servers after an import, so it is not an option.
5. **Do anonymous visitors see prices, and are they the same for everyone?** Default: anonymous visitors see list prices only. Their pages can also take a short whole-page cache. That is a later step, kept away from logged-in traffic.

Answer first: 1 and 2. Question 1 may remove the need for a cache. Question 2 decides whether the price lookup is one simple query or needs its own cache layer.

## Plan

**1. Measure the page (no code change).** Record the number of queries and the time per query for one listing request, logged in as a B2B customer, with the filters people actually use. Run `EXPLAIN ANALYZE` on the main query and the count query. Write down p50/p95 from production monitoring as the baseline. I am not setting a target until there is a baseline.

**2. Fix what the measurement shows.** This is usually `select_related` or `prefetch_related` for the product's related data, an index on the filter and sort columns, and a cheaper or capped count for pagination. Re-measure. If the page is fast enough now, stop here.

**3. Cache the shared listing data.**
- Key: `plp:v{catalog_version}:{hash of normalised filters + sort + page}`. The value holds the product IDs in order, the total count, and the product fields the template shows. It never holds prices that vary by customer.
- `catalog_version` is an integer in the cache, or in a one-row table as a fallback. The import job increases it as its last step, after its transaction commits (`transaction.on_commit`). Old keys are never read again and expire on their own. This avoids deleting by key pattern.
- TTL: a few hours, as a backstop in case a version bump is missed. This is a guess, set as `PLP_CACHE_TTL`.
- Feature flag `PLP_CACHE_ENABLED` (a setting, or an env var read per request) so the cache can be turned off without a deploy.
- Admin edits to products: a `post_save` signal on `Product` increases the same version. This is crude but correct. Make it finer only if admin edits are frequent.

**4. Load the customer's prices per request, uncached.** After getting the page's product IDs (from the cache or the database), run one query: prices for `(customer's price group, product_id IN page_ids)`. Fall back to list price where no negotiated price exists. Use the same code path for the product page and the cart, so the listing can't show a price the cart doesn't honour. This query uses an index on `(price_group_id, product_id)`. Check that the index exists.

**5. Roll out in shadow mode, then enable.** With the flag in a `shadow` setting, the view builds the page both ways: from the cache, and from the existing code. It logs any difference in IDs, order or prices, and serves the existing result. Run it through at least two import cycles. Then turn on the cache for internal accounts, then for everyone. Check that the cache hit rate is sensible. The rendered HTML still contains per-customer prices, so the response must keep sending `Cache-Control: private` (or `no-store`). Confirm that nothing in front of Django (CDN, nginx) caches responses for logged-in users.

**Stop and revert rules**
- Any shadow log line where prices differ between the two paths: stay in shadow and find the cause. Do not enable.
- After enabling: any report of a customer seeing a price that isn't theirs, or a price on the listing that differs from the cart. Turn off `PLP_CACHE_ENABLED` immediately and investigate with the flag off.
- If p95 does not improve compared with the step 1 baseline, remove the cache. It adds staleness and invalidation code for nothing.

**Tests to add**
- Two customers with different negotiated prices for the same product request the same listing URL one after the other. Each sees only their own price, and the second request is a cache hit.
- An import run (or the version bump alone) followed by a listing request shows the new list price and product data.
- An anonymous request never shows a negotiated price.

## Found, not touched
- I have not seen the import job. If it updates prices in several transactions, readers can see half-imported prices during a run whether or not there is a cache. Bumping the version after commit does not fix that.
- Whole-page caching for anonymous visitors (question 5) is a separate, cheaper step. I left it out so that logged-in and anonymous caching never share a code path.

## Need from you
- The listing view, the `Product` and price models, and the import job's entry point.
- A production p95 for the listing page, and one slow URL with its filters.
- Whether Redis is in production, and how many app servers there are.
