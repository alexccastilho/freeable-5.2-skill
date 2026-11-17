# Holdout answer key, round 2

## Scoring rule

- Each trap: **1** = caught (the plan names the specific issue and does something about it: a step, a decision, or an explicit question to the requester); **0.5** = vague (gestures at the area without the specific, e.g. "consider security" or "handle edge cases"); **0** = missed.
- Each over-reach item present in the plan: **-0.5**.
- Task score = sum of trap scores minus over-reach penalties. Max is the number of traps (10 per task).
- A trap is caught whether the plan resolves it or flags it as an open question, as long as the specific is named. Mentioning it only in a generic risk list with no consequence for the plan is 0.5.
- For H1, a claim about the code that is wrong (e.g. "reuse the existing admin auth middleware") earns 0 for the related trap even if the topic is mentioned.

---

## H1 - CSV export of orders (shopmini)

Code facts the key relies on: `src/server.js` has 4 routes and no auth, no error middleware; `src/db.js` creates tables with `CREATE TABLE IF NOT EXISTS` only; `orders` has `id, user_id, status, total_cents, tracking_code, updated_at`; `src/admin/bulkImport.js` updates rows directly and does not set `updated_at`; the only test file is `test/orders.test.js`, service-level.

### Traps

**H1-a (premise: there is no "admin area").** The repo is an API only; "admin" is one unauthenticated route, `POST /admin/shipments/import`, with no UI, no session and no login. The plan must say that "download from the admin area" means a new GET endpoint (or ask whether a page/button exists elsewhere), not assume a front end to add a button to.
*Caught:* states there is no admin UI in this repo and defines the deliverable as an endpoint (or asks who/what calls it).

**H1-b (no auth on anything).** No route has authentication or authorization, so an export endpoint publishes the whole order list to anyone who can reach port 3000. The existing admin route has the same problem, so "follow the existing pattern" means shipping it open.
*Caught:* notes the absence of auth in `server.js` and either asks how the service is exposed / how admin access is meant to be restricted, or gates the endpoint minimally. Building a whole auth system unasked is over-reach (see below).

**H1-c (premise: the data warehouse staff need is not in the schema).** `orders` has no line items, quantities, shipping address or customer name; a "list of orders" from this table is id, status, total, tracking code, timestamp. A picking or packing list cannot be produced.
*Caught:* lists the columns actually available and confirms with the requester which columns they need, pointing out that items/address do not exist here.

**H1-d (`updated_at` is unreliable, and there is no `created_at`).** `bulkImport.importShipments` sets `status` and `tracking_code` but not `updated_at`, while `markShipped` does. Any "orders since X" / "shipped today" filter or sort on `updated_at` is wrong for bulk-shipped rows, and order placement date is lost once an order is shipped.
*Caught:* identifies the bulkImport/`updated_at` inconsistency or the missing creation date, and its effect on date filtering or the date column in the CSV.

**H1-e (scope of the list: which orders, how many).** "The list of orders" is undefined: all orders ever, only `placed` (awaiting shipment), a date range? Unbounded export grows forever; `better-sqlite3` is synchronous, so `.all()` on the full table blocks the single-threaded server for every other request.
*Caught:* asks for or decides a filter (status and/or date) and addresses size, e.g. `.iterate()` with a streamed response, or a stated row cap.

**H1-f (CSV correctness: do not copy the existing CSV handling).** `bulkImport` parses with `split(',')` and no quoting; there is no CSV library in `package.json`. The export needs RFC 4180 quoting (commas, quotes, newlines) and neutralising of cells starting with `= + - @` (formula injection), which matters as soon as `users.name`/`email` or a free-text `tracking_code` is included.
*Caught:* specifies escaping/quoting and formula injection, or a deliberate library choice; not just "generate CSV".

**H1-g (spreadsheet behaviour of the specific fields).** `total_cents` is integer cents (export as `1000` or `10.00`? under what header?); `tracking_code` values that are long digit strings get turned into scientific notation or lose leading zeros in Excel; non-ASCII names need a UTF-8 BOM for Excel; `updated_at` is ISO UTC, not warehouse local time.
*Caught:* at least two of: money format, tracking-code mangling, encoding/BOM, timezone.

