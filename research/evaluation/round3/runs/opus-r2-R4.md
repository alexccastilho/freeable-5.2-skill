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
