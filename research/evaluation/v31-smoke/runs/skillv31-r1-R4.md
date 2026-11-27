The plan is to measure first and then fix the store where it already runs: same host, same theme, cheapest reversible change first, with each change kept only if it moves its number. Most of the effort is in the pages a cache cannot serve. A page cache plus image and script trimming can make the home, category and product pages fast for anonymous visitors in a few days. Cart, checkout, My Account and every page a shopper sees after adding to cart are built fresh on each request, and on shared hosting with about 40 plugins that server time is usually where the 6 seconds comes from, and it is where the money is. So the plan splits the 6 seconds into server time and browser time before touching anything, and gives the uncacheable pages their own phase. I have not seen the site, its plugin list, its host or its database, and I have run none of the commands below. The plan rests on the defaults in the questions. Moving host and rebuilding the theme are kept behind a gate in Phase 3: either may turn out to be the right call, but only the Phase 1 numbers can show that.

## Questions

Q1. What prompted this: lost sales or abandoned checkouts, a PageSpeed or Search Console warning, or customer complaints? Default: conversions on mobile, so the work follows the buying path (product, cart, checkout) rather than the PageSpeed score of the home page. If it is the score or SEO, Phase 2 weights landing-page loading (Largest Contentful Paint) and Phase 2c moves later.

Q2. What is the "6 seconds", and what counts as good enough? Default: no target until the Phase 1 baseline exists. Google's "good" Largest Contentful Paint threshold (2.5 s for 75% of real visits) is a reference point, not a promise. If the 6 s is a PageSpeed lab figure, real visitors may already see something different, and Phase 1 shows which.

Q3. Do anonymous visitors see different prices, stock or content (currency switcher, geolocation, wholesale or membership pricing, a "recently viewed" block)? Default: no for anonymous visitors, yes for logged-in ones, so only anonymous, cart-empty pages are cached. If yes, those pages either get a cache variant per cookie or stay uncached, and the cache gains less.

Q4. Is changing host an option, and what does the current one provide (web server type, PHP version, Redis or Memcached, staging, SSH)? Default: stay put. The host question opens only at the Phase 3 gate.

Q5. Who makes the changes, and is there a staging copy plus admin, file and database access? Default: a staging clone is created in step 1 and every change goes there before production.

Answer first: Q1 and Q3. Q1 decides which pages get the work. Q3 decides how much a page cache can do, and a wrong guess there can show one customer's cart to another.

## Plan

### Phase 1: Safety net and baseline (no production changes)

1. **Back up and clone.** Take a full backup (files and database) and restore it to a staging copy, with a host one-click staging or a cloning plugin. Check: staging loads, and a test order goes through with the payment gateway in test or sandbox mode. Set staging to "discourage search engines" and disable outgoing order emails, so the clone never mails real customers.
2. **Measure lab and field data on four URLs:** home, one busy category, one busy product, and cart with an item in it. Run PageSpeed Insights three times each and keep the median of LCP, Total Blocking Time, TTFB, request count and JavaScript bytes. Record the field-data panel ("what real users experience") if the site has enough traffic to show one.
3. **Split server time from browser time.** Time the first byte with curl, once as a cache-busting anonymous visitor and once with a cart session (see First steps). If uncached TTFB takes most of the 6 seconds, Phase 2b leads. If TTFB is low and LCP is high, Phase 2a leads.
4. **Profile the server side on staging** with the Query Monitor plugin: on the product and cart pages, record total query time, slow queries and the "Queries by Component" table, which names the plugins that cost the most. Install it on staging only, because it adds overhead.
5. **Inventory the plugins.** Export the active list, and next to each one write what it does, whether anyone still uses it, and whether it loads assets on every page. Expect overlaps: two SEO tools, several builder add-on packs, sliders, a security suite that scans on every request.

**First steps** (none needs an answer; replace `example.com` and the `wp_` table prefix with yours):

- `for i in 1 2 3 4 5; do curl -o /dev/null -s -w "%{time_starttransfer}\n" "https://example.com/product/<slug>/?nc=$RANDOM"; done` (curl 7.x or later). A query string bypasses most page caches, but not all of them, so check the response headers once with `curl -sI`.
- `wp plugin list --status=active --fields=name,version,update --format=csv > plugins.csv` (WP-CLI 2.x). Without SSH, copy the list from the Plugins screen.
- Autoloaded options size, which WordPress loads on every request:
  `SELECT SUM(LENGTH(option_value))/1024 AS kb FROM wp_options WHERE autoload IN ('yes','on','auto','auto-on');`
  WordPress 6.6 changed the autoload values from yes/no to on/off/auto variants, as I recall. Run `SELECT DISTINCT autoload FROM wp_options;` first to see which ones your version uses.
- `SELECT status, COUNT(*) FROM wp_actionscheduler_actions GROUP BY status;` A large pending or failed count means background jobs are piling up and slowing requests.
- `grep DISABLE_WP_CRON wp-config.php`. If it is missing, WordPress runs scheduled tasks inside visitors' page loads.

