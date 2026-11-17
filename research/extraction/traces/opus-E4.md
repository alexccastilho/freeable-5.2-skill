# E4: "Make our app faster"

Happy to help, but "faster" could mean five different problems with five different fixes. If I start optimizing without knowing which one, I'll likely spend effort on something your customers don't feel. So the plan is **measure → pick the 1–3 biggest bottlenecks → fix → measure again**, and here are the questions that decide where to start.

## Questions I would ask

1. **What feels slow, and to whom?** Initial page load? Navigating between screens? Specific pages (reports, search, big tables)? Saving/submitting? Is it everyone or certain customers (large accounts with lots of data, a region, a browser)? Default: **specific data-heavy screens are slow for larger B2B accounts, and the initial load is somewhat heavy.** That's the most common pattern for a B2B SPA.
2. **Where is that coming from: support tickets, churn feedback, a sales complaint, or internal perception?** Is there a specific customer or deal driving this? Default: **customer complaints about a few screens.**
3. **What do we already measure?** APM (Datadog, New Relic, Sentry performance, OpenTelemetry), RUM / Core Web Vitals, slow-query logs on the database? Default: **error tracking only, no real performance telemetry.** Then step 1 is adding some.
4. **What's the stack below the Node API?** Which database, any cache (Redis), hosted where, how many instances, any CDN in front of the SPA? Default: **Postgres, no cache, SPA served without a CDN or with default caching headers.**
5. **What does "done" look like?** A target like "p95 API latency < 300ms on the top 10 endpoints" or "dashboard interactive in < 2s for our largest customer". Default: **I'll propose targets after the baseline (step 1).**
6. **Constraints?** Timebox, freeze periods, how risky changes may be (B2B customers dislike regressions more than slowness). Default: **about 2–3 weeks, incremental low-risk changes behind feature flags where possible.**
7. **Can I see the repo(s)?** I don't have the code here. With access I'd start with the bundle config, the API routes behind the slow screens, and the queries they run.

## Plan

### Phase 1: Baseline and locate the bottleneck (about 2–4 days)

Goal: a ranked list of where the time goes, backed by data, not guesses.

**Frontend (React SPA)**
- Lighthouse / WebPageTest on the 3–5 most important screens, using a realistic large account, not an empty test tenant.
- Bundle analysis (`webpack-bundle-analyzer` / `vite-bundle-visualizer` / `source-map-explorer`): total JS size, biggest dependencies, whether there's route-level code splitting.
- Chrome DevTools Performance + React Profiler on the slow screens: long tasks, wasted re-renders, huge unvirtualized tables.
- Network waterfall: request waterfalls (screen waits on A, then B, then C), duplicate requests, oversized JSON payloads, missing caching headers / compression.
- Add RUM (web-vitals → your analytics/APM) so we measure real customers going forward: LCP, INP, CLS per route.

**Backend (Node API)**
- APM or at least per-route latency logging (p50/p95/p99, request count). Rank endpoints by **p95 × call volume**: that's where customers feel it.
- Database: enable slow-query logging / `pg_stat_statements`. Find the top queries by total time, `EXPLAIN ANALYZE` them, and look for N+1 query patterns in the ORM.
- Check event-loop blocking (synchronous CPU work, large JSON serialization, sync crypto/fs) with `clinic.js` or event-loop-lag metrics.
- Check infra basics: instance CPU/memory saturation, DB connection pool size vs. waiting, API and DB in the same region.

**Output of Phase 1:** a one-page table (screen/endpoint, current p95 or LCP, cause, proposed fix, expected gain, effort). We agree on the top items together before I change code.

### Phase 2: Fix the top items (about 1–2 weeks)

The usual suspects in this kind of app, in rough order of payoff vs. effort. **Which of these actually apply depends on Phase 1.**

*Backend / data*
- Missing indexes on the queries behind slow screens (often the single biggest win).
- N+1 queries → joins or batched loads (DataLoader-style).
- Unbounded list endpoints → pagination / server-side filtering, and return only the fields the UI uses.
- Cache expensive, rarely changing results (per-tenant config, reference data, aggregate dashboards) in Redis or in memory with explicit invalidation. Be careful with tenant isolation in cache keys.
- Move slow side-effects (emails, exports, report generation) to background jobs.
- gzip/brotli compression on API responses.

*Frontend*
- Route-level code splitting (`React.lazy`), drop or replace heavy dependencies (moment → date-fns/dayjs, whole-lodash imports, etc.).
- Serve static assets from a CDN with hashed filenames + long-lived `Cache-Control: immutable`.
- Parallelize request waterfalls, or add a combined endpoint for a screen.
- Client-side data caching with stale-while-revalidate (React Query / SWR) so navigating back to a screen is instant.
- Virtualize long tables/lists (`react-window`/TanStack Virtual); memoize expensive components only where the profiler shows wasted renders.

### Phase 3: Verify and keep it fast

- Re-run the Phase 1 measurements on the same screens and accounts; report before/after numbers.
- Roll out behind flags / gradually; watch error rates as well as latency.
- Add guardrails so it doesn't regress: bundle-size budget in CI, alerting on p95 per key endpoint, a RUM dashboard per route.

## What I'd do first if you just say "go"

1. Get access to the repos and any APM/logs.
2. Run the bundle analyzer and Lighthouse on the main screens, and pull the top 20 endpoints by p95 × volume plus the top queries from `pg_stat_statements`.
3. Come back within a few days with the ranked bottleneck table and a proposed shortlist.

## Process log

1. Wrote this file. No files were read and no commands were run for this task (no application code for this app was available in the environment).
