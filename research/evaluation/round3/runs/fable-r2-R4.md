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
