# Answer keys. Written before any arm ran.

Scoring per trap: 1 = caught explicitly (named and handled in the plan, or asked as a question with a sensible default), 0.5 = gestured at vaguely, 0 = missed.

## V1 (8 points)
- V1-a: `src/admin/bulkImport.js` marks orders shipped with a raw UPDATE, bypassing `markShipped`. A hook placed only in `markShipped` misses bulk shipments, which are probably the majority path (end-of-day CSV).
- V1-b: Reuse the existing `notifications/mailer.js` and its `templates` map; don't build a new e-mail path.
- V1-c: Idempotency. Re-importing the CSV, or calling /ship twice, must not send duplicate e-mails. Needs a "notified" flag or a check that the status actually transitioned.
- V1-d: Mail is sent synchronously in the request path. A bulk import of hundreds of orders would block or slow down. Needs queueing or batching, or at least an explicit decision.
- V1-e: Failures are swallowed (`catch` + console.error). Decide on retry and visibility, so a customer doesn't silently get nothing.
- V1-f: Tests stub `mailer.send` and use the injectable clock. The plan should extend the tests in that style, including a test for the bulk path.
- V1-g: The e-mail content needs a tracking code or link. bulkImport also does not set `updated_at` (a bonus observation).
- V1-h: Asks or decides on a product question: which carrier/link format, or whether opt-out is needed. Transactional mail should not be gated on `marketing_opt_in`.

## V2 (9 points)
- V2-a: Active Stripe subscription: cancel it, decide on proration/refunds, and stop future charges.
- V2-b: Workspaces owned by the user that have other members: transfer ownership or block deletion. Don't cascade-delete other people's data.
- V2-c: Legal and accounting retention (invoices, tax records) versus erasure (GDPR/LGPD). Anonymise rather than hard-delete where retention applies.
- V2-d: S3 uploads must be deleted, including the shared ones.
- V2-e: Revoke sessions, API tokens and OAuth grants immediately.
- V2-f: Grace period or soft delete with undo. The action is irreversible.
- V2-g: Re-authentication or strong confirmation before deletion.
- V2-h: Backups and third-party processors (analytics, e-mail provider, Stripe customer object) still hold the data. Document or handle it.
- V2-i: Asks why or what drives it (legal requirement, app-store rule, user requests). The answer changes how far deletion must go.

## V3 (7 points)
- V3-a: Challenges the premise and asks what problem JWT solves here. For a server-rendered Django app with Redis sessions, JWT is often a downgrade. Proposes keeping sessions if no real driver.
- V3-b: Revocation and logout: stateless JWTs can't be revoked without a denylist, which reintroduces state.
- V3-c: Token storage: localStorage (XSS exposure) versus cookies (CSRF still needed). Django's CSRF protection relationship.
- V3-d: Migration of currently logged-in users: accept both sessions and JWT during a transition, with no mass logout.
- V3-e: Key management and rotation, algorithm pinning, short expiry plus a refresh-token design.
- V3-f: Scope: maybe only the React widget or an API needs tokens; a hybrid approach.
- V3-g: Rollback plan and a feature flag.

## V4 (3 points; anti-overplanning control)
- V4-a: Just does it or proposes the one-line edit, with no multi-phase plan, no clarifying questions to the user, and no test plan. Clear over-planning (more than about 10 lines of plan or questions) scores 0 here.
- V4-b: Checks for the same typo elsewhere (grep), or notes it only occurs once.
- V4-c: Verification proportional to the change, e.g. re-reading the line. Running the full test suite is not needed.

## V5 (7 points)
- V5-a: Measure or profile first (query count, N+1, missing indexes) before choosing caching. Caching might be the wrong fix.
- V5-b: Customer-specific prices. A page or fragment cache keyed without the customer or price group leaks one customer's negotiated prices to another. This is a security and commercial incident.
- V5-c: Invalidation on the hourly price import; tie cache keys to the import version.
- V5-d: Asks how much staleness is acceptable for prices and stock.
- V5-e: Cache stampede or thundering herd at expiry or after the import.
- V5-f: Establishes a baseline metric and a target, then verifies the improvement.
- V5-g: Chooses the cache layer deliberately (query, fragment, per-customer, CDN for anonymous) and explains why.

## V6 (8 points)
- V6-a: Internet or ISP installation lead time, often weeks, so it must be ordered well in advance. It's the classic Monday failure.
- V6-b: Building logistics: elevator or loading-dock booking, the movers' insurance certificate required by the building, parking.
- V6-c: IT equipment: labelling, network/server/printer setup, and testing everything before Monday 8am.
- V6-d: Fallback if the new office isn't ready Monday: remote-work plan, communicated in advance.
- V6-e: Notify clients and suppliers of the address change; mail forwarding; update the website, invoices and registrations.
- V6-f: Keys, access cards and alarm codes for both buildings; old-lease move-out obligations and condition.
- V6-g: Owner and decision-maker, budget, and a timeline working back from the weekend (it starts weeks before, not Friday).
- V6-h: Asks or decides about staff involvement (packing own desks), and furniture: new versus moved.

## Global quality dimensions (judged pairwise, 1–5 each)
- Q1 Clarifying questions: few, high-value, each with a stated default assumption.
- Q2 Grounding: references real files and constraints instead of generic advice.
- Q3 Risk and verification: each risky step has a check or rollback.
- Q4 Proportionality: plan size matches task size.
- Q5 Actionability: an implementer could start immediately.
