The text replacement is the easy part. The work is in the names other systems depend on: the domain, the API hostname, the npm and PyPI package names, the iOS bundle ID and Android package name, and everything bound to `acmenotes.com`. That includes login cookies, passkeys, OAuth redirect URIs, email sending reputation and universal/app links. Some of these can't be renamed at all: changing a bundle ID or package name ships a new app that existing users don't receive. Others break silently if renamed: a redirect on an API host breaks POST requests from old SDKs. So by default I rename everything a person sees, and I keep every machine-facing identifier working under its old name, permanently, next to the new one. Internal names (repositories, code namespaces, database names) stay as they are. That gets "Inkwell everywhere a user or customer looks", and every step can be undone up to the moment the new name is announced. If the reason is a trademark dispute that requires removing "Acme Notes" completely, the plan changes (see Q1). I haven't seen your codebases, infrastructure or contracts, so the plan rests on the defaults below.

## Questions I would ask

1. **What is driving the rename: a voluntary rebrand, or a legal or trademark demand?** Default: voluntary, with no hard deadline. Old identifiers stay alive indefinitely, and the launch date is chosen around app review and email warm-up. If it is a legal demand, the deadline sets the schedule, old package names get a final release and are then deprecated on a fixed date, and the old domain only redirects. Counsel decides whether even redirects are acceptable.
2. **Have the new names been secured: the domain, the trademark in your markets, the npm and PyPI names, app store names, and social handles?** Default: the domain is bought (I write `inkwell.example` below). Phase 0 checks the rest before anything is built. If `inkwell` is taken on npm or PyPI, the SDKs use a scoped name such as `@inkwell/sdk`, and this has to be settled before launch, because SDK names are permanent once published.
3. **Do users log in with passkeys, or through "Sign in with Google/Apple"?** Default: password plus Google sign-in. Passkeys are bound to the domain they were created on, so moving the web app to the new domain would stop them working. If passkeys are in use, login stays on `acmenotes.com` (or a related-origin setup is verified) until users have re-enrolled.
4. **Which integrations hold your old name or domain: OAuth apps registered by third parties, webhooks, Zapier and similar, enterprise SSO (SAML) configurations?** Default: some exist, found in Phase 0. They keep working because the old hosts stay up.
5. **Who does the work, and is there a target launch date?** Default: not assumed. The largest phase is the client and email work in Phase 2. Its length depends on app review lead times and how many places the name is hard-coded.

Answer first: Q1 and Q2. Q1 sets the deadline and what must disappear. Q2 can block the names themselves.

## Plan

**Phase 0: inventory and secure (no user-visible change).** Search every repository, the mobile projects, email templates, help centre, legal pages, store listings, SDK READMEs and docs, status page, billing (Stripe statement descriptor, invoices), analytics and support tooling for `acme`, `Acme Notes`, `acmenotes` and `ACME_`. Classify each hit as *visible* (rename), *machine-facing* (keep, add an alias), or *internal* (leave). Reserve the package names, store names and handles. Check: every hit has a class. Nothing ships in this phase.

**Phase 1: new domain alongside the old one (invisible, reversible).**
- Serve the web app and API on both domains with TLS. `api.inkwell.example` and `api.acmenotes.com` hit the same backend.
- Register OAuth redirect URIs, CORS origins, CSP and cookie domains for both. Add universal links and Android App Links (`apple-app-site-association`, `assetlinks.json`) on the new domain.
- Set up email on the new domain (SPF, DKIM, DMARC) and warm it up by moving low-volume mail first, such as password resets. A cold domain sending to 40k users at once lands in spam.
- Check: a full login, sync and API run on each domain in staging, then production.

**Phase 2: visible rename behind a brand setting.** Put the product name, logo, support address and domain behind one configuration value, so the web app and emails flip at launch without a deploy and can flip back.
- Web: strings, `<title>`, meta and Open Graph tags, favicon, PWA manifest, legal pages.
- iOS and Android: display name, icon, store listing, screenshots, in-app strings. Do not change the bundle ID or package name, since that would publish a new app. Submit early, because review can delay the launch. The new strings can sit behind a remote-config flag, or the build can be timed to launch day.
- Emails and push notification templates. Billing descriptor, because "ACME NOTES" on a card statement after a rebrand causes chargebacks.
- Check: a screenshot pass of key screens on each client with the setting on. A search of built artefacts finds no visible "Acme Notes".

**Phase 3: API and SDKs.**
- Publish new SDK packages (`inkwell` on PyPI, `inkwell` or `@inkwell/sdk` on npm) with the new default base URL. Publish a final release of the old packages that depends on and re-exports the new one, and logs a one-time deprecation notice. Then deprecate the old packages on npm, and on PyPI via README and classifiers. Never unpublish them.
- The old API host stays working with no redirect. A 301 or 302 on POST or PUT is followed inconsistently by HTTP clients, and some drop the body.
- Check: the old SDK's test suite passes against both hosts, and the new SDK's against both.

**Phase 4: launch.**
- Two weeks before, email paying users and API customers: new name, what changes for them (nothing they must do, except an optional SDK swap), and that old URLs keep working.
- On the day: flip the brand setting, release the apps, publish the SDKs, update the store listings, and redirect web pages on `acmenotes.com` to the same paths on the new domain.
- Use **302 for the first two weeks, then 301**. Browsers cache a 301 more or less permanently, so it can't be rolled back.
- Sessions are per domain, so a redirected user would be logged out. Either do a signed one-time token handoff from old domain to new, or accept one re-login and say so in the announcement. Default: the handoff, if login is your own code.

Abort or revert rules for the first 72 hours, measured against the week before:
- Login success rate drops more than 2 points, or the API error rate on either host rises above its normal level: flip the brand setting back and remove the redirect (it is still a 302).
- Spam-folder or bounce rate on the new mail domain above 2%: send from the old domain again while warm-up continues.
- Support tickets about login or sync above twice normal: pause the redirect and investigate before continuing.

**Phase 5: afterwards.**
- Keep `acmenotes.com` registered and auto-renewing for good. A lapsed domain gets bought and used for phishing your users, and still receives old SDK traffic, password-reset links in old emails, and saved passwords.
- Monitor traffic to the old API host. Its share is the measure of SDK migration. Remove nothing.
- Search-engine site-move notice, sitemap on the new domain.

What the current arrangement gives for free, and what replaces it: one origin for cookies, passkeys and saved passwords, replaced by the session handoff and an extended passkey window; an established mail reputation, replaced by the warm-up; one set of package names, replaced by shim packages kept alive.

**Branch (renaming internals as well):** after launch, as a separate project. Rename repositories, code namespaces, environment variables, cloud resource names and the database name, one service at a time, each behind a normal deploy. It is the largest cost for the smallest user-visible gain, and the only part that can't be done with aliases. The bundle ID and package name would still stay.
