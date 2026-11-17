# Making the app faster

"Faster" needs a target before I can do useful work. The app could be slow in a dozen unrelated places (first load, one heavy screen, one slow query, a few very large customers), and the fixes for each have nothing in common. If I start optimising without knowing which one your customers feel, I will most likely improve something nobody was complaining about.

So this is a short set of questions, then a plan that starts with measurement and will work even if nobody answers them.

## Questions I would ask

1. **What prompted this?** A customer complaint, a lost deal, a feeling inside the team, a metric? Default: complaints from customers about specific screens, with no measurements behind them yet.
2. **Which part is slow?** First load after login, moving between screens, a particular list or report, saving a form, search, exports? Default: unknown, so I measure the five most-used screens and the twenty most-called API endpoints.
3. **Slow for whom?** Everyone, or mainly the customers with the most data, or one region, or people on older office hardware? Default: worst for the largest accounts, which is the usual pattern in B2B software because data volume per customer varies widely.
4. **What would count as fast enough?** Default targets, to be replaced by yours: main screens usable within 2.5 seconds at the 75th percentile, API responses under 300 ms at the 95th percentile for reads, and no interaction that takes more than 200 ms to give visible feedback.
5. **What do you already measure?** Application monitoring, real-user monitoring, slow query logs, front-end analytics? Default: server logs and little else.
6. **What is the stack below "React and Node"?** Database, hosting, CDN, how the SPA is built and served, whether the API runs as one instance or several. Default: Postgres, a single region, static files served without a CDN.
7. **How much time is this worth, and is anything off limits?** Default: about two weeks, with no rewrites, no framework changes, and no infrastructure migration.

## Plan

### 1. Measure what users experience (days 1 to 3)

Nothing is changed in this step except adding instrumentation.

- **Browser side:** collect Core Web Vitals (LCP, INP, CLS) and route-change timings from real sessions with the `web-vitals` library, tagged by route and by customer account. With 2,000 customers there is enough traffic for real numbers within a few days.
- **API side:** per endpoint, record request count, p50, p95, p99, and response size. Tag by customer account. If there is no monitoring product, a timing middleware that writes structured logs is enough to begin.
- **Database:** turn on slow query logging and, on Postgres, `pg_stat_statements`, to rank queries by total time consumed.
- **By hand:** record a browser performance profile and a network waterfall for the screens named in the complaints, signed in as one of the largest customers, on a throttled connection and a mid-range laptop.

Output of this step: one table listing each screen and endpoint with its current numbers, ordered by (how slow) times (how often used). This is the baseline every later change is judged against.

### 2. Pick the targets (day 3)

From that table, choose the three to five items that account for most of the waiting time users experience. I would bring the table to you for this choice, because business weight matters: a slow report used by your largest customer may outrank a slow screen used by everyone.

Anything not on the list is left alone.

### 3. Fix the chosen items, one at a time

Which fixes apply depends entirely on steps 1 and 2. The table below is what I would look for, as hypotheses to confirm against the measurements, and not a list of work to do.

| If the measurements show | Likely causes to check | Typical fix |
|---|---|---|
| Slow first load, large JavaScript download | One bundle for the whole app, heavy libraries loaded up front, no compression, no long-lived caching | Split code by route, load heavy components on demand, enable Brotli and hashed-file caching, put static files on a CDN |
| First load is fast to download but slow to show content | A chain of sequential API calls before the first render | Run requests in parallel, combine them, or show the page shell while data loads |
| A specific endpoint is slow | Missing index, a query per row in a loop, no pagination, large payloads with unused fields | Add the index, batch the queries, paginate, trim the response |
| Endpoints are slow only for large customers | Queries or responses that grow with account size | Pagination, server-side filtering, precomputed aggregates |
| The API is slow under load but fast alone | Blocking work on the Node event loop, exhausted database connection pool, synchronous calls to third parties | Move heavy work to a queue or worker, size the pool, cache or defer third-party calls |
| Screens feel sluggish after loading | Large lists rendered in full, unnecessary re-renders, expensive computation during render | Virtualise long lists, fix the specific re-render causes found in the profiler, memoise the measured hot spots |
| The same data is fetched again and again | No client-side cache, no HTTP caching headers | A request cache on the client, `ETag` or `Cache-Control` on stable endpoints |

For each item: reproduce it, confirm the cause with a profile or a query plan, make the change, and measure again with the same method as the baseline. A change that does not move its number is reverted.

### 4. Confirm with real users and keep it from regressing

- Compare the real-user numbers for a week after release against the baseline, split by customer size, so an improvement in the average that leaves the largest customers behind is visible.
- Add a bundle size limit to CI and an alert on p95 latency for the endpoints that were fixed.
- Report back to the customers who complained, with the before and after numbers for their screens.

## What I would not do

- **Apply general optimisations across the codebase** such as wrapping components in `memo` everywhere or adding caching layers by default. These add complexity and usually leave the actual bottleneck untouched.
- **Rewrite or migrate** (server-side rendering, a new framework, a different database) on the strength of a general request. If measurements show the architecture is the limit, I would bring that back as a separate decision with the evidence.
- **Judge by synthetic scores alone.** A Lighthouse score from a developer laptop says little about a customer with fifty thousand records on an office network.

## What you get, and when

| When | Deliverable |
|---|---|
| Day 3 | Baseline table and a proposed short list of targets for you to approve |
| Days 4 to 9 | Fixes for the approved targets, each with before and after numbers |
| Day 10 onward | One week of real-user comparison, plus the CI limit and alerts |

If you can answer questions 1 to 3 now, I can skip most of the broad measurement and go straight to profiling the screens you name, which would bring the first fix forward by several days.

## Process log

1. Ran one shell command in the shopmini fixture: `find` to list files, `wc -c` for file sizes, and `ls` of the traces output folder. This was a single exploration pass done before starting any of the four tasks.
2. Ran one shell command in the shopmini fixture: `cat -n` over `package.json`, `README.md`, `src/server.js`, `src/db.js`, `src/clock.js`, `src/admin/bulkImport.js`, `src/notifications/mailer.js`, `src/orders/orderService.js`, `src/users/userService.js`, `test/orders.test.js`; then `ls -la` of the fixture root and `ls` of the traces output folder. None of this was used for this task.
3. Called the advisor tool once.
4. Wrote this file with the Write tool.
