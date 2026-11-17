# Renaming Acme Notes to Inkwell

"Change the name everywhere" sounds like a find-and-replace. For a product with public SDKs, mobile apps, a domain and 40k paying customers, it isn't one. Some "names" are user-facing copy that should change on launch day. Others are **identifiers other people's code and devices depend on**, and changing those breaks integrations, logs people out, or orphans app installs. So I'd split the work into tiers and only blanket-replace the first one.

## Questions I would ask

1. **Is the trademark cleared, and do we already own the Inkwell domain, App Store/Play names and package names?** "Inkwell" is a common word. `inkwell` on npm and PyPI, and `inkwell.com`, may be taken.
   *Default:* legal clearance is done. We have (or will get) a domain such as `inkwell.app` and can publish under an npm scope (`@inkwell/sdk`) and a PyPI name such as `inkwell-sdk`. Nothing ships until those are confirmed.
2. **Is there a launch date or marketing moment?**
   *Default:* one coordinated public launch day. Prep work lands earlier behind flags or in unlisted form.
3. **Does "everywhere" include internal identifiers** (repo names, service names, DB names, AWS resources, bundle IDs)?
   *Default:* no. Internal-only identifiers stay as they are unless there's a specific reason to change them. Renaming them costs effort and adds risk, and no user benefits.
4. **How long must the old domain and API host keep working?**
   *Default:* indefinitely for redirects and the API host. We own `acmenotes.com`, so keeping it costs little, and letting it lapse invites phishing.
5. **Is the company or legal entity also renaming?** That affects invoices, terms of service, the privacy policy and payment descriptors.
   *Default:* product only. The legal entity stays the same.

## The tiers

### Tier 1: change on launch day (user-visible copy and branding)
- Web app UI strings, page titles, meta tags, favicon/logo, OG images.
- iOS and Android **display names**, store listings, screenshots and icons. Store review means submitting these days ahead and releasing manually on launch day.
- Transactional email templates, sender name, and the in-app and email footer.
- Marketing site, docs site, help centre, status page and social handles.
- Billing: Stripe (or equivalent) product names and the **card statement descriptor**. An unfamiliar name on a card statement causes chargebacks, so the customer email should mention it explicitly.
- Terms of service and privacy policy text (legal review).
- Error messages and support macros.

This is the tier where a code search is appropriate. I'd do it as a reviewed PR per client, not as one blind replace. I'd first add a single brand constant or config value (`PRODUCT_NAME`) so the copy is centralised and any future change is a config edit.

### Tier 2: migrate with backward compatibility (public contracts)
- **Domain.** Serve the web app from the new domain. 301-redirect `acmenotes.com/*` path-preserving. Keep TLS certificates on both.
  - **Sessions and cookies are scoped to the old domain.** Moving the web app logs all 40k users out unless we do a token handoff on redirect (a short-lived signed token that is exchanged on the new domain). Plan for that.
  - Update OAuth redirect URIs, SSO/SAML ACS URLs for business customers, CORS allowlists, CSP, and deep links / universal links (`apple-app-site-association`, `assetlinks.json` on the new domain, while keeping the old ones live).
  - Email deliverability: set up SPF, DKIM and DMARC on the new sending domain and warm it up gradually. Keep sending from the old domain until it's warm, or expect a spam-folder spike.
  - SEO: use Search Console change-of-address and keep the redirects permanent.
- **Public REST API.** Keep `api.acmenotes.com` working indefinitely, with no redirect, because many HTTP clients don't follow 301s on POST. Add `api.<newdomain>` as an alias pointing at the same backend. Make the new host the documented default.
  - Don't rename API fields, headers, error codes, webhook event names, or token prefixes (for example an `acme_` key prefix). These are contracts, and renaming them is a breaking v2 change. If something embarrassing must change, add the new name alongside the old one and deprecate.
  - Webhooks: if signatures use a header such as `X-AcmeNotes-Signature`, send both headers.
- **SDKs.**
  - Publish new packages (`@inkwell/sdk` on npm, `inkwell-sdk` on PyPI) with the new default base URL.
  - Keep publishing the old packages for a deprecation window. On npm, `npm deprecate acme-notes "Renamed to @inkwell/sdk"` plus a final version that re-exports the new package. On PyPI, a final release of `acme-notes` that depends on `inkwell-sdk` and re-exports it with a `DeprecationWarning`. Don't delete the old packages: deletion breaks lockfiles and frees the name for squatters.
  - Keep old import names and class names as aliases (`AcmeNotesClient = InkwellClient`) for at least one major version.
  - Update GitHub repo names (GitHub redirects renamed repos), README badges and the docs.
- **Mobile apps.**
  - **Do not change the iOS bundle ID or the Android `applicationId`.** Changing either creates a new app: existing users get no update, and you lose reviews, ratings and in-app subscriptions. Only the display name and the listing change.
  - Keep handling the old URL schemes and universal-link domains alongside the new ones.
  - Old app versions will keep calling the old API host for years. That's another reason it must stay up.

### Tier 3: leave alone, or do later and opportunistically
- Internal repo names, Python and JS module names inside the monolith, database names and table prefixes, AWS resource names, S3 buckets (they can't be renamed, only copied), log and metric names, feature-flag keys, Kafka topics, Docker image names.
- Analytics event names, because renaming them breaks historical dashboards.
- Mentions in old changelogs, blog posts and historical invoices. Those should stay accurate to their time.

I'd write this tier down explicitly so engineers don't "helpfully" rename it mid-project.

## Sequencing

1. **Inventory (week 1).** Grep every repo for `acme`, `AcmeNotes`, `acme-notes`, `acme_notes`, `acmenotes`, `ACME_` (case-insensitive) and classify every hit into Tier 1, 2 or 3. Also list everything outside the code: DNS, app stores, Stripe, email provider, OAuth apps (Google/Apple sign-in consent screens show the app name), social, Zendesk, etc. That gives us the real scope.
2. **Prep (weeks 2–4).** Domain, DNS, certificates and email authentication on the new domain, then start warm-up. Brand constant and copy PRs merged behind a flag. New SDK packages published. API alias host live. Cookie handoff built and tested. App store builds submitted with manual release. Legal texts updated.
3. **Customer comms.** Email all paying users about a week ahead covering what changes, what doesn't, the new card descriptor, and that their data and logins are unaffected. For API customers, send a separate developer notice with the SDK migration path and a commitment that the old host and packages keep working.
4. **Launch day.** Flip the flag, release the apps, enable the redirects, switch marketing. Support staffed up.
5. **After launch.** Watch login failures, 404s on the old domain, email bounce and spam rates, API error rates by host, SDK download split and support tickets. Once the new email domain is warm, cut sending over to it.
6. **Deprecation window (6–12 months).** Deprecation warnings in the old SDKs, then a final release. Keep the old domain redirect and the API host up indefinitely.

## What I can do right away

If you point me at the repos, I'll start with step 1: produce the categorised inventory of every occurrence, with a proposed tier for each. Then I'll make the Tier 1 copy change and the brand constant in each client as separate PRs for review. I won't touch Tier 2 identifiers until the domain and package names are confirmed. I won't touch Tier 3 at all unless you tell me to.
