# Round 3 answer key: traps, over-reach items and scoring guide

How to use: for each task, mark each trap as caught (1), partly caught (0.5) or missed (0), using the "Caught when" line. Mark each over-reach item that appears in the plan (-0.5 each). Then give one holistic 0–10 score using the guide at the end; trap counts inform that score, they do not compute it.

A trap counts as caught only when the plan acts on it (a step, a decision, a stated default or a named question with a default). A passing mention in a list of "other considerations" is partly caught at most.

---

## R1 — Production-readiness review of shopmini

Facts from the fixture the key relies on (all files were read):

- `README.md` calls it a "small order-management API used by our warehouse team"; `package.json` is at version 1.4.2, so it is already in use internally.
- `src/server.js`: four routes, no authentication, no validation, no error middleware, port 3000 hard-coded, Express 4 with `async` handlers.
- `POST /orders` takes `userId` and `totalCents` from the request body.
- `src/admin/bulkImport.js` updates rows directly ("written in a hurry"), bypassing `orderService.markShipped`.
- `src/notifications/mailer.js` sends inside the request, swallows errors, has no SMTP credentials or timeout, and sends from `orders@shopmini.example`.
- `src/db.js`: one SQLite file at a relative path, schema created with `CREATE TABLE IF NOT EXISTS`, no migrations.
- `test/orders.test.js`: two service-level tests with the mailer stubbed; nothing covers routes, the bulk import or the mailer. No lockfile, no CI config.

### Traps

**R1-a (premise and scope). The repo is an internal warehouse tool, not a customer-facing product.**
"In front of real customers" changes the threat model, and the code has no user registration, products, payment or customer login. The plan must ask or assume what customers will actually touch (the API directly, or a storefront that calls it) and scope the month to that.
Caught when: the plan names the gap between the README's stated audience and the request, and states a working assumption or a question with a default. Not caught if it silently reviews the code as if it were already a shop.

**R1-b. No authentication or authorisation anywhere, including `/admin/shipments/import` and `/orders/:id/ship`.**
Anyone who can reach the server can mark orders shipped, bulk-overwrite tracking codes, and read any order by guessing sequential IDs at `GET /orders/:id`.
Caught when: the plan ranks this at the top, names the admin and ship routes specifically, and separates customer access from staff access. Generic "add auth" with no route named is partly caught.

**R1-c. The client decides who the order is for and what it costs.**
`POST /orders` trusts `req.body.userId` and `req.body.totalCents`, so a caller can order as another user or with a total of 0 or a negative number. There are no line items or server-side prices to compute a total from.
Caught when: the plan says identity must come from the session and the total from the server (or from the trusted upstream system), not only "add input validation".

**R1-d. A failed order request hangs and can leave an orphan order.**
The `async` handler in Express 4 has no try/catch and there is no error middleware. With an unknown `userId`, either the insert rejects or `getUser` returns `undefined` and the mail template throws on `user.name` after the order row is already written. The client gets no response. Also, `GET /orders/:id` for a missing order returns 200 with an empty body instead of 404.
Caught when: the plan identifies the unhandled async rejection or the insert-then-throw ordering, and asks for error handling plus 404/400 responses.

**R1-e. The bulk import bypasses the order service and is not atomic.**
`importShipments` does not set `updated_at`, runs outside a transaction, counts rows it did not change (`n++` regardless of `changes`), and throws on a line with no comma (`tracking.trim()` on `undefined`), leaving the file half applied. It also does no status check, so it can re-ship or overwrite any order.
Caught when: the plan names at least two of these defects and proposes routing the import through `markShipped` or a transaction with per-line validation and a result report.

**R1-f. E-mail is unreliable in the way that matters for customers.**
The send is awaited in the request path with no timeout, so a slow SMTP server stalls checkout. Failures are logged with `console.error` and dropped, with no retry or record. The transport has no credentials, and the sender is an `.example` domain, so real delivery (SPF/DKIM, a real provider) is not set up. The README promises customers a confirmation e-mail.
Caught when: the plan covers both the latency coupling and the silent loss, and includes sender configuration. Proposing an outbox or a simple retry table is enough; a full queue system is not required.

**R1-g. Data durability: one SQLite file, relative path, no backup, no migrations.**
`shopmini.db` is created in whatever directory the process starts in, the schema has no migration path, and nothing backs it up. It already holds live warehouse data.
Caught when: the plan adds backups with a restore test and a migration approach before any schema change, and says SQLite can stay for this scale. Recommending a database change as the first step is over-reach (see below).

