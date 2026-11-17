"6 seconds" can come from two places, and each needs a different fix: time spent on the server before the first byte arrives (shared hosting, 40 plugins running PHP on every request, no page cache), and weight in the browser after it arrives (page-builder markup, CSS and JS from every plugin on every page, images, third-party scripts). The first step measures which of the two it is on your pages, and every fix after that follows the measurement. Checkout gets extra care throughout: with about 3,000 orders a month, a broken cart costs far more than a slow one.

I have not seen the site, the plugin list, the hosting panel or any measurements. The plan below runs without answers, starting with measurement.

## Questions I would ask

1. **Which pages are slow, and what does "6 seconds" measure (a PageSpeed Insights score, fully loaded time, what a customer feels)?** Default: the home page, one category, one product, cart and checkout, measured as in step 1.
2. **Is moving hosting on the table?** Default: stay on shared hosting until step 1 shows whether server time dominates. If server response time is the bulk and caching cannot fix it (cart and checkout cannot be page-cached), managed WooCommerce hosting or a VPS with an object cache (Redis) is usually the single biggest gain. The cost is a monthly fee plus one migration.
3. **Which plugins are off limits (payments, shipping, invoicing, ERP or stock sync)?** Default: none is removed without your OK. Disabling them as a test only happens on staging.
4. **What access is there: WordPress admin, the hosting panel, SFTP/SSH, a staging copy?** Default: admin and the panel, no SSH. A staging copy is made in step 0.

Answer first: 1 and 2. Question 1 points the measurement at the pages that matter. Question 2 decides whether hosting is an option when the server turns out to be the problem.

## Plan

**Step 0: safety first.** Take a full backup (files and database) and restore it once on staging, using the host's staging feature or a cloning plugin. Do all the work on staging, and move each change to production on its own, outside peak order hours. After every production change, run a checkout smoke test: add to cart, apply a coupon, and pay with each payment method in test mode (or one real low-value order that you then refund).

**Step 1: measure and split server from browser.**
- Field data: PageSpeed Insights on the five pages, mobile, with real-user (CrUX) data where the site has enough traffic.
- Lab data: WebPageTest or PSI lab on a throttled mobile profile, 3 runs per page, logged-out, with an empty cart and with one item in the cart.
- Server: Time to First Byte for each page, logged-out, with and without the page cache if one exists. On staging, use Query Monitor to see query count and time and which plugins are slowest. Check the size of autoloaded options in `wp_options`, and how often `admin-ajax.php` / `wc-ajax=get_refreshed_fragments` is called.
- Inventory: plugins that load CSS or JS on every page, third-party tags (chat, pixels, review widgets), and image sizes and formats.
*Check:* a small table per page: TTFB, LCP, total JS/CSS weight, request count. Targets are set from this table. I am not inventing them now; Google's "good" line for LCP (2.5 s) is a useful reference.

**Step 2: fix what the measurements point to.** The table below is a set of hypotheses to confirm against step 1, not a list of work to do.

| If step 1 shows | Likely cause | Typical fix |
|---|---|---|
| High TTFB on logged-out catalogue pages | No page cache, or a cache that bypasses too much | Page cache (the host's own, or a single caching plugin), excluding cart, checkout, my-account and logged-in users |
| High TTFB on cart and checkout, even when cached elsewhere | Plugin work in PHP, slow queries, large autoload, shared CPU | Remove or replace the heavy plugins Query Monitor names; clean up autoload; add an object cache if the host supports it; otherwise question 2's branch |
| Large JS/CSS, many requests | Plugins and page builder loading assets on every page | Unload plugin assets on pages that do not use them; turn on the builder's own performance options (loading only used widgets, etc.); defer non-critical JS |
| Late LCP image | Oversized hero image, lazy-loaded hero | Properly sized WebP/AVIF; no lazy loading on the LCP image; preload it |
| Many `get_refreshed_fragments` calls | Cart-fragment AJAX on every page | Limit it to pages that show the cart |
| Slow third-party scripts | Chat, pixels, widgets | Load them after interaction, or drop the ones nobody uses |

Rules for this step:
- One change at a time, re-measured on the same pages under the same conditions.
- **A change that does not move its number is reverted.**
- **Caching rule:** before any page cache goes live in production, confirm on staging that two different browsers with different carts never see each other's cart, prices or account details. A cache that leaks carts is worse than a slow site.
- Use one optimisation or caching plugin, not several. They conflict, and stacking them is a common cause of broken checkouts.

**Step 3: plugin audit.** For each of the 40 plugins, record whether it is used, what it costs (from step 1), and whether something else on the site already does the same job. Deactivate candidates on staging one at a time, then run the checkout smoke test. Remove plugins in production only with your OK (question 3), and keep their settings exported.

**Step 4: decide on hosting (if step 1 points there).** If TTFB on uncacheable pages stays high after steps 2 and 3, compare one managed WooCommerce host or VPS by cloning the site onto a trial account and measuring the same five pages. Move only if the trial shows a clear difference. Migrate on a low-traffic day, lower the DNS TTL beforehand, and keep the old hosting active until a full day of orders has gone through the new one.

**Step 5: keep it fast.** Re-run the step 1 measurements monthly, and after any new plugin or theme update. Add a note to whoever installs plugins: measure before and after.

## Things I would not do yet, and why

- **Rebuild the theme or drop the page builder.** It is the most expensive option, and steps 2 and 3 often get most of the gain without it. Reconsider only if, after those steps, the builder's own CSS/JS is still what dominates the measurements.
- **Install several "speed" plugins at once.** They overlap, conflict, and make results impossible to attribute.
- **Move hosts before measuring.** It may not be the bottleneck, and a migration brings its own risk.

## Need from you

- Answers to questions 1 and 2.
- The plugin list (Plugins page export or screenshot) and the theme/builder name.
- A staging copy, or permission to create one, plus admin access to it.
