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