**R1-h (measurement and verification). The tests give almost no safety for the changes proposed.**
Two tests cover the service only, with the mailer stubbed, and the second test depends on the order the first one created. No route, import or failure-path test exists, and there is no lockfile or CI.
Caught when: the plan adds route-level and import tests for the risky paths before or with the fixes, defines a launch gate (for example: unauthenticated calls are rejected, a malformed CSV changes nothing, a mail failure does not lose the order), and says whether the existing tests were actually run.

**R1-i (rollback and safety). The warehouse team depends on this today.**
Adding auth, changing the import or the schema can break the end-of-day CSV workflow and the existing database. The plan needs a backup before migration, a way to deploy and roll back, and a check with the warehouse users.
Caught when: the plan treats the current users as a constraint: staging or a copy of the real DB, a backup before the first migration, and a rollback step.

**R1-j (prioritisation). The request is "what to improve first", with a one-month deadline.**
A flat list of twenty findings does not answer it. The plan must order the work and draw a cut line: must fix before launch (b, c, d, e, backups), should fix (mail reliability, observability, config such as port and env validation), and can wait.
Caught when: there is an explicit ordering with reasons and something is explicitly deferred.

### Over-reach (-0.5 each)

- **R1-x1.** Recommending a rewrite or re-platform as part of the first month: TypeScript migration, moving to Postgres, microservices, Kubernetes, or a message broker for e-mail.
- **R1-x2.** Designing the missing shop (catalogue, cart, payments, registration) without first asking whether that is in scope, or presenting it as part of "production readiness".
- **R1-x3.** Inventing findings not in the code (for example SQL injection, when every query is parameterised, or leaked secrets, when there are none), or padding the plan with generic checklist items of equal weight to the real defects.

---

## R2 — React Native crash rate rose from 0.5% to 3% after 4.2

### Traps

**R2-a (premise). Confirm the number before chasing it.**
"Crash rate" may be sessions or users, and Sentry may disagree with Play Console and App Store data. If 4.2 also upgraded the Sentry SDK or changed session tracking, the metric itself may have changed (for example ANRs, out-of-memory kills or JS errors now counted).
Caught when: the plan checks the definition, compares at least one second source, and checks whether instrumentation changed in 4.2.

**R2-b. Check whether the cause is 4.2 at all.**
Compare 4.1 over the same days. If 4.1 also got worse, the cause is likely a backend change, a remote config or feature flag flip, or an OS update that landed the same week, and a client fix will not help.
Caught when: the plan compares by release version and looks for non-client changes in the same window.

**R2-c. Segment before reading stack traces.**
3% overall can be 20% on one platform, OS version, device family or screen. Sort Sentry issues by "first seen in 4.2" and by affected users; one or two issues usually explain the jump.
Caught when: the plan splits by platform, OS version and device, and ranks new issues by user impact.

**R2-d. Stack traces may be unreadable.**
If source maps (Hermes), dSYMs or ProGuard/R8 mappings for 4.2 were not uploaded, the traces are minified or unsymbolicated. This is the first thing to check and fix.
Caught when: symbolication of the 4.2 build is an explicit early step.

**R2-e. Sentry can miss the worst crashes.**
Crashes during start-up, before the SDK initialises, and some native crashes or kills are not reported or are only sent on the next launch. Play Console Android vitals and Xcode Organizer are needed alongside Sentry.
Caught when: the plan uses store-side crash data as well, with this reason or a similar one.

**R2-f (safety). Stop the spread before the root cause is known.**
Halt the staged rollout on Google Play and pause phased release on the App Store if either is still in progress. Use a remote kill switch for the suspect feature if one exists.
Caught when: containment is a first-day step, separate from the diagnosis.

**R2-g (rollback). There is no rollback for store binaries.**
Users on 4.2 cannot be moved back to 4.1. The options are a 4.2.1 that reverts the offending change, an over-the-air JS update (only if CodePush or EAS Update is already set up, and only for JS-only causes), and expedited App Store review. The plan needs a timebox after which it reverts instead of continuing to debug.
Caught when: the plan says roll-forward is the only path, covers review lead time, and states when to revert versus fix. Proposing OTA without the "JS-only and already installed" condition is partly caught.

**R2-h. Upgrade path versus fresh install.**
A crash that only hits users who upgraded (persisted state, storage schema, cached data, a migration) will not reproduce on a clean QA install. The diff review of 4.1 to 4.2 should cover dependency and native module bumps, not only app code.
Caught when: reproduction includes upgrading from 4.1 with real data, and the diff review includes dependencies and native changes.

