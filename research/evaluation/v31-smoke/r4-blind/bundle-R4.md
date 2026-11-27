# Responses for task R4


=============== RESPONSE R4-A ===============

"6 seconds" can come from two places, and each needs a different fix: time spent on the server before the first byte arrives (shared hosting, 40 plugins running PHP on every request, no page cache), and weight in the browser after it arrives (page-builder markup, CSS and JS from every plugin on every page, images, third-party scripts). The first step measures which of the two it is on your pages, and every fix after that follows the measurement. Checkout gets extra care throughout: with about 3,000 orders a month, a broken cart costs far more than a slow one.

I have not seen the site, the plugin list, the hosting panel or any measurements. The plan below runs without answers, starting with measurement.

## Questions I would ask

1. **Which pages are slow, and what does "6 seconds" measure (a PageSpeed Insights score, fully loaded time, what a customer feels)?** Default: the home page, one category, one product, cart and checkout, measured as in step 1.
2. **Is moving hosting on the table?** Default: stay on shared hosting until step 1 shows whether server time dominates. If server response time is the bulk and caching cannot fix it (cart and checkout cannot be page-cached), managed WooCommerce hosting or a VPS with an object cache (Redis) is usually the single biggest gain. The cost is a monthly fee plus one migration.
3. **Which plugins are off limits (payments, shipping, invoicing, ERP or stock sync)?** Default: none is removed without your OK. Disabling them as a test only happens on staging.
4. **What access is there: WordPress admin, the hosting panel, SFTP/SSH, a staging copy?** Default: admin and the panel, no SSH. A staging copy is made in step 0.

Priority: 1 and 2. Question 1 points the measurement at the pages that matter. Question 2 decides whether hosting is an option when the server turns out to be the problem.

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


=============== RESPONSE R4-B ===============

# Plan: make the WooCommerce store fast on mobile

Six seconds on mobile with 40 plugins, a page-builder theme, and shared hosting usually has three causes stacked on top of each other: a slow server response (no page cache, overloaded shared CPU, heavy PHP from plugins), too much JavaScript and CSS (page builder plus plugins loading on every page), and heavy images. The plan is to measure first so we know which one dominates, take the cheap wins, and only then make the bigger decisions (hosting, theme).

## Questions I would ask

