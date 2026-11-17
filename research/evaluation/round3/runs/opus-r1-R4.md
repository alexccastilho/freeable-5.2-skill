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
