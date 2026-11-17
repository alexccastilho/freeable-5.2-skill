On shared hosting with about 40 plugins, the 6 seconds is usually two separate problems: slow server responses, and a heavy page from the builder theme. They need different fixes, so the plan measures which one dominates on each page type before changing anything. Page caching fixes the server side for visitors who are just browsing. It cannot help cart, checkout or account pages, or any visitor who has something in their cart, and for a store doing 3k orders a month those pages matter most. If those pages stay slow after the plugins are trimmed, the next step is better hosting with an object cache, not more caching plugins. The plan works on a staging copy, makes one change at a time, keeps only changes that move a measured number, and places a test order after every change. Rebuilding the theme is left out: it takes weeks, and measurement usually shows it is not where most of the time goes. I have not seen your site, so the plan rests on the defaults below. Plugin and setting names are recalled and flagged where they appear.

## Questions I would ask

Q1. Where does "6 seconds" come from: PageSpeed Insights, a monitoring tool, analytics, or customers complaining? And which pages? Default: a PageSpeed mobile test of the home and product pages. If the complaint is about checkout specifically, phase 3 (the server side) moves ahead of phase 2.

Q2. What counts as fast enough? Default: Core Web Vitals in the "good" range in Google's real-user data (LCP up to 2.5 s, INP up to 200 ms, CLS up to 0.1, which are Google's published thresholds), plus a server response target for cart and checkout that I set after the baseline. I am not setting a seconds target before measuring.

Q3. Is changing hosting an option, and is there a monthly budget for it? Default: yes, if the measurements show the server is the main cost. If not, the plan stays on caching and plugin trimming, and the ceiling is whatever the shared host can deliver.

Q4. Which plugins are untouchable: payment, shipping, invoicing, ERP or marketplace syncs? Default: payment, shipping and anything that touches orders stay as they are. Everything else is a candidate for removal.

Q5. What access do I get? Default: a wp-admin administrator, the hosting control panel and SFTP, and a staging copy created from the host's panel or a staging plugin.

Answer first: Q1 and Q3. Q1 decides which pages come first. Q3 decides how far the server side can go.

## Plan

### Phase 0: safety net (before any change)

- Take a full backup of files and database through the host's backup feature, and restore it once to staging, so you know restoring works.
- All changes are made on staging first. Each change goes to production on its own, with its date and the before and after numbers written down.
- **After every change:** place a real test order (a 100% coupon, or the gateway's test mode on staging) through cart, checkout and the confirmation e-mail. Revert at once if any step fails.

### Phase 1: baseline

**First steps** (none needs an answer):

1. Run [PageSpeed Insights](https://pagespeed.web.dev) on mobile for five URLs: home, one category, one product, cart and checkout. Record the field data (the real-user section, if it appears) and the lab LCP, TBT and TTFB for each.
2. Measure server time on its own, three times per URL, with nothing in the cart: `curl -o /dev/null -s -w "%{time_starttransfer}\n" https://<store>/product/<slug>/`. Repeat the cart URL with a cart cookie copied from your browser, to see the uncached path.
3. Measure the size of autoloaded options, which WordPress loads on every request: `SELECT ROUND(SUM(LENGTH(option_value))/1024) AS kb FROM wp_options WHERE autoload IN ('yes','on');`. Then list the 20 largest: `SELECT option_name, LENGTH(option_value) AS bytes FROM wp_options WHERE autoload IN ('yes','on') ORDER BY bytes DESC LIMIT 20;`. Adjust the `wp_` prefix if yours differs.
4. Check the backlog of scheduled tasks: `SELECT status, COUNT(*) FROM wp_actionscheduler_actions GROUP BY status;`. Hundreds of thousands of rows marked complete or failed slow down the admin and the cron runs.
5. On staging, install Query Monitor and load the product and checkout pages. Record the total database query time, the slowest queries, and the time each plugin adds.
6. Write down the PHP version (Tools, then Site Health, then Info), and whether the server runs LiteSpeed, Apache or Nginx (in the response headers, or ask the host). The server type decides which cache plugin works best.

Phase 1 ends with a table: page, TTFB, LCP, total page weight, and the largest items in it. Every fix after this point is a hypothesis to be checked against that table.

### Phase 2: changes that usually pay off, one at a time, measured

| What the baseline shows | Likely cause | Fix to try |
|---|---|---|
| High TTFB on browsing pages | No page cache | A page cache that matches the server: LiteSpeed Cache on LiteSpeed, otherwise WP Rocket or similar (names recalled; check compatibility with your host). Cart, checkout, my-account and visitors with WooCommerce's cart or session cookies are excluded. Check: in a private window, add an item to the cart, then confirm the cart page shows your item and nobody else's, and that a second browser sees an empty cart. |
| High TTFB everywhere | Plugins or PHP | Deactivate plugins one at a time on staging, starting with the slowest in Query Monitor, and delete those nobody needs. Upgrade PHP to the newest version your host offers that every plugin supports (check each plugin's stated compatibility first). |
| Autoload larger than about 1 MB | Leftovers from removed plugins | Set the largest unneeded options to not autoload, after a database backup. Never delete options belonging to active plugins. |
| A `wc-ajax=get_refreshed_fragments` request on every page | Cart fragments | Limit it to pages that show the mini-cart, or switch it off if the theme does not need it. Check: the cart count still updates after adding an item. |
| Large LCP image | Unoptimised images | Serve WebP or AVIF at the right sizes, do not lazy-load the main image, and lazy-load everything below it. |
| Heavy JavaScript or CSS from the builder | Assets loaded on every page | Unload unused assets per page, defer non-critical scripts, host fonts locally and use fewer of them. Check: the menu, the variation selector and add-to-cart still work on a real phone. |
| Slow for distant visitors | No CDN | Put a CDN such as Cloudflare in front of static assets, and exclude cart, checkout and account pages from any HTML caching. |

**Revert rule:** a change that does not improve its row of the baseline table is reverted. Anything not in the table is left alone.

### Phase 3: decision on the server side

After phase 2, measure the cart and checkout TTFB again, with an item in the cart. If it is still well above the target set from Q2, the shared host is the limit: there is no persistent object cache, and the CPU is shared. Then:

- Move to managed WooCommerce hosting, or a VPS, with Redis object caching and current PHP.
- Before switching DNS, all of these must be true: the site cloned to the new host passes the test order, payment webhooks and transactional e-mail work there, the DNS TTL was lowered to 300 seconds at least a day earlier, and order-taking is paused or kept to a quiet hour during the final database copy, so no order is lost between the two databases.
- **Rollback:** point DNS back at the old host. Any orders placed on the new host in the meantime have to be re-entered by hand, so watch it for the first few hours.

If cart and checkout are already close to the target, skip this phase.

### Phase 4: keep it fast

- Monitor TTFB for the product and checkout pages with an uptime service, and alert at twice the post-fix baseline.
- Before any new plugin goes live, check its effect on staging with Query Monitor.
- Recheck the Core Web Vitals report in Search Console 28 days after the last change, since Google's real-user data covers a rolling 28-day window.

I have left out replacing the page-builder theme. Asset unloading usually recovers most of what it costs, and it can still be considered once phase 2's numbers are in.