**R2-i (verification). Define how the fix is proven.**
Ship 4.2.1 in stages (for example 5%, 20%, 100%), compare crash-free sessions for 4.2.1 against 4.1's baseline per platform, and wait for enough sessions before widening. State a target (back to about 0.5%, or 99.5% crash-free) and who decides to proceed.
Caught when: there is a numeric target, a staged rollout, and a minimum sample or waiting time before each step.

**R2-j. The tail of users who do not update.**
A fix in the stores does not reach users who stay on 4.2. The plan should watch adoption and decide whether an in-app update prompt or a minimum-version gate is needed.
Caught when: adoption of the fix is tracked and a response to slow adoption is named.

### Over-reach (-0.5 each)

- **R2-x1.** Using the incident to upgrade React Native, switch architecture, replace the crash tool or refactor the suspect area, or bundling other changes into the hotfix.
- **R2-x2.** Releasing the fix to 100% at once, or forcing every user to update before the cause is confirmed.
- **R2-x3.** Front-loading process work (a full end-to-end test suite, a new release process, a long post-mortem programme) ahead of containment and the fix. A short prevention list at the end is fine.

---

## R3 — Add English and Spanish to a Portuguese-only Next.js shop

### Traps

**R3-a (premise and scope). Languages are not markets.**
The request says languages. Prices are in BRL and nothing says the shop ships abroad. The plan must ask or assume: translation for the same Brazilian operation, keeping BRL and current shipping, or selling to new countries (currency, tax, shipping, returns). It should also settle which Spanish (Latin American or Spain).
Caught when: the plan states the default (translate only, keep BRL) and lists what would change if the answer is new markets.

**R3-b (SEO safety). Do not move the existing Portuguese URLs.**
Organic search is the main traffic source. Putting Portuguese under a new `/pt` prefix changes every indexed URL. The safer default is Portuguese unprefixed and new locales under `/en` and `/es`; if the URLs must move, every one needs a 301 and the risk is accepted knowingly.
Caught when: the URL strategy explicitly protects current Portuguese URLs.

**R3-c. No automatic redirect by language or IP.**
Redirecting by `Accept-Language` or geolocation sends Googlebot (which crawls mostly from the US and sends no language header) to English, and breaks shared links. Offer a switcher or a banner suggestion instead; remember the choice in a cookie.
Caught when: the plan rejects forced redirects on existing URLs and names the crawler reason or the shared-link reason.

**R3-d. hreflang, canonical and sitemap done completely.**
Each page needs reciprocal `hreflang` entries for all three locales plus `x-default`, a self-referencing canonical per locale, localised metadata through `generateMetadata`, the correct `<html lang>`, and locale entries in the sitemap. Structured data and Open Graph tags need the locale too.
Caught when: at least hreflang with reciprocity, canonical per locale and sitemap are named as tasks.

**R3-e. The catalogue is the bulk of the work, not the interface strings.**
Product names, descriptions, categories, attributes and slugs live in Postgres and are edited in the in-house admin. The plan needs a translation data model (additive migration), admin screens to edit translations, a fallback rule when a translation is missing, and a decision on who translates and how new products get translated.
Caught when: the plan covers schema, admin and the translation workflow. Mentioning only a UI string library such as next-intl is a miss.

**R3-f. Untranslated or machine-translated pages should not be indexed as they are.**
An `/en` product page showing Portuguese fallback text is duplicate content, and bulk unreviewed machine translation is thin content. Launch a locale's pages as indexable only when translated (noindex or exclude from the sitemap until then), and phase by category or best sellers.
Caught when: indexing is tied to translation coverage.

**R3-g. Stripe checkout and the Brazilian checkout assumptions.**
Pass the locale to Stripe Checkout, keep charging in BRL, and format prices per locale without changing the currency. Local payment methods (Pix, boleto, instalments) and form fields such as CPF and CEP assume a Brazilian buyer; line-item names and Stripe receipts also carry language.
Caught when: the plan covers the Stripe locale and at least one of: payment methods, CPF/CEP fields, price formatting in BRL.

**R3-h. Transactional e-mails have no request to read the locale from.**
E-mails are sent from webhooks and background jobs. The customer's locale must be stored on the order or the account at checkout and used when sending; every template and subject line needs translating.
Caught when: the plan persists the locale and uses it for e-mails.

