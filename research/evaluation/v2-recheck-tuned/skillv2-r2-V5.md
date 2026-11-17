The main risk here isn't speed. It's that logged-in B2B customers see their own negotiated prices. If you cache the rendered page or the whole view, the first customer's prices get served to the next customer, and that leak is commercial and hard to notice.

So the plan splits the page in two:
- **Cached:** the shared catalogue part (which products match the filters, their names, images and list prices). It's invalidated when the hourly import commits.
- **Never cached:** the customer's prices. They're looked up on every request for just the products on the page, in one query.

Before any of that, I measure. "Slow" with 50k products is often N+1 queries or a missing index. Those are cheaper to fix than a cache and stay fixed.

I haven't seen the code or the timings. The plan rests on the defaults below, and no code has been run.

## Questions I would ask

1. **After the hourly import, how long may the old prices stay on the page?** Default: no longer than it takes the import to commit. The import bumps a catalogue version once it commits, and all cached entries become unreachable at once. There's also a TTL of 2 hours as a safety net, as a setting. If a few minutes of staleness is fine, a plain 10-minute TTL replaces the version bump and the import job needs no change.
2. **Does anything else on the listing differ per customer, besides price: which products they can see, stock, currency, minimum order?** Default: I assume it might. Step 1 reads the listing query. If the product set depends on the customer, the cache key includes the customer's assortment group, never the user ID. If it differs per individual customer, only the per-product data is cached, not the list.
3. **Which pages and filters are slow, and how slow?** Default: I find out in step 1. Targets get proposed after the baseline, not before.
4. **Is there a CDN or reverse proxy in front of Django, and is Redis or Memcached already set up?** Default: I check the response headers and settings in step 1. If there's no shared cache, I add Redis. The per-process local-memory cache can't be invalidated across workers, so it isn't an option.

Answer first: 1 and 2. They decide the cache key and whether the import job changes.

## Plan

**Step 1: Measure and look (no production change)**
- Profile the listing for an anonymous visitor and for one B2B customer, on the slowest filter combinations, using query counts and timings from Django Debug Toolbar or `connection.queries` in staging, plus `EXPLAIN ANALYZE` on the main queries.
- Read the listing view to find every per-customer input.
- Record p50/p95 from production logs for 7 days as the baseline.
- Check: a list of where the time goes. If most of it is N+1 queries or a sequential scan, the fix is `select_related`/`prefetch_related` and an index, and caching waits until those are measured again.

**Step 2: Query fixes, if step 1 found them**
- Make the change step 1 identified, ship it, and measure again against the baseline.
- Revert rule: a change that doesn't move p95 gets reverted.

**Step 3: Cache the shared part, keyed safely**
- Cache key: `plp:v{catalogue_version}:{assortment_group}:{normalised filters}:{sort}:{page}`. "Normalised" means the parameters are sorted and unknown ones dropped, so junk query strings can't create endless keys.
- Cached value: product IDs plus the display fields. No customer prices, and no HTML containing prices.
- Customer prices: a single query, `WHERE customer_id = X AND product_id IN (page ids)`, merged in the view. It runs on every request, so prices are always current for that customer.
- Anonymous visitors: they also see the list price from the cached data. A rendered fragment cache for anonymous visitors is a later option once this one is proven.
- Response headers: logged-in responses send `Cache-Control: private, no-store` and `Vary: Cookie`, so a CDN or proxy never stores them.
- Behind a flag (`PLP_CACHE_ENABLED`) that can be switched off without a deploy.

**Failure coverage for step 3**
- **Price leak:** a test logs in as customer A, loads the listing, then logs in as customer B on the same filters, and checks that B's response has none of A's prices. It runs in CI.
- **Import commits:** `catalogue_version` is bumped in `transaction.on_commit` at the end of the import, so a failed import leaves the old version in place.
- **Partial import:** if the import fails midway, there's no bump, and the cache keeps showing the last consistent catalogue. Customer prices come from the database live in any case.
- **Many callers at once:** at the hour, every key misses together. The import warms the first page of the 20 most-requested filter sets after it bumps the version, with the list taken from the logs. Other keys fill on demand. For a hot key, a short lock (`cache.add`) lets one request rebuild it while the others wait up to 2 seconds and then query directly.
- **Cache down:** cache errors are logged and the request falls through to the database, so the page is slow but correct. In django-redis that's `IGNORE_EXCEPTIONS`, a name I'm recalling from memory that should be checked against the installed version.
- **Overload:** only the first 5 pages of each filter set are cached, which caps how many keys there are. There's an eviction policy and a memory limit on Redis.
- **Unknown caller:** other code that writes prices or products outside the import, such as admin edits or a sales-rep tool, would leave the cache stale. A `post_save` hook on `Product` bumps the version, and step 1 lists any other writers.

**Step 4: Rollout with shadow comparison**
1. Deploy with the flag in shadow mode for 2 days. 5% of requests compute both the cached and uncached result and log any difference in product IDs or prices. The page shown always comes from the uncached path.
2. Turn the flag on for anonymous visitors, then for all logged-in users.
3. Abort rule: any price difference in the shadow logs, or any leak report, means the flag goes off and stays off until the cause is reproduced and fixed.
4. Revert rule: if p95 on the listing doesn't fall below the step 1 baseline within 2 days of the flag being on, remove the cache rather than tune it.
