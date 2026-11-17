I haven't changed anything yet, for two reasons: I can't see the Django project from here (the only repo I have access to is shopmini, which is a Node/Express order API with no product listing), and caching this page the obvious way would show one customer another customer's negotiated prices.

Below is the plan I'd follow once I'm pointed at the code.

## The constraint that shapes everything

Negotiated prices are per customer, so nothing that contains a price can be cached under a key shared between customers. That rules out `@cache_page` on the view, a CDN or full-page cache, and a template fragment cache around the product grid, unless the key includes the customer.

The safe design is to split the page into two layers:

- **Shared catalogue data** (name, image, SKU, category, list price, and the ordered product IDs for a given filter, sort and page). This is identical for everyone and is where the cache goes.
- **Customer prices**, overlaid per request for only the 20 to 50 products on the current page. With an index on `(customer_id, product_id)` this is a single fast query and may not need caching at all.

## Step 1: measure before caching

A listing of 50k products is not inherently slow in Postgres. In Django listing pages, the usual causes are:

- N+1 queries (a price, image or category lookup per product row), fixed with `select_related` / `prefetch_related`.
- The paginator's `COUNT(*)` over a filtered join.
- A missing index on the filter or sort columns, or deep `OFFSET` pagination.
- The negotiated price resolved per product in Python rather than in one query.

I'd look at the query count and timings for one page load (Django Debug Toolbar or `EXPLAIN ANALYZE` on the main query). If it turns out to be an N+1 or a missing index, fixing that is a smaller change than caching and removes the problem rather than hiding it. I'd fix that first and then see how much caching is still needed.

## Step 2: add the cache

- **Backend:** Redis through Django's cache framework. If the project has no shared cache yet, that is a new piece of infrastructure, and local-memory cache is not a substitute when there is more than one app process.
- **What is cached:** the serialised shared catalogue data per `(filters, sort, page)`, and the total count for each filter combination.
- **Invalidation:** a catalogue version number is part of every key, and the hourly import job increments it when it finishes. Old entries are never read again and expire on their own. A TTL of a little over an hour acts as a backstop in case the bump is missed.
- **Customer prices:** queried live per request for the visible product IDs. If measurement shows this is still slow, I'd cache it per customer under a key that includes the customer ID and the catalogue version, and invalidate it when that customer's price agreement changes.
- **Anonymous visitors:** if they see list prices only, the fully rendered page can also be cached for them, with the cache varying on authentication so that a logged-in response is never stored.

## Step 3: tests

- Two customers with different negotiated prices request the same page back to back, and each sees their own prices. This is the test that matters most.
- An anonymous request after a logged-in one shows list prices.
- After the import job runs, the page shows the new prices.
- Query count for a warm page load is fixed and small.

## Questions I would ask

1. **Where is the code, and which view is the slow one?** Default: the main catalogue list view, server-rendered with Django templates.
2. **How slow is it, and what is the target?** Default: multi-second today, aiming for under 300 ms server time on a warm cache.
3. **Is there Redis or another shared cache in production already?** Default: no, and adding Redis is acceptable.
4. **Does the hourly import also update negotiated prices, or only list prices?** Default: list prices only, with negotiated prices changed occasionally through the admin.
5. **How is a negotiated price defined: a per-product row, a percentage discount on a customer or group, or a price list shared by several customers?** Default: per-customer, per-product rows. If it is a shared price list or a discount tier, the prices can be cached per list or tier rather than per customer, which is much cheaper.
6. **Can a customer sort or filter by price?** Default: no. If they can, the product order itself differs per customer, and the shared ID list can't be used for those sorts.
7. **Do anonymous visitors see prices at all?** Default: yes, list prices.
8. **Is a price that is a few minutes stale after an import acceptable?** Default: no, which is why the import bumps the version rather than relying on a TTL alone.

Send me the repo and the answer to question 5 in particular, and I'll start with the measurement.