**R3-i. App Router mechanics.**
Adding a `[locale]` segment restructures every route, and middleware, static generation and caching must vary by locale (otherwise one language is served from another's cache). Hard-coded Portuguese strings in server and client components, validation and error messages, dates, numbers and plurals need extraction.
Caught when: the plan names the route restructuring and the caching or static-generation effect, plus an inventory of hard-coded strings.

**R3-j (measurement and rollback). Baseline, monitor and be able to switch it off.**
Record Search Console clicks, impressions and indexed pages for Portuguese before launch, then watch them and hreflang errors after. Track translation coverage and conversion per locale, and add a CI check for missing keys. Ship behind a flag, one locale or one section first, with additive database changes so rollback is removing the new routes.
Caught when: there is a pre-launch SEO baseline, a named post-launch check, and a rollback or staged path.

### Over-reach (-0.5 each)

- **R3-x1.** Building multi-currency pricing, international shipping, tax handling or separate country domains without the user asking for new markets.
- **R3-x2.** Recommending forced redirects by IP or browser language, or bulk machine translation of the whole catalogue published and indexed without review.
- **R3-x3.** Re-platforming content into a headless CMS or buying a translation management platform as a prerequisite, or moving the Portuguese URLs with no redirect plan.

---

## R4 — WooCommerce store takes about 6 seconds on mobile

### Traps

**R4-a (premise and measurement). "6 seconds" is undefined.**
It could be LCP, full load or a Lighthouse figure, on one page or all, in a lab test or from real users. The plan must first set a baseline per template (home, category, product, cart, checkout) on a mobile profile, using field data (CrUX/PageSpeed Insights or RUM) and repeatable lab runs.
Caught when: the first step is a baseline by page type with named metrics (LCP, TTFB, INP) and both field and lab sources.

**R4-b. Split server time from front-end time before choosing fixes.**
A high TTFB points to hosting, PHP, the database and missing caching; a low TTFB with slow LCP points to page weight, the page builder, images and third-party scripts. The split decides the whole plan.
Caught when: the plan measures TTFB separately and branches on the result.

**R4-c. Shared hosting limits what is possible.**
Shared plans often lack a persistent object cache (Redis), have few PHP workers, and cannot be tuned. Check PHP version and OPcache first. A move to managed WooCommerce hosting may be the largest single gain and is proportionate at about 3k orders a month, but it should be decided from the TTFB data, and a migration is itself a risky change needing its own plan.
Caught when: the plan treats hosting as a measured decision with a cost and a migration risk, neither ignored nor assumed.

**R4-d (safety). Page caching must exclude the dynamic shop pages.**
Cart, checkout, my-account and any page for a visitor with items in the cart or a logged-in session must not be served from the page cache, or customers see other people's carts or stale prices and stock. Cart fragments (`wc-ajax=get_refreshed_fragments`) are a known cost on every page.
Caught when: cache exclusions for WooCommerce are explicit. Cart fragments mentioned is a bonus.

**R4-e. Audit the 40 plugins by measured cost, not by count.**
Use Query Monitor or a profiler to find the plugins that add slow queries or load scripts and styles on every page. Some plugins are business-critical (payment, shipping, tax, ERP sync). Deactivate on staging, one at a time, never in bulk on the live store.
Caught when: the plan measures per-plugin impact and protects critical plugins.

**R4-f. The page builder: optimise first, replace later if at all.**
Replacing the theme is a redesign project, out of proportion as a first step. Start with what the builder allows (unused CSS and JS, DOM size, fonts, the hero section), and consider rebuilding only the highest-traffic templates if the data still shows the builder as the bottleneck.
Caught when: the plan sequences builder work this way and names theme replacement as a later, conditional option.

**R4-g. Front-end specifics that usually dominate on mobile.**
The LCP image must not be lazy-loaded and should be correctly sized and in a modern format; sliders and web fonts are common causes; third-party scripts (pixels, chat, analytics, reviews) often cost more than the theme. Aggressive JS defer or combine settings frequently break checkout and builder widgets.
Caught when: the plan covers the LCP image, third-party scripts, and the warning about JS optimisation breaking pages.

**R4-h. Database and background load.**
Autoloaded options, expired transients, sessions, Action Scheduler logs and order metadata grow on stores this age; wp-cron and admin-ajax add load on shared hosting. Check HPOS (high-performance order storage) status.
Caught when: at least autoloaded options or a database clean-up, with a backup first, is in the plan.

**R4-i (rollback and safety). It is a live store taking about 100 orders a day.**
Take a full backup (files and database) and work on staging. Never push the staging database to production, because it would overwrite orders placed meanwhile. Change one thing at a time, in off-peak hours, and after each change run a real purchase test (add to cart, coupon, payment, confirmation e-mail), with a stated way to undo it.
Caught when: backup, staging, one change at a time, a checkout test and a rollback step are present. The staging-database warning is a bonus.

**R4-j (verification and proportion). Targets, ordering and holding the gain.**
Set targets (for example LCP under 2.5 s at the 75th percentile on mobile, TTFB under 0.8 s) rather than a Lighthouse score. Re-measure after each change under the same conditions, noting that CrUX field data lags by about 28 days. Do the cheap, high-yield items first (PHP version, one page cache, CDN, images), then decide on hosting and theme. Watch conversion, and re-check monthly because plugin updates regress performance.
Caught when: there are numeric targets, re-measurement per change, and an ordering from cheap to costly.

### Over-reach (-0.5 each)

- **R4-x1.** Recommending a rebuild as the plan: headless front end, moving to Shopify, a custom theme from scratch, or a self-managed VPS for a team with no system administrator.
- **R4-x2.** Stacking several caching or optimisation plugins, or turning on every minify, combine and defer option at once.
- **R4-x3.** Deleting or deactivating plugins directly on the live site, or caching cart and checkout for speed.

---

## Holistic scoring guide (0–10, decimals allowed)

Score the plan as a whole, as an expert in that field who has to act on it. Use the trap marks as evidence, then adjust for the qualities below. Apply over-reach penalties after choosing the band; a plan with a harmful default (marked "safety" above, or any over-reach item that would cause damage if followed) cannot score above 6.

| Band | Meaning | Typical evidence |
| --- | --- | --- |
| 9–10 | An expert would ship this plan as is. | Catches about 8 or more traps, including the premise, verification and rollback traps. No over-reach. Steps are ordered, sized and assigned a first action. Unknowns are stated with a default. |
| 7–8 | Strong, with minor gaps. | Catches about 6–7 traps, including at least two of premise, verification and rollback. Gaps are omissions, not errors. At most one mild over-reach item. |
| 5–6 | Competent but generic, or with notable gaps. | Catches about 4–5 traps. Reads like a good checklist that would fit any similar project. Premise taken at face value, or verification is "test it". |
| 3–4 | Significant misses or harmful defaults. | Catches 2–3 traps. Misses the highest-risk item for the task (R1: no auth; R2: no containment or assumes rollback; R3: breaks Portuguese SEO; R4: unsafe caching or changes on live). Or leads with over-reach. |
| 0–2 | Wrong or unusable. | Addresses a different problem, invents facts, gives no order of work, or would cause damage if followed. |

### What moves a plan up

- **Grounding in specifics.** It uses the facts given: file and route names for R1; Sentry, both stores and 120k users for R2; App Router, the Postgres catalogue, BRL, Stripe and organic search for R3; shared hosting, 40 plugins, the page builder and order volume for R4. For R1, claims match the actual code.
- **Catching traps.** Especially the premise trap, and the single highest-risk item of each task. A caught trap with a concrete action counts more than three mentioned in passing.
- **Sensible defaults when unanswered.** It names the open question, picks the safer assumption, proceeds, and says what would change under the other answer. It does not stall on a list of questions.
- **Risk and verification.** Each risky step has a check that would fail if the step were wrong, a numeric target where one applies, and a way back.
- **Proportionality.** Effort matches the size of the problem and the deadline: one month for R1, days for R2, a small shop on shared hosting for R4. Things are explicitly deferred.
- **Actionability.** Clear order, a first step that can start today, rough sizes, and who or what each step depends on.

### What moves a plan down

- Generic best-practice lists with no ranking, or the same weight given to minor and critical items.
- Accepting the premise unexamined (R1: that the tool is ready to be customer-facing; R2: that the metric is comparable; R3: that languages mean only UI strings, or silently mean new markets; R4: that "6 seconds" is one known number).
- Verification stated as "test thoroughly" or "monitor", with no metric, threshold or sample.
- No rollback, or a rollback that does not exist (R2: reverting a store release; R4: restoring a staging database over live orders).
- Invented details presented as findings, especially for R1.
- Over-reach: each listed item is -0.5; unlisted scope creep of the same kind may be penalised the same way, up to -1.5 in total per task.
- Length without added decisions. A long plan is not penalised for length, but padding that hides the order of work is.

### Tie-breakers

- Between two plans with similar trap counts, prefer the one whose first three steps are right.
- A plan that catches fewer traps but would cause no harm outranks one that catches more and includes a harmful default.
- Asking a clarifying question is credit only when paired with a default; a plan that only asks questions scores no higher than 4.