**H1-h (route placement and response headers).** `GET /orders/:id` already exists, so `GET /orders/export` or `/orders.csv` registered after it is swallowed (`Number('export')` is NaN, handler returns `res.json(undefined)`). The endpoint belongs under `/admin/...` like the import, with `Content-Type: text/csv` and `Content-Disposition: attachment; filename=...`.
*Caught:* chooses a path that does not collide with `/orders/:id` (or orders it explicitly) and sets the download headers.

**H1-i (personal data and the join to users).** A useful export probably joins `users` for name/email; that puts PII (and `marketing_opt_in` if `SELECT *` is used) into files that end up on warehouse PCs and in e-mail. `orders.user_id` is nullable with no enforced FK, so an inner join silently drops orders.
*Caught:* explicit column allow-list rather than `SELECT *`, PII minimised or confirmed, and LEFT JOIN / missing-user handling.

**H1-j (verification and rollback fitted to this repo).** Existing tests are service-level only, set `process.env.DB_PATH = ':memory:'` before requiring `db`, and stub `mailer.send`; `node --test test/` runs each file in its own process, so a new test file must repeat that setup. There is no HTTP test helper, but `server.js` exports `app` and only listens when run directly. Verification should include an HTTP-level test with awkward data (comma/quote in a name, null tracking code, empty table) and opening the file in the staff's actual spreadsheet tool. Rollback: the change is additive and read-only, so revert is enough, *unless* the plan adds a column or index, in which case `CREATE TABLE IF NOT EXISTS` will not alter the existing `shopmini.db` and a real migration is needed.
*Caught:* a concrete test approach compatible with the existing setup plus a real-file check, and a statement of rollback (or of the migration gap if schema changes are proposed).

### Over-reach (-0.5 each)

- **H1-x1.** Designing a full authentication/roles system, or an admin front end (React page, templates), as part of this plan rather than flagging the gap and asking.
- **H1-x2.** Refactoring unrelated code: rewriting `bulkImport.js`, moving mail sending to a queue, adding an ORM/migration framework, converting to TypeScript, fixing the README typo. (Noting the `updated_at` bug and proposing it as a separate fix is fine.)
- **H1-x3.** Building export infrastructure not asked for: background jobs with e-mailed links, S3 storage, scheduled exports, XLSX/PDF formats, a generic "export anything" framework.

---

## H2 - Rename "Acme Notes" to "Inkwell"

### Traps

**H2-a (premise: "everywhere" must not be taken literally).** The plan must split user-visible brand (copy, logos, store listing, e-mails, docs) from technical identifiers (iOS bundle ID, Android applicationId, DB/table names, env vars, internal module names, API paths, header names, URL schemes). The second group is mostly left alone or aliased.
*Caught:* an explicit rename / alias / do-not-touch classification, with bundle ID and applicationId named as never changing (changing them creates a new app and orphans the installed base).

**H2-b (premise: is the new name actually usable).** Before any work: trademark clearance for "Inkwell" in the relevant classes and markets, the domain, App Store / Play listing name, npm and PyPI package names, social handles. "Inkwell" is a common word and likely taken in several of these.
*Caught:* an availability/legal check as a gating first step, naming at least trademark plus one of domain/package names.

**H2-c (the old domain can never just be switched off).** `acmenotes.com` is baked into bookmarks, shared note links, old e-mails, released app binaries and released SDK versions. It needs permanent 301s for web, and API hosts on the old domain must keep serving (not only redirecting: many HTTP clients drop the body or auth header on redirect for POST).
*Caught:* keeps the old domain indefinitely, and distinguishes web redirects from keeping the old API hostname functional.

**H2-d (auth and identity bound to the domain).** Moving domains breaks: session cookies (everyone logged out), OAuth redirect URIs and the Google/Apple consent-screen brand (re-verification), SAML/SSO entity IDs configured by customers, WebAuthn/passkeys (bound to the RP ID, cannot be migrated), password-manager entries, CORS allow-lists, iOS universal links / Android app links association files, and custom URL schemes.
*Caught:* at least three of these named with a mitigation or a decision to keep auth on the old domain for now.

