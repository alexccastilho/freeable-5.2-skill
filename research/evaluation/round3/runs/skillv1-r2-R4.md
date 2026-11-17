The first job is to find out which half of the 6 seconds is slow. One half is the server building the page. On shared hosting with WooCommerce and 40 plugins this is often 1–3 seconds before the browser receives anything, and no front-end optimization fixes it. The other half is the browser downloading and running what the page builder and plugins load. Each half has a different fix, and only the server half can justify moving hosts, so the plan measures first and then fixes in order of cost. It works without answers to the questions below. The answers mainly decide whether moving hosting is an option.

**Not seen:** the site, the plugin list, the hosting plan or any measurements. I don't know which page or tool the 6 seconds comes from.

## Questions I would ask

Q1. Where does "6 seconds" come from: which page, which tool, measured by whom? - Default: PageSpeed Insights on mobile for the home page. Step 1 measures again across the key pages anyway.

Q2. What access do we have: wp-admin, the hosting control panel, SFTP/SSH, a staging feature? - Default: wp-admin and the control panel, no SSH. Changes are tried on a staging copy first (the host's staging tool, or a cloned subdomain).

Q3. Is changing hosting on the table? - Default: yes, if step 1 shows server time is the main problem. No budget figure assumed: you get the measured difference to decide with. If not, the plan still runs, but the server half stays capped at what caching can do.

Q4. Which plugins are business-critical (payments, shipping, invoicing, ERP or marketplace sync, marketing tags)? - Default: anything that touches checkout, payment, shipping, tax, stock or an outside integration stays. Removal candidates come to you as a list for approval. Nothing is removed silently.

Answer first: Q1 and Q3. With them I can go straight to the right half and know whether the largest fix is allowed.

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

## Found, not touched

- Forty plugins on shared hosting is also a security and update risk. Plan a regular update routine and keep a list of who owns each plugin.
- Check that WooCommerce scheduled actions (`Tools > Scheduled Actions`) aren't piling up with failed or pending jobs. A backlog slows the admin and sometimes the storefront.

## Need from you

- Answers to Q1 and Q3.
- wp-admin and hosting panel access, and whether a staging copy exists.
- The plugin list marked with anything you know is essential.
