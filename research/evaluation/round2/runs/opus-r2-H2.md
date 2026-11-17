# Renaming Acme Notes to Inkwell

I'd push back on doing this literally as "everywhere." The name appears in two different kinds of places, and they need different treatment:

- **Brand surfaces** are places people read the name: UI copy, app store listings, emails, the marketing site, docs, legal pages. These should all say Inkwell, and should do so on the same day.
- **Identifiers** are names other systems depend on. Examples: the domain, API hostnames, SDK package names, iOS and Android bundle IDs, OAuth redirect URIs, webhook header names, cookie domains, and database and infrastructure names. Changing one of these breaks someone's integration, a mobile install, or a login. Some of them can't be changed at all.

So the real job is to rebrand everything users see, add Inkwell versions of the public identifiers alongside the old ones, keep the old ones working for a long time, and leave internal-only identifiers alone.

## Questions I would ask

1. **Which domain do we own for Inkwell, and has the trademark been cleared in our markets?**
   Default: we own `inkwell.<tld>` (I'll write `inkwell.app` below as a placeholder) and legal has cleared the name. If the trademark isn't cleared, nothing below should start, because "Inkwell" is a common word.
2. **Is the company or legal entity changing too, or only the product?**
   Default: product only. If the entity is also changing, then terms, privacy policy, invoices, the Stripe statement descriptor, the DPA and the App Store / Play seller name become a separate legal track.
3. **Is there a fixed launch date, for example tied to a marketing announcement?**
   Default: no fixed date. We set a "flip day" once the compatibility work (Phase 1) is done, and roughly 6–8 weeks out is realistic.
4. **Does "everywhere" include internal code: repo names, module and class names, database and table names, AWS resources, env vars?**
   Default: no. Renaming internal identifiers is risky, and customers never see them. We rename them later if the team wants to, one at a time, and never as part of launch.
5. **Who owns customer communication: in-app notices, the email to the ~40k paying users, and API-customer notices?**
   Default: product/marketing write the copy, and engineering provides the timing and technical details. API customers get a dedicated notice with migration steps.

## What changes, and how

| Area | Treatment |
|---|---|
| Web app UI, emails, notifications, in-app copy, help center, marketing site | Rename fully on flip day. |
| **Domain `acmenotes.com`** | Add the new domain and serve both. On flip day, 301-redirect web traffic to the new domain, and **keep the old domain and its DNS indefinitely**. Old links in years of emails, shared notes, bookmarks and SEO all depend on it. Never let it expire. |
| Auth / sessions | Cookies are scoped to the domain. Moving users from the old domain to the new one logs them out unless we plan for it, e.g. a session handoff or simply accepting one re-login. Add the new redirect URIs to every OAuth/SSO provider (Google, Apple, SAML customers) **before** keeping the old ones becomes optional. Enterprise SAML customers have the old ACS URL configured on their side, so the old endpoints must keep working. |
| **Public REST API** | Add `api.inkwell.app` as an alias. **`api.acmenotes.com` keeps working with no announced end date**, and if one is ever set, it's 12+ months out. If any header or field contains the brand (e.g. `X-AcmeNotes-Signature` on webhooks), accept or send both the old and new names. Never only the new one in the same API version. |
| **SDKs on npm and PyPI** | Publish new packages (e.g. `@inkwell/sdk`, `inkwell` on PyPI, if those names are available, so check and reserve them **now**). Keep the old packages: a final release that wraps the new package, with deprecation notices (`npm deprecate`, a PyPI classifier/README note, and a runtime warning). Keep the old packages patched for security fixes during the deprecation window. Never unpublish. |
| **iOS app** | Change the display name, App Store name, screenshots and icon. **Don't change the bundle ID.** A new bundle ID is a new app, and existing users wouldn't get the update. Changing the name goes through App Store review, so submit ahead and release manually on flip day. |
| **Android app** | Same approach. **Don't change `applicationId`.** Changing it creates a separate app with zero installs. Change the label and Play listing, using staged rollout or managed publishing so it goes live on flip day. |
| Universal links / app links | Add the new domain's `apple-app-site-association` and `assetlinks.json`, and keep the old domain's files. Otherwise links stop opening in the apps. |
| Transactional email | Sending from the new domain needs SPF/DKIM/DMARC set up and a **warm-up period** first, or 40k emails start landing in spam. Start warming weeks ahead. Keep replies to the old addresses working. |
| Billing | Stripe statement descriptor, invoice templates, receipt emails. An unfamiliar name on a card statement causes chargebacks, so tell customers about it in the announcement email. |
| Third parties | Status page, support desk, social handles, analytics properties, app review contacts, Slack/Zapier/other integration marketplace listings. |
| Internal code, infra, DB | Leave as is (question 4). Add a short note in the repo README explaining the history. |

## Phased plan

**Phase 0: Inventory (week 1)**
- Grep every repo (web, iOS, Android, API, SDKs, infra, docs, email templates) for the variants: `Acme Notes`, `AcmeNotes`, `acmenotes`, `acme-notes`, `acme_notes`, `ACME_NOTES`.
- Sort each hit into *brand string*, *public identifier* or *internal identifier*.
- Also check places grep won't reach: config in third-party dashboards, image assets with the logo baked in, store listings, and localized strings in every language.
- Output: a spreadsheet with an owner for each row.

**Phase 1: Compatibility groundwork (weeks 1–4, nothing visible changes yet)**
- Register the new domain, set up DNS and TLS, and serve the app and API on both domains.
- Add the OAuth/SSO redirect URIs and the universal-link files for the new domain.
- Reserve the npm/PyPI names and social handles. Start the email domain warm-up.
- Add dual header support to the API and webhooks.

**Phase 2: Prepare the brand change behind a flag (weeks 3–6)**
- Move brand strings into one place: a product-name constant, i18n keys and email templates. Then the switch is a config flag, not a big-bang edit across hundreds of files.
- Prepare the new assets: logo, icons, store screenshots, OG images, favicons.
- Submit the mobile builds with the new name, held for manual release.
- Publish the new SDK packages under a prerelease tag. Prepare the docs site on the new domain.
- Write the customer emails, the in-app banner and the API migration guide.

**Phase 3: Flip day**
1. Turn on the brand flag on web.
2. Release the mobile builds.
3. Turn on web redirects from the old domain to the new one, with the API excluded.
4. Publish the SDKs as stable and deprecate the old ones.
5. Send the announcement email.

Watch login success rate, API error rate split by hostname, email bounce and spam rates, and support volume. Rollback is turning the flag off and removing the redirect. Only that part needs to be reversible, and Phase 1 keeps it that way.

**Phase 4: Long tail (months)**
- Watch old-domain API and SDK traffic and contact the heaviest remaining users directly.
- Remove old brand strings that slipped through.
- Decide whether any internal renames are worth doing at all.
- Keep `acmenotes.com` registered permanently.

## What I'd do first if you want me to start

Run the Phase 0 inventory across the repos you point me at, and come back with the categorized list and an estimate of the size of the "brand strings into one place" refactor. That list is what makes the rest of the plan concrete. Until it exists, a find-and-replace across the codebase would break SDK imports, bundle IDs and stored data in ways that only show up after users are affected.