**H2-e (SDKs on npm and PyPI cannot be renamed).** Packages are published under a new name; the old ones stay, get a final release that re-exports or depends on the new one, and are deprecated, not unpublished. Exported symbols (`AcmeNotesClient`), env vars (`ACME_NOTES_API_KEY`), default base URL and User-Agent need aliases; a rename of public symbols is a semver-major change.
*Caught:* new package + deprecation shim for old + backward-compatible aliases for public names.

**H2-f (public API contract).** Brand strings in the wire contract, such as `X-Acme-*` headers, webhook signature header names, API key prefixes, error codes, media types, OpenAPI titles and webhook source IPs/hosts, are consumed by customer code. They must be kept or dual-supported with a versioned deprecation, not changed with the copy.
*Caught:* identifies wire-level brand identifiers as a separate category and keeps/dual-emits them.

**H2-g (mobile release mechanics).** Display name and store listing changes go through review with uncertain timing; old app versions keep the old name, icon and hard-coded hosts indefinitely; a renamed icon/name on the home screen without warning looks like a different app to users. Push certificates/keys and the bundle ID stay.
*Caught:* store review lead time in the schedule, old versions keep working, and in-app notice before the icon/name changes.

**H2-h (40k paying users: money and trust).** The card statement descriptor, invoices/receipts, and billing e-mails changing to an unknown name causes chargebacks and support load; e-mail from a new sending domain with no reputation and new SPF/DKIM/DMARC lands in spam or looks like phishing. Customers need advance notice from the old name/domain, a "formerly Acme Notes" period, and legal documents (ToS, privacy policy, DPAs, legal entity vs product name) updated.
*Caught:* statement descriptor or invoices, plus e-mail deliverability/phishing perception, plus advance customer communication. Two of three is 0.5.

**H2-i (sequencing: this is a launch, not a commit).** Marketing site, apps, e-mails, docs, SDKs and stores cannot change at different random times. The plan needs a brand switch that is configuration-driven or flagged, a cutover date with store approvals obtained beforehand, a dual-brand transition window, and coordination with marketing/support/legal. It should also ask what triggered the rename (legal dispute vs marketing choice), since that determines the deadline and whether the old name may keep appearing.
*Caught:* an ordered, phased rollout with a cutover mechanism and named non-engineering owners.

**H2-j (verification, rollback, and what must not be rewritten).** Inventory by searching all spellings (`Acme Notes`, `AcmeNotes`, `acme-notes`, `acme_notes`, `ACME_NOTES`, `acmenotes`) plus things grep cannot see: text inside images, PDFs, e-mail templates in third-party tools, translations, store screenshots, third-party listings and integrations. Do not rewrite user content, historical invoices, changelogs or existing export files. After launch, monitor old-domain traffic, login success, e-mail bounce rate, old-SDK usage. State which steps are irreversible (public announcement, published packages, store listing) and keep the rest behind a switch.
*Caught:* multi-variant inventory including non-code assets, at least one post-launch metric, and an explicit reversible/irreversible distinction.

### Over-reach (-0.5 each)

- **H2-x1.** A global find-and-replace across the codebase/database, or renaming internal identifiers, tables, repos, cloud resources and bundle/application IDs "for consistency".
- **H2-x2.** Retiring or setting an end date for `acmenotes.com`, the old API hostname, or the old npm/PyPI packages (including unpublishing), or forcing all users to update.
- **H2-x3.** Bundling unrelated work into the rename: visual redesign, new API version with breaking changes, pricing changes, re-architecture.

---

## H3 - Weekly releases to continuous deployment

### Traps

**H3-a (premise: what problem, and is CD the right target).** The plan should ask what the team wants to fix (lead time, painful Fridays, big risky batches, hotfix speed) and distinguish continuous *delivery* (always releasable, push-button) from continuous *deployment* (every merge goes to production unattended). It should also check that this is a decision the team can make alone (product, support, QA, any compliance obligations).
*Caught:* names the delivery/deployment distinction or asks for the motivating problem, and adjusts the target accordingly.

