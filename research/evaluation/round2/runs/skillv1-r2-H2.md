My recommendation is to change the name people see everywhere and to leave the identifiers that other systems depend on exactly as they are. Doing a literal find-and-replace of "Acme Notes" / "acmenotes" across code and infrastructure is the costly, risky version of this job. Most of the risk sits in things that are bound to the old name or domain and break for users when it changes:

- passkeys and WebAuthn credentials (tied to the domain)
- the web app's offline storage (tied to the browser origin)
- OAuth and SSO redirect URLs configured by customers and partners
- app store bundle and package IDs, which cannot change
- package names on npm and PyPI
- the e-mail sending domain's reputation
- the name on customers' card statements

The text itself is quick to change. Those items take most of the effort, and the domain move is the step that needs gates.

I have not seen your code, infrastructure or contracts, so this plan rests on the defaults below.

## Questions I would ask

1. Is "Inkwell" cleared and secured: trademark search in your markets, `inkwell.com` (or the domain you will use) registered, app store names and social handles available? Default: the plan treats this as not yet confirmed, and nothing public happens until phase 0 is done. If the name is not cleared, stop: everything after phase 0 depends on it.
2. Does "everywhere" include the domain, or only the brand? Default: the brand changes now, and the product moves to the new domain in a separate, gated phase. `acmenotes.com` keeps working for good. If you want to keep `acmenotes.com` as the main domain for now, phase 4 disappears, and with it most of the risk.
3. Do internal identifiers (repository names, Python and JS module names, database names, environment variables, AWS resource names) need renaming? Default: no. Nobody outside sees them, and renaming them is work with nothing to show for it. If yes, it becomes its own engineering project after launch, one service at a time.
4. Is there a fixed launch date or announcement already promised? Default: no date until phase 1 has measured the scope. Launch day is the day the visible rename ships, not the domain move.
5. Do any enterprise contracts or DPAs name "Acme Notes" or `acmenotes.com` (SSO endpoints, IP allowlists, data-processing addenda)? Default: some do. They get a written notice and keep their old endpoints until they confirm.

Answer first: 1, 2 and 5. Question 1 can cancel the project. Question 2 decides whether the risky phase exists at all. Question 5 decides how long the old endpoints must live.

## Plan

### Phase 0: Secure the name (before anything public)

Trademark clearance, domains (including common typos), app store names, npm and PyPI package names, and social handles. Registering `inkwell` on npm/PyPI now costs nothing and stops someone else from taking it. Check: each item is registered to the company and recorded in one list.

Order: no announcement, customer e-mail or store listing until this is done. An announcement made before the domain or trademark is secured invites squatters.

### Phase 1: Inventory, and sort every hit into Change, Alias or Keep

Search all repositories, infrastructure config, the help center, marketing site, e-mail templates, app store listings, and Stripe and other vendor dashboards for `Acme Notes`, `AcmeNotes`, `acme-notes`, `acmenotes`, `acme_notes` and the logo files. Put each hit into one of three buckets:

| Bucket | Examples | Treatment |
|---|---|---|
| **Change**: text people read | UI strings, app display names, store listings, e-mail templates and sender name, help center, legal pages, logo and icons, card statement descriptor, marketing site | Rename |
| **Alias**: names others type or install | API host, SDK package names, docs URLs, support e-mail address | New name added, old name keeps working |
| **Keep**: identifiers bound to the old name | iOS bundle ID, Android `applicationId`, API key prefixes, webhook header names (e.g. `X-AcmeNotes-Signature`), OAuth client IDs, database and AWS resource names, deep-link schemes | Unchanged; documented as legacy |

Check: every hit is in a bucket, and the Keep list has been reviewed by mobile, API and infrastructure owners.

### Phase 2: Visible rename (launch day)

- Web, iOS and Android: strings, logo, app icon, display name. All of it ships behind one flag or config value, so web can switch on launch day while the mobile builds go through store review beforehand. The iOS bundle ID and Android package name do not change. On Android they cannot change without the app becoming a different app, and users would lose their install.
- App store listings: name, subtitle, screenshots. Submit early: store review time varies, and the listing name change rides on an app update.
- E-mail: the display name changes to "Inkwell". The sending domain stays `acmenotes.com` for now. A new sending domain needs SPF, DKIM and DMARC set up and a gradual warm-up, or password resets and notifications start landing in spam.
- Billing: change the Stripe statement descriptor. Tell users in the announcement e-mail that charges will now read "INKWELL". Otherwise an unfamiliar line on the statement brings disputes and chargebacks.
- Legal pages and the in-app "About" screen: new name, with a "formerly Acme Notes" line kept for a year.
- Announcement to the roughly 40k paying users goes out the same day, after the release is live. It covers the name, that nothing about their data or login changes, and the statement descriptor.

