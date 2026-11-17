"6 seconds" can come from two very different places, and the plan starts by finding out which. The first is server time: shared hosting running PHP for about 40 plugins on every uncached request. The second is the browser: page-builder CSS and JavaScript, large images and third-party scripts. A WooCommerce store has a third part that ordinary page caching cannot cover. The cart, checkout and account pages, and every visitor who has added something to the cart, always run uncached, so a page cache alone can make the homepage fast while checkout stays slow. The default plan is to measure, then make reversible changes one at a time on a staging copy, each kept only if it moves its number. Moving hosts or rebuilding the theme waits until the measurements point there. I have not seen the site, its plugin list or the host, so the plan rests on the defaults below. Targets come after the baseline, except where Google's published Core Web Vitals thresholds already define "good".

## Questions I would ask

Q1. What prompted this, and where does "6 seconds" come from (PageSpeed Insights, GTmetrix, a stopwatch on a phone, customer complaints)? - Default: a PageSpeed Insights mobile result for the homepage, and a worry about conversion and Google ranking. If the complaint is about cart and checkout, the uncached path and the hosting decision (step 9) move to the front.
Q2. What counts as good enough? - Default: field LCP at or under 2.5 s, and INP at or under 200 ms, on product and category pages (Google's "good" thresholds), and checkout server response under 1 s. Firm targets for each template follow the baseline.
Q3. Is changing hosting an option, and roughly what monthly budget? - Default: yes, if step 9's condition is met. If not, steps 5 to 8 are the whole plan, and checkout will stay limited by the server.
Q4. Which plugins are essential to the business (payment, shipping rates, invoices and NF-e, ERP or stock sync, reviews)? - Default: nothing in these categories is removed without a tested replacement. Step 3 labels every plugin.
Q5. Do you have a staging copy and daily backups, and who will make the changes (you, a developer, an agency)? - Default: the host provides staging and backups, and one developer does the work with your approval for each removal.

Answer first: Q1 and Q3. With those, I can skip part of the measurement and decide early whether hosting is the main fix.

## Plan

### Phase 1 - Baseline and safety (days 1-3)

1. **Safety first.** Take a full backup (files and database) and restore it to a staging copy, then confirm the copy places a test order. Every change below is tried on staging first, then applied to production during a low-order hour. Keep a change log (date, change, before and after numbers) so any change can be undone individually.
2. **Measure four page types:** homepage, a category page, a product page, and cart/checkout with an item in the cart.
   - Field data: PageSpeed Insights mobile for each, recording field LCP, INP and CLS where Chrome has enough visits, plus the lab result.
   - Server time, cached against uncached: `for i in 1 2 3 4 5; do curl -s -o /dev/null -w "%{time_starttransfer}\n" "https://yourstore/produto/x/?nocache=$RANDOM"; done`, then the same without the query string. Uncached time above about 1 s means the server is the main problem; under that, with LCP still slow, it is the browser side.
   - The `server:` and cache headers from `curl -sI https://yourstore/` show whether a page cache exists and which web server runs (LiteSpeed changes the caching choice in step 5).
3. **Find the cost inside the server,** on staging. Install Query Monitor and record, per page type, the slowest database queries, the plugins whose hooks take longest, and outgoing HTTP calls made during page generation (each one blocks the page). Export the plugin list with `wp plugin list --status=active --fields=name,version --format=csv` if the host offers WP-CLI, otherwise from the Plugins screen. Label each plugin: essential (Q4), used, or unused.

**First steps (need no answers):**
- Run the `curl` timing loop above for the four page types, cached and uncached, and save the numbers.
- Run PageSpeed Insights mobile on the same four URLs and save the reports.
- In phpMyAdmin: `SELECT COUNT(*), ROUND(SUM(LENGTH(option_value))/1024) AS kb FROM wp_options WHERE autoload IN ('yes','on','auto','auto-on');` (WordPress 6.6 added the newer autoload values; check against your version). Above roughly 1 MB, autoloaded options slow every request.
- `SELECT status, COUNT(*) FROM wp_actionscheduler_actions GROUP BY status;` to see whether WooCommerce's background job table has grown large.
- Read the PHP version under Tools > Site Health > Info > Server.

### Phase 2 - Reversible fixes, one at a time (weeks 1-2)

Rule for this phase: each change is measured again with the same step-2 method. A change that does not move its number is reverted. Nothing outside this list is changed.

4. **Clean up the server side.** Upgrade to the newest PHP version your plugins support (test checkout on staging first). Deactivate unused plugins. For used plugins that Query Monitor shows as costly, look for a lighter replacement. Clear expired transients, and delete completed Action Scheduler entries older than 30 days. Check: uncached server time drops on staging, and a test order and an admin order edit both still work.
5. **Page cache with WooCommerce exclusions.** Use the host's cache, or LiteSpeed Cache if the server is LiteSpeed. Otherwise use a caching plugin. Exclude `/carrinho`, `/finalizar-compra` and `/minha-conta` (or whatever your actual page slugs are), and bypass the cache for visitors with the `woocommerce_items_in_cart` or `wp_woocommerce_session_` cookies, and for logged-in users. These exclusions are what stop one customer's cart or account page from being served to another. Check: add an item in one browser, open the same product in a private window, and the cart there is empty; product pages show a cache HIT, and the cart page bypasses the cache.
6. **Images.** Serve WebP or AVIF at the displayed size, lazy-load everything below the fold, and do not lazy-load the main product image or hero image (give it `fetchpriority="high"`). Check: PageSpeed's LCP element and its load time.
7. **Scripts.** Delay chat widgets, pixels and other third-party tags until the visitor interacts, and load the page builder's assets only on pages that use each widget (most builders have a setting for this; its name depends on the builder). Check whether the cart-fragments AJAX request (`wc-ajax=get_refreshed_fragments`) fires on every page. From memory, recent WooCommerce versions load it only with the mini-cart widget; confirm in the browser's Network tab. Check: INP and total JavaScript size in PageSpeed, and the mini-cart still updates after adding an item.
8. **Object cache and CDN, if available.** Turn on Redis object cache if the host offers it, and serve static files through a CDN. Do not cache HTML at the CDN until step 5's exclusions are copied there.

### Phase 3 - Structural decision (week 3, behind a gate)

9. **Hosting.** Move to managed WooCommerce hosting or a VPS with dedicated PHP workers and Redis if, after phase 2, uncached server time on cart or checkout is still above 1 s, or Query Monitor shows the time spent in the database or PHP rather than in any one plugin. Before switching DNS, all of these must be true:
   - the new host passes the step-2 measurements on a temporary URL;
   - a real order has been paid and e-mailed from the new host;
   - payment-gateway webhooks and the shipping and invoice plugins are pointed at the new domain or IP.
   Rollback is pointing DNS back. Set the DNS TTL to 300 seconds a day ahead, and freeze product edits during the switch so no orders or edits are lost between hosts.
10. **Theme (branch).** If LCP stays above 2.5 s on product and category pages after phases 2 and 3, and the page builder's markup is the main cost, rebuild only those two templates in a lighter theme or block templates. That is several weeks of work, and only the measurements make it worth starting.

I am leaving out a "speed plugin" that minifies and combines everything at once. It often breaks checkout scripts, and it would hide which change helped.