**H3-b (the 35-minute suite is the pipeline's clock).** With 14 engineers, a 35-minute gate means queued merges, stale results by the time they finish, batching (which recreates releases), and pressure to skip. The plan needs a target (roughly 10 minutes) and a method: parallelise/shard, split fast gate from slower post-merge stages, a merge queue. Flaky tests, tolerable weekly, now block every deploy, so flake rate must be measured and quarantined.
*Caught:* treats suite duration as a blocker with a number or mechanism, and mentions flakiness or merge queueing.

**H3-c (the Thursday manual QA pass is a safety net with unknown contents).** Before removing it, find out what it actually catches (defect log from recent weeks), convert those cases into automated checks or smoke tests, and redefine the QA role (exploratory testing behind flags, test design, production verification). Simply dropping it removes the only end-to-end check; keeping it as a gate means it is not CD.
*Caught:* analyses what QA catches and gives the QA function a concrete new place, including the people affected.

**H3-d (Django migrations under rolling deploys).** With per-merge deploys, old and new code run against the same schema during every deploy and every rollback. Migrations must be backward compatible (expand/contract, no rename or drop in the same deploy as the code change), must avoid long table locks on live traffic, and should be linted in CI. The same applies to Celery/queued task signatures if workers exist.
*Caught:* expand/contract or equivalent backward-compatibility rule for migrations, tied to deploy or rollback safety.

**H3-e (decouple deploy from release).** Weekly batching currently hides unfinished work. Per-merge deployment needs feature flags (or dark launches) and short-lived branches / trunk-based development; any release or long-lived feature branches in today's flow must go. Flag hygiene (ownership, removal) should be mentioned.
*Caught:* feature flags plus a change to branching practice.

**H3-f (the Friday release contains undocumented manual steps).** A weekly manual release usually includes things only the person doing it knows: running migrations by hand, `collectstatic`, cache clears, restarting workers, a maintenance window, a smoke check, a changelog e-mail. The plan must inventory the current runbook and check whether deploys are zero-downtime at all before automating frequency.
*Caught:* an explicit step to document the present release procedure and automate or eliminate each manual step, including zero-downtime deployment on AWS.

**H3-g (production safety net replaces the human gate).** Removing QA and the release manager means detection moves to production: health checks, error-rate and latency alerts tied to deploys, canary or blue/green with automatic rollback, and a rollback that takes minutes and has been rehearsed. Rollback is not possible past an incompatible migration, so the policy must say when to roll forward. Also who watches: on-call ownership and "you merge it, you watch it".
*Caught:* automated post-deploy checks with rollback, a rehearsed rollback, and on-call/ownership. Two of three is 0.5.

**H3-h (incremental path with exit criteria, and a way back).** Not a switch-over date. Stages such as: auto-deploy every merge to staging; twice-weekly then daily production releases; push-button deploy per merge; unattended deploy. Each stage has entry/exit criteria, and the process change itself is reversible (a deploy freeze / pause switch, return to the weekly cadence if change-failure rate rises).
*Caught:* at least three ordered stages with criteria, and an explicit way to pause or revert the new process.

**H3-i (measure before and after).** Record a baseline now: deployment frequency, lead time for changes, change failure rate, time to restore, plus what Friday releases currently break. Without it nobody can tell whether the move helped or set guardrail thresholds for H3-h.
*Caught:* baseline metrics captured before changes, with at least two named, and used as success or stop criteria.

**H3-j (everyone downstream of the weekly rhythm).** Support, product, marketing and customers currently learn what changed once a week; release notes, customer announcements and support briefing need a new mechanism (changelog from merges, flags-on announcements). Deploy-time policy needs deciding (late Friday or out-of-hours merges now go straight to production). The pipeline itself now holds production AWS credentials, so branch protection, required review and CI secrets handling become production controls; any audit or change-approval requirement must be satisfied by the pipeline record.
*Caught:* at least two of: stakeholder/release-notes communication, deploy-hours policy, pipeline access controls / change-approval evidence.

### Over-reach (-0.5 each)

- **H3-x1.** Prescribing a re-architecture as a prerequisite: breaking the monolith into microservices, moving to Kubernetes, or replacing the CI/CD vendor wholesale without a stated reason.
- **H3-x2.** Getting speed by weakening checks: deleting or skipping slow tests, dropping manual QA outright with no replacement, removing code review, or eliminating the QA role.
- **H3-x3.** A big-bang cutover ("from next sprint every merge deploys to production") or rigid mandates unrelated to the request (100% coverage requirement, mandatory pair programming, a fixed tool list).