### Phase 2: Fixes, one at a time, staging first

The table lists hypotheses to confirm against the Phase 1 numbers. It is not a work list.

| If Phase 1 shows | Likely cause | Typical fix |
|---|---|---|
| High TTFB on product and category pages for anonymous visitors | No page cache | Page cache (2a) |
| High TTFB on cart, checkout and logged-in pages | Heavy plugins on every request, large autoload, no object cache, old PHP | 2b |
| Low TTFB, high LCP | Slider or hero image, oversized images, page-builder CSS blocking render | 2c |
| High Total Blocking Time | Scripts from plugins, builder widgets and third-party tags on every page | 2c |
| Some requests slow at random | WP-Cron in visitor requests, Action Scheduler backlog | 2b |

**Revert rule:** after each change, rerun the Phase 1 measurement for the affected URLs. A change that does not move its number comes out. Make one change per deployment, so a regression points at one cause.

**2a. Page cache.** Use the cache the host provides if there is one (for example LiteSpeed Cache on a LiteSpeed server), otherwise one caching plugin, never two. Exclude cart, checkout and My Account, and bypass the cache whenever the WooCommerce cart or session cookies (`woocommerce_items_in_cart`, `wp_woocommerce_session_*`) or a logged-in cookie are present. These are the names as I recall them, so check them in your browser's cookie list after adding an item. Keep the cache lifetime below the WordPress nonce lifetime (24 hours by default, as I recall), or cached add-to-cart forms start failing. Purge product pages when stock or price changes, so a cached page never shows an item that is out of stock.
Gate before enabling it in production. All of these must be true on staging:
- A cart filled in browser A does not appear in a private window B.
- `curl -sI` shows a cache miss on `/cart/` and `/checkout/`. The header depends on the cache, for example `x-litespeed-cache` or `cf-cache-status`.
- A test order completes, and a logged-in test customer sees only their own name and orders.

Abort rule: if anyone reports seeing another person's cart, name or order, turn the page cache off at once and investigate on staging.

**2b. Server time on uncacheable pages.**
- Deactivate the plugins the inventory marks as unused or duplicated, one at a time on staging, then in production in a low-traffic hour. Deactivate them rather than delete them, so rollback is one click. Some plugins remove their data when deleted, which cannot be undone.
- Replace the heaviest component from Query Monitor if its job can be done more cheaply.
- Move to the newest PHP 8.x your host offers that all active plugins support. Check the PHP error log on staging first.
- Turn on Redis or Memcached object caching if the host offers it.
- Set `DISABLE_WP_CRON` and add a real cron job every 5 minutes from the host panel.
- For autoloaded options left behind by removed plugins, set autoload to off rather than deleting the rows, after the backup.
Check for each change: cart TTFB, plus one test order with its confirmation email received.

**2c. Front-end weight.**
- Turn on the page builder's own performance settings. Their names vary by builder and version, so check your builder's documentation.
- Convert images to WebP or AVIF at the displayed size. Preload the LCP image and exclude it from lazy loading.
- Replace a home-page slider with one static image.
- Stop plugins from loading scripts on pages that do not use them, and defer third-party tags (chat, review widgets, pixels).
Exclude cart and checkout from every JavaScript delay, combine or minify setting: payment gateway scripts break under them, and the failure shows only at payment. Gate: a test order with each payment method on staging. After release, compare the daily count of Failed and Pending payment orders with the previous two weeks. A clear rise means the last front-end change is reverted that day.

### Phase 3: Decision gate for host and theme

This phase starts only after Phase 2 has been measured.
- **Host.** If uncached cart TTFB still takes most of the load time and Query Monitor shows the time is not in any plugin's queries (PHP itself is slow, or the host's process limits are hit), the host is the bottleneck. About 3,000 orders a month is roughly 100 a day, which a modest managed WordPress host handles; promotion spikes on shared hosting are the usual weak point. A move takes days and can be reversed: keep the old account and lower the DNS record's lifetime (TTL) for two weeks.
- **Theme.** If page-builder markup and CSS still dominate LCP and Total Blocking Time after 2c, rebuild only the product, category and home templates in a lighter theme on staging. This takes weeks, so it waits for this evidence and your go-ahead.

### Phase 4: Keep it fast

- Re-run the four-URL measurement monthly and after every plugin addition.
- Install a new plugin on staging first, with a before-and-after measurement.
- Set an uptime monitor with a TTFB alert on the cart page.

The order is deliberate: the baseline comes before the cache, because a cache hides the server time that matters most on cart and checkout. Two things are adjacent and not planned here. Moving orders to WooCommerce's High-Performance Order Storage, if it is not on already, speeds up the admin and order queries more than the storefront. Pending plugin updates in `plugins.csv` should be applied on staging anyway, for security.