1. **"6 seconds" measured how?** Which pages (home, category, product, cart/checkout), and which tool (PageSpeed Insights, real users in Search Console's Core Web Vitals report, a stopwatch)?
   *Default: the PageSpeed Insights mobile score on the home and product pages. I'll re-measure everything at the start anyway.*
2. **Which page builder, which theme, which host and plan, and which PHP version?**
   *Default: Elementor or Divi on a typical shared plan, PHP possibly old (7.4 or 8.0).*
3. **Is there a staging copy, and do you have recent backups?**
   *Default: no staging. Creating one is step 1, because changes to plugins and caching on a live store can break checkout.*
4. **Is moving hosting on the table, and what's the budget?**
   *Default: yes, if the measurements show the server is the bottleneck. Something like USD 25–60/month for a managed WooCommerce host or a small VPS.*
5. **Is a theme rebuild on the table** (moving off the page builder to a lightweight theme or block theme)?
   *Default: not now. We optimize what exists first, and treat a rebuild as a later option.*
6. **Are there plugins you know are essential** (payments, shipping, invoicing, ERP integration)?
   *Default: I'll classify them from the plugin list and confirm with you before removing anything.*

## Phase 0: safety and baseline (day 1–2)
- **Full backup, plus a staging site** (most hosts offer one-click staging; otherwise use a plugin like WP Staging). Every change below is tested on staging first, including a real test order with each payment method.
- **Baseline measurements**, written down:
  - PageSpeed Insights / Lighthouse mobile for home, a category page, a product page, and the cart. Record LCP, INP, CLS, and TTFB.
  - Field data from Search Console's Core Web Vitals report or CrUX, if the site has enough traffic.
  - A WebPageTest waterfall (mobile, 4G) to see request count, total weight, and what blocks rendering.
- **Server-side profiling:** install Query Monitor on staging to see slow database queries, slow plugins, and HTTP calls out to external services during page load. Check TTFB with and without being logged in.

**How to read it:**
- TTFB above about 0.8–1 s → the bottleneck is the server and PHP. Go to Phase 2 early.
- TTFB fine but LCP high → the front end (images, JS/CSS) is the bottleneck. Go to Phase 1.

## Phase 1: quick wins (week 1)
1. **Page caching.** Use the host's cache if it exists (e.g. LiteSpeed Cache on LiteSpeed servers), otherwise WP Rocket or similar. Cache full pages for anonymous visitors, and **exclude cart, checkout, and my-account**. Make sure WooCommerce cookies bypass the cache correctly.
2. **Images.** Convert to WebP/AVIF, serve the right sizes (`srcset`), lazy-load images below the fold, and **don't** lazy-load the LCP image (the hero or main product image). Preload or `fetchpriority="high"` the LCP image.
3. **Plugin audit.** Classify all 40 plugins as essential / replaceable / unused. Remove unused ones, and replace heavy single-purpose ones (sliders, social feeds, multiple analytics or pixel plugins, duplicate SEO or security plugins). Each removal gets tested on staging.
4. **Load assets only where needed.** Use Perfmatters or Asset CleanUp to stop plugin CSS and JS loading on pages that don't use them: contact-form scripts outside the contact page, WooCommerce scripts outside shop pages, cart fragments where they aren't needed.
5. **`wc-ajax=get_refreshed_fragments` (cart fragments).** This is a classic WooCommerce slowdown: an uncached AJAX request on every page view. Disable it on non-shop pages, or replace it with a lighter mini-cart.
6. **Third-party scripts.** Audit chat widgets, pixels, tag managers, and review widgets. Delay the non-critical ones until the user interacts with the page; consolidate tracking into one tag manager.
7. **Fonts.** Host them locally, keep only the weights you use, and add `font-display: swap`. Preload the main font.
8. **Update PHP** to 8.2/8.3 (check plugin compatibility on staging first). This alone often speeds up PHP execution by 20–30% or more.

Re-measure after each group of changes so we know what actually helped.

## Phase 2: server and database (week 2)
- **Database cleanup:** remove expired transients, post revisions, orphaned metadata, and old Action Scheduler logs (often huge on WooCommerce). Check autoloaded options (`wp_options` where `autoload = 'yes'`): over about 1 MB is a problem, often caused by leftovers from deleted plugins.
- **WooCommerce High-Performance Order Storage (HPOS):** enable it if all your plugins support it. It speeds up order queries and admin.
- **Object cache** (Redis or Memcached) if the host offers it. It helps the logged-in, cart, and checkout pages, which can't be page-cached.
- **Real cron:** turn off `WP_CRON` running on page visits, and use a server cron instead.
- **A CDN** (Cloudflare or the host's CDN) for static files, plus Brotli/gzip and HTTP/2 or HTTP/3.
- **Hosting decision.** If TTFB is still high after page caching and object caching, or uncached pages (cart, checkout, search, filters) stay slow, shared hosting is the limit. At about 3k orders a month, moving to managed WooCommerce hosting or a small VPS with LiteSpeed/Nginx, PHP 8.x, and Redis is usually the single biggest improvement, and it pays for itself in conversions.

## Phase 3: front-end weight from the theme (weeks 3–4)
- Turn on the page builder's own performance options (Elementor: optimized DOM output, improved asset loading, inline font icons; Divi: dynamic CSS/JS). Remove unused widgets and modules.
- Simplify the heaviest templates (usually home and product): fewer nested sections, no sliders or carousels above the fold, no autoplay video in the hero.
- Critical CSS plus deferred non-critical CSS, and deferred JS (through the cache plugin, testing checkout carefully).
- Fix CLS: set dimensions on images and banners, and reserve space for cookie bars and promo bars.

## Phase 4: decide on the longer term
If after all this the mobile LCP is still above about 2.5 s on product and category pages, the page-builder theme is the remaining ceiling. Options, from cheapest to most work:
1. Rebuild only the key templates (product, category) with WooCommerce blocks or a lightweight theme (Kadence, Blocksy, GeneratePress), and keep the builder for marketing pages.
2. Fully migrate to a lightweight or block theme.
3. Go headless (only worth it at a much larger scale; not recommended at your size).

## Targets and how we verify
- **Targets (mobile, 75th percentile of real users):** LCP under 2.5 s, INP under 200 ms, CLS under 0.1, TTFB under 0.8 s.
- Lab tests before and after each phase on the same pages, plus the field data in Search Console (it takes about 28 days to reflect changes).
- **Business checks:** conversion rate on mobile, checkout errors, and a test order after every change. Speed is pointless if checkout breaks.

## What I'd do first
1. Backup and staging.
2. Baseline measurements, with TTFB as the deciding number.
3. Page caching, images, the plugin audit, and the PHP update. These are usually where most of the gain comes from in the first week.

If you send the plugin list, the host and plan, and a PageSpeed link for your product page, I can turn Phase 1 into a concrete checklist for your site.


=============== RESPONSE R4-C ===============

The first job is to find out which half of the 6 seconds is slow. One half is the server building the page. On shared hosting with WooCommerce and 40 plugins this is often 1–3 seconds before the browser receives anything, and no front-end optimization fixes it. The other half is the browser downloading and running what the page builder and plugins load. Each half has a different fix, and only the server half can justify moving hosts, so the plan measures first and then fixes in order of cost. It works without answers to the questions below. The answers mainly decide whether moving hosting is an option.

**Not seen:** the site, the plugin list, the hosting plan or any measurements. I don't know which page or tool the 6 seconds comes from.

## Questions I would ask

Q1. Where does "6 seconds" come from: which page, which tool, measured by whom? - Default: PageSpeed Insights on mobile for the home page. Step 1 measures again across the key pages anyway.

Q2. What access do we have: wp-admin, the hosting control panel, SFTP/SSH, a staging feature? - Default: wp-admin and the control panel, no SSH. Changes are tried on a staging copy first (the host's staging tool, or a cloned subdomain).

Q3. Is changing hosting on the table? - Default: yes, if step 1 shows server time is the main problem. No budget figure assumed: you get the measured difference to decide with. If not, the plan still runs, but the server half stays capped at what caching can do.

Q4. Which plugins are business-critical (payments, shipping, invoicing, ERP or marketplace sync, marketing tags)? - Default: anything that touches checkout, payment, shipping, tax, stock or an outside integration stays. Removal candidates come to you as a list for approval. Nothing is removed silently.

Priority: Q1 and Q3. With them I can go straight to the right half and know whether the largest fix is allowed.

## Plan

**Step 0: Safety net.** Take a full backup (files and database) and confirm it restores to staging. Make all changes there first. Apply changes to production during your quietest hours. After each production change, place a real test order through checkout, start to finish, and refund it.

**Step 1: Measure (1–2 days).**
- **Field data:** PageSpeed Insights, top section (real Chrome users, if there is enough traffic), and the Search Console Core Web Vitals report. This is what customers actually experience.
- **Lab data, mobile:** home, a category page, a product page, cart and checkout, each tested 3 times in WebPageTest or PageSpeed. Record time to first byte (TTFB), Largest Contentful Paint (LCP), total page weight, and request count and JavaScript size by domain.
- **Server:** Query Monitor on staging, to see slow database queries and time per plugin on each of those pages. Also note the PHP version, whether page caching or an object cache exists, and how many autoloaded options are stored in `wp_options`.
- Targets are set after this baseline, page by page, not now.

**Step 2: Hypotheses, then fixes in order of cost.** Each row is a guess until step 1 confirms it.

| If step 1 shows | Likely cause | Fix |
|---|---|---|
| High TTFB on uncached pages | Old PHP, no page or object cache, slow plugins or queries, overloaded shared server | Upgrade PHP to a supported 8.x, add page caching, remove the slow plugins Query Monitor names, clean up autoloaded options. If TTFB is still high, move to a host with server-level caching and Redis (Q3). |
| High TTFB on cart/checkout only | Those pages can't be cached; heavy plugins hook into them | Remove or replace the plugins that slow those pages; check WooCommerce cart fragments (`wc-ajax=get_refreshed_fragments`) |
| Large JS/CSS and many requests | Page builder plus plugins loading their files on every page | Unload plugin files on pages that don't use them (for example, a contact form only on Contact); turn on the builder's own performance settings; remove plugins you don't need |
| Slow LCP with a large hero image | Unoptimized images, lazy-loading on the main image | Compress and convert images to WebP/AVIF at the right sizes; don't lazy-load the main image, preload it instead |
| Much of the time spent on other domains | Chat widgets, pixels, review widgets, fonts | Delay non-essential scripts until interaction; self-host fonts; remove tags no one uses |

- **One change at a time, measured on the same pages as step 1. A change that doesn't improve its number is reverted.** Don't stack several optimization plugins on top of each other: they fight, and it becomes impossible to tell which one helped.

**Step 3: Page caching (usually the largest single gain).**
- Turn on page caching that **excludes** cart, checkout and my-account, and bypasses caching for logged-in users and anyone with a non-empty cart.
- **Go / no-go before enabling on production:** on staging, using two different browsers, put items in the cart in browser A and confirm browser B never sees them. Confirm checkout completes, and coupon, stock and price changes show correctly on product pages within the cache lifetime. If any of these fail, it doesn't go live. Serving one customer another customer's cart or stale prices costs more than a slow page.

**Step 4: Plugin audit.** List all 40 plugins with what each does, the pages it loads on, and its cost from Query Monitor. Mark each one keep, replace or remove, and send the list to you (Q4 default). Remove them one at a time on staging, running a checkout test after each.

**Step 5: Hosting decision.** If uncached TTFB is still the largest part of LCP after steps 2–4, move hosting. Use a WooCommerce-capable managed host or VPS with PHP 8.x, an object cache and server-level page caching. Before the move, test a full copy on the new host for checkout and payment webhooks. Lower DNS TTL a day before the move. At about 3k orders a month, do the switch in the quietest hour and pause stock changes while the database is copied.

**Step 6: Confirm.** Repeat the step 1 measurements. Field data takes about 28 days to fully reflect changes in Search Console and PageSpeed's field section.

## What I won't do, and why

- Rebuild the theme or drop the page builder: it's the most expensive option and only worth discussing if steps 2–5 leave front-end weight as the clear bottleneck.
- Go headless: a new architecture for a speed problem that hosting, caching and plugin cleanup usually solve.
- Remove a plugin without your approval: a plugin that looks unused may run an integration or a scheduled job.

## Other observations

- Forty plugins on shared hosting is also a security and update risk. Plan a regular update routine and keep a list of who owns each plugin.
- Check that WooCommerce scheduled actions (`Tools > Scheduled Actions`) aren't piling up with failed or pending jobs. A backlog slows the admin and sometimes the storefront.

## Need from you

- Answers to Q1 and Q3.
- wp-admin and hosting panel access, and whether a staging copy exists.
- The plugin list marked with anything you know is essential.


=============== RESPONSE R4-D ===============

"6 seconds" can come from two very different places, and the plan starts by finding out which. The first is server time: shared hosting running PHP for about 40 plugins on every uncached request. The second is the browser: page-builder CSS and JavaScript, large images and third-party scripts. A WooCommerce store has a third part that ordinary page caching cannot cover. The cart, checkout and account pages, and every visitor who has added something to the cart, always run uncached, so a page cache alone can make the homepage fast while checkout stays slow. The default plan is to measure, then make reversible changes one at a time on a staging copy, each kept only if it moves its number. Moving hosts or rebuilding the theme waits until the measurements point there. I have not seen the site, its plugin list or the host, so the plan rests on the defaults below. Targets come after the baseline, except where Google's published Core Web Vitals thresholds already define "good".

## Questions I would ask

Q1. What prompted this, and where does "6 seconds" come from (PageSpeed Insights, GTmetrix, a stopwatch on a phone, customer complaints)? - Default: a PageSpeed Insights mobile result for the homepage, and a worry about conversion and Google ranking. If the complaint is about cart and checkout, the uncached path and the hosting decision (step 9) move to the front.
Q2. What counts as good enough? - Default: field LCP at or under 2.5 s, and INP at or under 200 ms, on product and category pages (Google's "good" thresholds), and checkout server response under 1 s. Firm targets for each template follow the baseline.
Q3. Is changing hosting an option, and roughly what monthly budget? - Default: yes, if step 9's condition is met. If not, steps 5 to 8 are the whole plan, and checkout will stay limited by the server.
Q4. Which plugins are essential to the business (payment, shipping rates, invoices and NF-e, ERP or stock sync, reviews)? - Default: nothing in these categories is removed without a tested replacement. Step 3 labels every plugin.
Q5. Do you have a staging copy and daily backups, and who will make the changes (you, a developer, an agency)? - Default: the host provides staging and backups, and one developer does the work with your approval for each removal.

Priority: Q1 and Q3. With those, I can skip part of the measurement and decide early whether hosting is the main fix.

## Plan

### Phase 1 - Baseline and safety (days 1-3)

1. **Safety first.** Take a full backup (files and database) and restore it to a staging copy, then confirm the copy places a test order. Every change below is tried on staging first, then applied to production during a low-order hour. Keep a change log (date, change, before and after numbers) so any change can be undone individually.
2. **Measure four page types:** homepage, a category page, a product page, and cart/checkout with an item in the cart.
   - Field data: PageSpeed Insights mobile for each, recording field LCP, INP and CLS where Chrome has enough visits, plus the lab result.
   - Server time, cached against uncached: `for i in 1 2 3 4 5; do curl -s -o /dev/null -w "%{time_starttransfer}\n" "https://yourstore/produto/x/?nocache=$RANDOM"; done`, then the same without the query string. Uncached time above about 1 s means the server is the main problem; under that, with LCP still slow, it is the browser side.
   - The `server:` and cache headers from `curl -sI https://yourstore/` show whether a page cache exists and which web server runs (LiteSpeed changes the caching choice in step 5).
3. **Find the cost inside the server,** on staging. Install Query Monitor and record, per page type, the slowest database queries, the plugins whose hooks take longest, and outgoing HTTP calls made during page generation (each one blocks the page). Export the plugin list with `wp plugin list --status=active --fields=name,version --format=csv` if the host offers WP-CLI, otherwise from the Plugins screen. Label each plugin: essential (Q4), used, or unused.

**Start with (need no answers):**
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


=============== RESPONSE R4-E ===============

# Plan: make the WooCommerce store fast on mobile

Measure first, because the fix depends on where the six seconds go: waiting for the server, or loading and rendering the page. With shared hosting, about 40 plugins and a page builder, I expect both, and I expect the hosting to be the limit on cart and checkout, which cannot be cached. The plan below works from the cheapest and safest changes to the most disruptive, re-measuring after each one.

I have not seen the site, so the expectations here are from the setup you described, not from measurements.

## Target

Google's "good" thresholds for mobile, measured on real visitors at the 75th percentile:

- Largest Contentful Paint (when the main content appears) under 2.5 seconds.
- Time to first byte (server response) under 0.8 seconds.
- Interaction to Next Paint (responsiveness to taps) under 200 ms.

## Step 1: measure and prepare (1 to 2 days)

- **Pick five pages:** home, a category, a product, cart, checkout.
- **Real-visitor data:** PageSpeed Insights shows the Chrome field data for your site, and Search Console's Core Web Vitals report shows which page groups fail.
- **Lab data:** run WebPageTest on each page with a mid-range Android phone on 4G, from a location near your customers. Record time to first byte, Largest Contentful Paint, page weight and request count.
- **Split the problem:** time to first byte above about one second means the server side needs work. A fast first byte with a slow paint means the front end does.
- **Server-side detail:** install Query Monitor on a staging copy to see slow database queries, and which plugins account for the time on each page.
- **Safety:** make a staging copy and a full backup. Make every change on staging first, and place a test order after each one.

## Step 2: quick wins on the current hosting (week 1)

- **PHP version:** move to a current PHP 8 release with OPcache on, from the hosting panel.
- **Page caching:** install one caching plugin (LiteSpeed Cache if the host runs LiteSpeed; otherwise WP Rocket or similar). Exclude cart, checkout and account pages, which WooCommerce-aware plugins do by default. Remove any other optimisation plugins; several running together conflict.
- **CDN:** put Cloudflare in front for static files, compression and HTTP/3.
- **Images:** usually the biggest part of page weight.
  - Convert to WebP and resize to the dimensions actually displayed.
  - Lazy-load images below the fold.
  - Do not lazy-load the main product or hero image; preload it.
- **Fonts:** host them locally, limit to the weights in use, and set `font-display: swap`.
- **Cart fragments:** disable WooCommerce's cart-fragments request on pages that do not show a live cart count.

This step alone usually brings cached pages (home, category, product) close to the target for first-time visitors.

## Step 3: plugin and script diet (weeks 1 to 2)

- **Audit all 40 plugins** using the Query Monitor data. Sort each into: remove (unused or duplicated), replace (a lighter alternative exists), or keep.
- **Load assets only where needed.** Many plugins load their scripts and styles on every page; a form plugin has no business on a product page. Dequeue them per page with a small code snippet or an asset manager such as Perfmatters.
- **Third-party scripts:** chat widgets, pixels, heatmaps and review widgets. Remove those nobody uses; delay the rest until the visitor first interacts. Do not delay payment or analytics scripts on checkout.
- **Database:**
  - Clear expired transients and old sessions.
  - Check the size of autoloaded options; above about 1 MB slows every request.
  - Turn on High-Performance Order Storage if it is not already on.

## Step 4: hosting (decide after step 2's measurements)

If time to first byte on uncached pages (cart, checkout, logged-in users) is still above about one second, the shared hosting is the limit, and no plugin fixes that. At 3,000 orders a month, moving to managed WooCommerce hosting or a VPS with Redis object caching is justified: these are the pages where customers pay. A migration takes a day or two, with a short low-traffic window for the switch.

## Step 5: the page builder (only if still needed)

Page builders add heavy markup, styles and scripts. If the product and category pages still miss the target after steps 2 to 4:

- Turn on the builder's own performance settings and remove unused widgets and add-on packs.
- Rebuild just the product and category templates in the block editor or a light theme, keeping the builder for landing pages.

A full theme rebuild is the last resort; it costs the most and carries the most risk to design and search rankings.

## How we know it worked

- Re-run the same five WebPageTest pages after every change and keep the numbers in one sheet, so each change's effect is visible and regressions get caught.
- Real-visitor data lags by up to 28 days, so the field numbers confirm the result about a month after the work is finished.
- Track conversion rate and checkout completion alongside speed. Speed is the means; orders are the point.

## Risks

- **Caching showing the wrong content:** one customer's cart shown to another, or stale prices and stock. Test with two browsers and a logged-in account.
- **Script delaying or combining breaking checkout,** payment methods or tracking. Test a real order with each payment method after every change.
- **Removing a plugin that something depends on.** Deactivate on staging first; delete only after a week without problems.

## Questions I would ask

1. **Where does the six-second figure come from, and for which page?**
   Assumed default: a PageSpeed Insights or similar lab test of the home page, measuring full load on mobile.
2. **Is there budget to change hosting?**
   Assumed default: yes, if step 2's measurements show the server is the limit.
3. **Where are most of your customers?**
   Assumed default: one country, the same one the server is in.
4. **Who can make changes, and is there a staging site?**
   Assumed default: you have admin and hosting-panel access, and no staging site exists yet.
5. **Which page builder and theme?**
   Assumed default: Elementor or similar; the specific settings in step 5 depend on the answer.


=============== RESPONSE R4-F ===============

# Plan: making the WooCommerce store fast on mobile

Six seconds on mobile is common for a page-builder theme with about 40 plugins on shared hosting, and it's very fixable. The usual causes, roughly in order of impact, are: a slow server response (shared hosting plus uncached PHP and 40 plugins), too much JS/CSS from the builder and plugins, and heavy images. The plan is **measure → quick wins → structural fixes**, re-measuring after each step so we know what actually helped.

## Questions I would ask

1. **What does "6 seconds" measure, and on which pages?** That could be PageSpeed Insights, a stopwatch, or Search Console. *Default:* PageSpeed/Lighthouse mobile, mainly home, category and product pages, with checkout probably also slow.
2. **Which page builder and theme?** (Elementor, Divi, WPBakery, Avada…) *Default:* Elementor with a commercial theme.
3. **Which host and plan, and is moving hosts on the table?** *Default:* cheap shared hosting. A move to managed WordPress or a VPS (about US$25–60/month) is acceptable if the numbers justify it. At about 3k orders/month, a few seconds of mobile load very likely costs more than that in lost sales.
4. **Is there a staging site and recent backups?** *Default:* no staging. We create one first, because plugin and caching changes on a live store can break checkout.
5. **Who can make changes, and how much budget for a redesign?** *Default:* no full redesign now. Optimise what's there, and consider rebuilding the theme only if Phases 1–3 aren't enough.

## Phase 0: baseline and safety (day 1–2)

1. **Full backup and a staging copy** (many hosts have one-click staging. Otherwise use a plugin like WP Staging). All changes are tested there first, especially anything touching cart and checkout.
2. **Measure, and write the baseline down** for 4–5 key templates (home, category, product, cart, checkout):
   - PageSpeed Insights mobile: LCP, INP, CLS, TBT, plus **field data (CrUX)** if available. Field data is what real customers experience and what Google uses.
   - **TTFB** (server response time). On shared hosting with WooCommerce this is often 1.5–3 s by itself. Above about 600 ms, the server is a main bottleneck.
   - WebPageTest on a mid-range Android on 4G, to get a waterfall and request count and page weight.
3. **Profile the backend:** install Query Monitor temporarily to see slow queries, slow plugins and the number of DB queries per page. Check the **autoloaded options size** in `wp_options` (above 1 MB slows every request) and the WooCommerce scheduled actions table (Action Scheduler often has hundreds of thousands of old rows).
4. **Plugin inventory:** a spreadsheet of all ~40 plugins showing what each does, whether it's needed, and whether it loads assets on every page.

## Phase 1: quick wins (week 1)

**Page caching (usually the biggest single win)**
- Use full-page caching with the right WooCommerce exclusions: cart, checkout, my account, and pages with `woocommerce_items_in_cart` / session cookies. Options: the host's built-in cache (LiteSpeed Cache if the host runs LiteSpeed, which is common on shared hosting), WP Rocket, or similar. Use one caching plugin only.
- Put a **CDN** in front (Cloudflare free/Pro, or Cloudflare APO for WordPress), for static assets and optionally cached HTML. Make sure it bypasses on cart/session cookies.
- Turn off cart fragments (`wc-cart-fragments` AJAX) on pages that don't need them, or switch to a lighter mini-cart approach. It's a well-known source of uncached AJAX requests on every page.

**Images**
- Convert to WebP/AVIF, resize to the sizes actually displayed, and lazy-load below the fold, but **not** the main LCP image (hero or product image). That one should be eager-loaded with `fetchpriority="high"`.
- Regenerate WooCommerce thumbnails at correct sizes. Replace oversized sliders on mobile with a static hero image.

**Plugin cleanup**
- Remove plugins that aren't used or that duplicate something (it's common to find two SEO plugins, several sliders, old builders' add-ons, and unused social or analytics plugins).
- Stop plugins from loading assets on pages where they aren't used (Perfmatters or Asset CleanUp, for example forms plugin JS only on the contact page, WooCommerce scripts off non-shop pages where safe).
- Replace heavy plugins with lighter ones where possible.

**Third-party scripts**
- Audit tags: chat widgets, Facebook/TikTok pixels, Hotjar, multiple analytics tags. Load them through one tag manager, delay non-essential ones until user interaction, and drop duplicates.

**Re-measure.** It's typical to go from about 6 s to 2.5–3.5 s after Phase 1.

## Phase 2: front-end weight (weeks 2–3)

- **Page builder settings:** turn on its performance features (Elementor: optimized DOM output, improved asset loading, inline font icons, disabling unused widgets, Google Fonts local/off). Reduce DOM size on the heaviest templates (nested sections and columns from the builder are a common cause of a slow mobile INP).
- **CSS/JS:** generate critical CSS, defer non-critical JS, remove unused CSS (test carefully, since this is where layouts break), and minify. Avoid aggressive "combine all files" on HTTP/2.
- **Fonts:** self-host, limit to 2 families and a few weights, `font-display: swap`, and preload the main font.
- **CLS:** reserve space for images, banners and cookie bars, and avoid late-injected promos.
- Mobile-specific: hide desktop-only sections properly (builders often still load hidden content), and lighter product galleries.

## Phase 3: server and database (weeks 2–4, can overlap)

- **Hosting decision:** if TTFB on *uncached* pages (cart, checkout, logged-in, search) is still above about 800 ms after cleanup, move to managed WordPress/WooCommerce hosting or a VPS with PHP 8.2+/8.3, OPcache, enough PHP workers, and **Redis object caching**. Checkout can't be page-cached, so server speed decides how fast checkout feels. With 3k orders/month, shared hosting is likely already at its limit at traffic peaks.
- PHP version 8.2+ (often a 20–30% gain on its own). Check plugin compatibility in staging.
- **Database cleanup:** clear old Action Scheduler logs, expired transients, revisions, and leftover tables from removed plugins. Reduce autoloaded options. Enable **WooCommerce HPOS (High-Performance Order Storage)** if not already on, after checking that plugins are compatible.
- Replace WP-Cron with a real server cron, so cron jobs don't run during visitor requests.
- WooCommerce search and filters: if layered nav or search is slow, use an indexed filter plugin or search service.

## Phase 4: keep it fast

- Weekly monitoring of Core Web Vitals (Search Console + a PageSpeed/uptime monitor), and alerting if mobile LCP regresses.
- A simple rule: no new plugin or tracking script goes live without checking its impact on staging.
- Track business impact: mobile conversion rate, bounce rate and revenue per session before/after. That shows whether a hosting upgrade or theme rebuild is worth it.

## Targets

- Mobile LCP **< 2.5 s** (field data, 75th percentile), INP < 200 ms, CLS < 0.1.
- TTFB < 600 ms on cached pages (ideally < 200 ms from the CDN), and < 1 s on cart/checkout.

## If that's still not enough

If after Phases 1–3 the page builder is still the main bottleneck (huge DOM, heavy JS), the longer-term option is a lighter theme (a block theme, GeneratePress/Kadence with the block editor) for the key templates, starting with product and category pages. That's a real project, so I'd only recommend it once the cheaper steps are done and measured.

I'd start with Phase 0 (staging, baseline and plugin inventory) and the caching and image work. In my experience those three deliver most of the improvement in the first week.


=============== RESPONSE R4-G ===============

The plan is to measure first and then fix the store where it already runs: same host, same theme, cheapest reversible change first, with each change kept only if it moves its number. Most of the effort is in the pages a cache cannot serve. A page cache plus image and script trimming can make the home, category and product pages fast for anonymous visitors in a few days. Cart, checkout, My Account and every page a shopper sees after adding to cart are built fresh on each request, and on shared hosting with about 40 plugins that server time is usually where the 6 seconds comes from, and it is where the money is. So the plan splits the 6 seconds into server time and browser time before touching anything, and gives the uncacheable pages their own phase. I have not seen the site, its plugin list, its host or its database, and I have run none of the commands below. The plan rests on the defaults in the questions. Moving host and rebuilding the theme are kept behind a gate in Phase 3: either may turn out to be the right call, but only the Phase 1 numbers can show that.

## Questions

Q1. What prompted this: lost sales or abandoned checkouts, a PageSpeed or Search Console warning, or customer complaints? Default: conversions on mobile, so the work follows the buying path (product, cart, checkout) rather than the PageSpeed score of the home page. If it is the score or SEO, Phase 2 weights landing-page loading (Largest Contentful Paint) and Phase 2c moves later.

Q2. What is the "6 seconds", and what counts as good enough? Default: no target until the Phase 1 baseline exists. Google's "good" Largest Contentful Paint threshold (2.5 s for 75% of real visits) is a reference point, not a promise. If the 6 s is a PageSpeed lab figure, real visitors may already see something different, and Phase 1 shows which.

Q3. Do anonymous visitors see different prices, stock or content (currency switcher, geolocation, wholesale or membership pricing, a "recently viewed" block)? Default: no for anonymous visitors, yes for logged-in ones, so only anonymous, cart-empty pages are cached. If yes, those pages either get a cache variant per cookie or stay uncached, and the cache gains less.

Q4. Is changing host an option, and what does the current one provide (web server type, PHP version, Redis or Memcached, staging, SSH)? Default: stay put. The host question opens only at the Phase 3 gate.

Q5. Who makes the changes, and is there a staging copy plus admin, file and database access? Default: a staging clone is created in step 1 and every change goes there before production.

Priority: Q1 and Q3. Q1 decides which pages get the work. Q3 decides how much a page cache can do, and a wrong guess there can show one customer's cart to another.

## Plan

### Phase 1: Safety net and baseline (no production changes)

1. **Back up and clone.** Take a full backup (files and database) and restore it to a staging copy, with a host one-click staging or a cloning plugin. Check: staging loads, and a test order goes through with the payment gateway in test or sandbox mode. Set staging to "discourage search engines" and disable outgoing order emails, so the clone never mails real customers.
2. **Measure lab and field data on four URLs:** home, one busy category, one busy product, and cart with an item in it. Run PageSpeed Insights three times each and keep the median of LCP, Total Blocking Time, TTFB, request count and JavaScript bytes. Record the field-data panel ("what real users experience") if the site has enough traffic to show one.
3. **Split server time from browser time.** Time the first byte with curl, once as a cache-busting anonymous visitor and once with a cart session (see Start with). If uncached TTFB takes most of the 6 seconds, Phase 2b leads. If TTFB is low and LCP is high, Phase 2a leads.
4. **Profile the server side on staging** with the Query Monitor plugin: on the product and cart pages, record total query time, slow queries and the "Queries by Component" table, which names the plugins that cost the most. Install it on staging only, because it adds overhead.
5. **Inventory the plugins.** Export the active list, and next to each one write what it does, whether anyone still uses it, and whether it loads assets on every page. Expect overlaps: two SEO tools, several builder add-on packs, sliders, a security suite that scans on every request.

**Start with** (none needs an answer; replace `example.com` and the `wp_` table prefix with yours):

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


=============== RESPONSE R4-H ===============

On shared hosting with about 40 plugins, the 6 seconds is usually two separate problems: slow server responses, and a heavy page from the builder theme. They need different fixes, so the plan measures which one dominates on each page type before changing anything. Page caching fixes the server side for visitors who are just browsing. It cannot help cart, checkout or account pages, or any visitor who has something in their cart, and for a store doing 3k orders a month those pages matter most. If those pages stay slow after the plugins are trimmed, the next step is better hosting with an object cache, not more caching plugins. The plan works on a staging copy, makes one change at a time, keeps only changes that move a measured number, and places a test order after every change. Rebuilding the theme is left out: it takes weeks, and measurement usually shows it is not where most of the time goes. I have not seen your site, so the plan rests on the defaults below. Plugin and setting names are recalled and flagged where they appear.

## Questions I would ask

Q1. Where does "6 seconds" come from: PageSpeed Insights, a monitoring tool, analytics, or customers complaining? And which pages? Default: a PageSpeed mobile test of the home and product pages. If the complaint is about checkout specifically, phase 3 (the server side) moves ahead of phase 2.

Q2. What counts as fast enough? Default: Core Web Vitals in the "good" range in Google's real-user data (LCP up to 2.5 s, INP up to 200 ms, CLS up to 0.1, which are Google's published thresholds), plus a server response target for cart and checkout that I set after the baseline. I am not setting a seconds target before measuring.

Q3. Is changing hosting an option, and is there a monthly budget for it? Default: yes, if the measurements show the server is the main cost. If not, the plan stays on caching and plugin trimming, and the ceiling is whatever the shared host can deliver.

Q4. Which plugins are untouchable: payment, shipping, invoicing, ERP or marketplace syncs? Default: payment, shipping and anything that touches orders stay as they are. Everything else is a candidate for removal.

Q5. What access do I get? Default: a wp-admin administrator, the hosting control panel and SFTP, and a staging copy created from the host's panel or a staging plugin.

Priority: Q1 and Q3. Q1 decides which pages come first. Q3 decides how far the server side can go.

## Plan

### Phase 0: safety net (before any change)

- Take a full backup of files and database through the host's backup feature, and restore it once to staging, so you know restoring works.
- All changes are made on staging first. Each change goes to production on its own, with its date and the before and after numbers written down.
- **After every change:** place a real test order (a 100% coupon, or the gateway's test mode on staging) through cart, checkout and the confirmation e-mail. Revert at once if any step fails.

### Phase 1: baseline

**Start with** (none needs an answer):

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


=============== RESPONSE R4-I ===============

# Plan: make the store fast on mobile

A realistic target is under 2.5 seconds to the main content on mobile for the home, category and product pages. With 40 plugins, a page builder and shared hosting, I expect the 6 seconds to be split between a slow server response and heavy pages, and the two need different fixes. So the first step is measuring which one dominates, before changing anything.

I have not seen the site, so the causes below are the usual ones for this setup, not findings.

## 1. Measure (1 to 2 days)

- Record a baseline for four pages: home, a category, a product, and the cart or checkout.
  - PageSpeed Insights for real-user data (it shows what Google's ranking sees).
  - WebPageTest on a mid-range Android profile over 4G for a waterfall.
- Split each load into two numbers:
  - **Server response time (TTFB).** Above about 800 ms means hosting, missing caching or slow PHP and database work.
  - **Everything after it.** Images, CSS, JavaScript, fonts and third-party scripts.
- Install Query Monitor on a staging copy to see which plugins and queries cost the most per page.
- Take a full backup and set up staging before any change. Every later step is tested there first, and checkout is retested after each one.

## 2. Quick wins (week 1)

These are low risk and usually take seconds off:

- **Page caching** for visitors who are not logged in, with cart, checkout and account pages excluded. If the host offers LiteSpeed, use LiteSpeed Cache; otherwise one caching plugin, not several.
- **A CDN in front of the site** (Cloudflare's free tier is enough) for images, CSS and JavaScript.
- **Images:** convert to WebP, serve sizes that match the screen, lazy-load everything below the first screen, and do not lazy-load the main product or hero image.
- **PHP:** move to a current 8.x version with OPcache on, if the host allows it.
- **WooCommerce cart fragments:** stop the script loading on pages that do not show a live cart count.
- **Fonts and third parties:** host fonts locally, cut unused weights, and delay chat widgets, pixels and review widgets until after the page is usable.

Re-measure. If server response is now fast on cached pages, hosting matters less for browsing, though it still matters for cart and checkout, which cannot be cached.

## 3. Plugin audit (week 2)

- Rank the 40 plugins by cost, using Query Monitor and by disabling them one at a time on staging.
- Sort each into: remove, replace with something lighter, or keep but load only on the pages that use it.
- Typical offenders: sliders, several overlapping optimisation plugins, broken-link checkers, statistics plugins that write to the database on every view, social feeds, and page-builder add-on packs.
- Clean the database: expired transients, old sessions, completed scheduled actions, and oversized autoloaded options.

## 4. Hosting (decide after step 2, do in week 3)

At 3,000 orders a month, shared hosting is very likely too small, and the uncached pages (cart, checkout, account, admin) are where it shows. I would move to managed WooCommerce hosting or a small VPS with:

- dedicated resources and PHP workers;
- Redis object caching;
- server-level page caching.

The cost is small against the revenue of a store this size, and it is the only fix for a slow checkout. Migrate at a low-traffic hour, with orders frozen for the cutover.

## 5. Theme and page builder (weeks 3 to 4, only as far as the numbers require)

Page builders load large CSS and JavaScript bundles on every page. In order of effort:

1. Turn on the builder's own performance settings and unload its assets where they are not used.
2. Generate critical CSS and defer the rest.
3. Rebuild the three templates that carry the traffic (home, category, product) with native blocks or a lightweight theme, leaving the rest in the builder.

A full theme rebuild is the last resort. I would only propose it if step 3 still leaves product pages over target.

## How we know it worked

- Lab numbers on the four pages before and after each step, kept in one sheet.
- Field data (Core Web Vitals in Search Console) passing on mobile within about a month, since it reports a 28-day window.
- Conversion rate and checkout completion unchanged or better, checked after every step that touches cart or checkout.

## Questions I would ask

1. **Which pages are slow, and is the 6 seconds from a tool or from a phone in hand?** *Default assumed:* all main pages, measured by PageSpeed Insights on mobile.
2. **Is there budget to leave shared hosting?** *Default assumed:* yes, up to roughly the cost of managed WooCommerce hosting for a store this size.
3. **Where are most customers?** *Default assumed:* one country, so the server goes there and the CDN covers the rest.
4. **Which page builder and caching plugins are installed now?** *Default assumed:* Elementor or similar, with no working page cache.
5. **Who makes the changes, and is there a staging site?** *Default assumed:* one developer, and staging has to be created first.
