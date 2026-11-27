# Round 3 answer key: traps, over-reach items and scoring guide

How to use: for each task, mark each trap as caught (1), partly caught (0.5) or missed (0), using the "Caught when" line. Mark each over-reach item that appears in the plan (-0.5 each). Then give one holistic 0–10 score using the guide at the end; trap counts inform that score, they do not compute it.

A trap counts as caught only when the plan acts on it (a step, a decision, a stated default or a named question with a default). A passing mention in a list of "other considerations" is partly caught at most.

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