Check: a crawl of the web app and help center finds no "Acme Notes" outside the "formerly" lines. Screenshots of both mobile apps are reviewed.

Revert rule: the web rename is a flag, so a broken layout or a missing string gets reverted the same day. The mobile apps cannot be rolled back, so all mobile strings ship in a build that went through TestFlight and an internal Play track first.

### Phase 3: API and SDKs (new names added, old names kept)

- API: serve the same API at `api.inkwell.com` *in addition to* `api.acmenotes.com`, from the same backend. Do not redirect the old host. Many HTTP clients do not follow redirects on POST, or they drop the `Authorization` header when following one. Docs show the new host, and the old host stays supported with no end date announced.
- npm and PyPI: publish `inkwell` (or `@inkwell/sdk`) as the real package. Publish one final version of the old package that wraps or re-exports the new one, and mark it deprecated (`npm deprecate`; on PyPI a deprecation notice in the description and a runtime `DeprecationWarning`). Do not unpublish or yank the old package: that breaks every install pinned to it.
- Keep public class and function names (for example an `AcmeNotesClient`) available as aliases of the new names for at least one major version.

Check: the old SDK's test suite passes against the new host, and the new SDK's against the old host. A clean project that installs the old package name gets working code and a deprecation warning.

### Phase 4: Domain move for the web app (only if Q2 says yes; the gated phase)

Before moving, find out what is tied to the old origin:

- **Passkeys/WebAuthn:** credentials are bound to the relying-party ID (`acmenotes.com`) and do not work on `inkwell.com`. Users with passkeys will need to sign in some other way and register a new passkey, unless you use the related-origins mechanism. That mechanism is recent and browser support varies. I am recalling it from memory, so check current support before relying on it.
- **Offline notes:** IndexedDB, localStorage and service-worker caches belong to the origin. Unsynced drafts on `app.acmenotes.com` will not exist on `app.inkwell.com`. The old origin must confirm everything is synced before it sends the user over.
- **Sessions:** cookies do not cross domains, so everyone gets logged out unless you build a one-time token handoff.
- **OAuth/SSO:** Google, Apple and Microsoft sign-in configs; customers' SAML ACS URLs and IdP settings; third-party integrations' redirect URIs. Register the new URLs *alongside* the old ones.
- **Universal links / App Links:** keep `apple-app-site-association` and `assetlinks.json` served on both domains, and ship app builds that claim both before the move.
- **Content Security Policy, CORS allowlists, links already embedded in notes, shared-note URLs, and customers' firewall allowlists.**

Then move in stages: internal staff, then 1%, 10%, 50% and 100% of users. The old origin redirects each user only after its client confirms there is nothing left to sync. Shared and public note URLs on the old domain redirect with a 301 for good.

All of these must be true before the first external stage:
- Zero unsynced items on the old origin for every user in the internal stage after the handoff.
- Sign-in works on the new domain for password, Google, Apple, each SSO customer in the test set, and passkey (re-registration path).
- Both domains serve the app-link files, and the current app builds open links from both.
- A rehearsed way to stop redirecting (flag flip, no deploy).

Stop criteria for any stage: a support ticket or error log showing lost notes; a sign-in error rate on the new domain above the old domain's for the same cohort; any SSO customer unable to log in. When one of these hits, stop redirecting, leave users on the old origin, and fix before resuming.

Do not let `acmenotes.com` lapse, ever. Set it to auto-renew with domain lock on. Someone who buys an expired product domain gets your password-reset links, OAuth redirects and old SDK traffic.

### Phase 5: Long tail

Help center redirects, SEO (301s plus change-of-address in Search Console), partner listings and integration marketplaces, social bios, invoices and receipts, internal docs. Monitor search traffic and support tickets that mention the old name for a quarter.

## What changes for users and what replaces it

| Today, free with the current name and domain | After the rename, provided by |
|---|---|
| Existing passkeys work | Re-registration prompt on first sign-in at the new domain (or related origins, if supported) |
| Offline drafts stay in the browser | Sync check before the redirect |
| Users stay logged in | Token handoff, or one announced re-login |
| Links in notes, e-mails and docs resolve | Permanent 301s on the old domain |
| `pip install` / `npm install` of the old name works | Old package kept and deprecated, never removed |
| Mail lands in the inbox | Old sending domain kept until the new one is warmed up |

## Found, not touched

- The internal code rename (Q3). Left out of the plan by default; nobody outside sees those names.
- Webhook header names and API key prefixes carry the old name. Changing them breaks every integration, so they stay.

## Need from you

- Trademark and domain status (Q1) and the answer on the domain (Q2).
- The list of enterprise customers with SSO or contractual endpoints (Q5).
- Who owns mobile, API/SDKs, infrastructure, support and marketing for this. I have not given a timeline: it depends on that and on the phase 1 inventory.
