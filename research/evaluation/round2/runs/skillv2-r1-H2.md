I plan this in two stages. Stage 1 changes everything a person sees: the apps, the website, e-mails, app store listings, docs, the SDK and API documentation. Stage 2 moves the identifiers other people's systems hold: the domain, the API hostname, the SDK package names. The work is in Stage 2, not in the find-and-replace. Some of those identifiers cannot be changed in place: the iOS bundle ID and Android application ID (changing either publishes a new app, and 40k users would not get updates), passkeys and "Sign in with Apple/Google" registrations tied to `acmenotes.com`, every SDK install and integration pointing at the old API host, and every link in old e-mails and documents. So "everywhere" in this plan means everywhere a customer reads the name; the old identifiers keep working indefinitely behind redirects and aliases, and internal names (repositories, code symbols, database names, bundle IDs) stay as they are. I have not seen your code or infrastructure; the plan rests on the defaults below. If the rename is forced by a trademark claim with a deadline, the order changes: see Q1.

## Questions I would ask

1. **What is driving the rename: our own rebrand, or a trademark dispute or acquisition?** Default: our own rebrand, with a launch date we choose. If it is a legal claim, the deadline sets the plan: Stage 1 is done first and fast, and the claim's wording decides whether the old domain and package names may stay live as redirects (usually yes, but legal counsel should confirm).
2. **Is "Inkwell" cleared, and which domain and handles do we own?** Default: trademark search done; a new domain (written `<new-domain>` below) and the npm, PyPI, App Store and social handles not yet secured. Securing them is step 0, before anything public. "Inkwell" is a common word; the npm package `inkwell` and PyPI `inkwell` may already be taken, in which case the SDKs become `@<new-scope>/sdk` and `inkwell-sdk` or similar.
3. **Is the new name secret until launch day?** Default: yes. Nothing with the new name goes into public repositories, package registries, DNS records others can see, or app store submissions before the announcement, except under neutral names.
4. **How do users sign in (passwords, Google/Apple sign-in, passkeys, SSO for business customers)?** Default: password plus Google and Apple sign-in, no passkeys. If passkeys or customer SSO (SAML) exist, the web app stays on `acmenotes.com` hostnames until a migration path for those is built, because passkeys are bound to the domain and SSO customers have our URLs configured in their identity providers.
5. **Who owns each surface (web, iOS, Android, API/SDK, marketing, support)?** Default: one owner per surface and a single launch coordinator; no duration is given until this is known.

Answer first: Q1 and Q2. Q1 sets the deadline and how long the old name may live; Q2 decides the package names and the domain, which everything in Stage 2 depends on.

## Plan

**Step 0. Secure and inventory (before anything public).**
- Register the domain, npm scope, PyPI name, app store names and social handles. Renew `acmenotes.com` for 10 years and keep it permanently: links, SDKs and e-mails out in the world depend on it.
- Inventory every place the name appears, split into *visible* (UI strings, store listings, e-mail templates and sender names, help center, marketing site, API docs, SDK READMEs, invoices and receipts, legal pages, push notification text, OG images, app icons) and *identifier* (domains and subdomains, API base URL, cookie domains, OAuth/Apple/Google client registrations and redirect URIs, universal/app links, webhooks we send with a `User-Agent` or header carrying the name, SDK package names and import names, Stripe statement descriptor, e-mail sending domain). A repository-wide search for `acme`, `Acme Notes`, `acmenotes` and `ACME_` covers the code; the external list is built by each surface owner.

**Step 1. Make the brand a value, ship it dark.** Move product name, support e-mail, and marketing URLs into one config per client, deployed with the old value. This ships in a normal release to web, iOS and Android with no visible change, so launch day needs no app store review for strings already behind remote config. Check: switch the value in staging and look for any screen still saying "Acme Notes".

**Step 2. Prepare the new domain alongside the old.** Point `<new-domain>` at the marketing site and docs. Set up e-mail authentication for the new sending domain (SPF, DKIM, DMARC) and warm it with low volume for two to three weeks before launch, because a cold domain sending to 40k users lands in spam. Add `apple-app-site-association` and `assetlinks.json` on the new domain so links open the apps. Leave the web app and API on `acmenotes.com` hostnames in this stage.

**Step 3. Launch (Stage 1, visible rename).** Go/no-go, all must be true:
- New app versions with icon, display name (`CFBundleDisplayName`, Android `label`) and store listing approved and held for manual release on both stores.
- New-domain e-mail passing DMARC and inbox placement checked on Gmail and Outlook test accounts.
- Support macros, help center and status page updated and reviewed.
- Customer announcement e-mail approved, sent from the old domain with the new name, so it is recognised.

On the day: release the apps, flip the brand config, switch the marketing site, start sending from the new domain. Marketing redirects from `acmenotes.com` use 302 for the first two weeks, then 301; a 301 is cached by browsers and cannot be called back if something is wrong.
Revert rule: if sign-in success or e-mail delivery drops more than 5% from the prior week's baseline in the first 48 hours, flip the config and redirects back and investigate.

**Step 4. API and SDKs (Stage 2, behind a decision gate).** Serve the API on `api.<new-domain>` as well as the old host, same backend, with TLS and the same rate limits. Publish the new SDK packages with the new default base URL. Release one final version of the old packages that depends on or re-exports the new one and prints a deprecation warning; never unpublish the old names (npm restricts unpublishing, and a freed name can be taken by someone else and used to ship malicious code to our users). Old API host: kept indefinitely; measure its traffic monthly and do not plan a shutdown until it is negligible and every paying integration has been contacted.

**Step 5. Web app domain (Stage 2, optional).** Moving the app from `app.acmenotes.com` signs everyone out (cookies are per domain), breaks passkeys and requires new redirect URIs at Google, Apple and every SSO customer. Do it only if Q1 requires it, with the old hostname redirecting, sign-in providers updated first, and SSO customers given a dated notice.

**Left unchanged on purpose:** bundle IDs, Android application ID, repository names, code symbols, database names and internal hostnames. Renaming them costs risk and buys nothing a customer sees. Say if you want any of them renamed too.

## Rollback limits

Stage 1 is reversible by config until the announcement e-mail goes out; after that, the name is public. 301 redirects and published packages cannot be fully withdrawn, which is why both come late and the old ones are never removed.
