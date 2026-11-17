Changing the words is not the hard part. Find-and-replace covers the UI, e-mails, store listings and docs in a few days. The work and the risk sit in the places where "acmenotes" is an address that other people and systems depend on: the domain (logins, saved passwords, passkeys, shared-note links, e-mail reputation, OAuth redirects, mobile deep links), the API host that customers' code calls, the SDK package names on npm and PyPI, and the app identifiers in the stores. My recommendation is to rename everything users see, run the new domain alongside the old one before making it primary, keep `acmenotes.com` and the old package names working permanently, and leave internal identifiers (repositories, database names, bundle IDs, environment variables) as they are.

I have not seen your code, infrastructure or contracts. The plan rests on the defaults below.

## Questions I would ask

1. **Is "Inkwell" trademark-cleared in your markets, and do you already own the domain, the npm scope or name, the PyPI name and the social handles?** Default: clearance is done and the domain is bought. Phase 0 confirms both before anything public happens. If either is missing, everything except the inventory waits. A rename announced and then withdrawn costs more than a delay.
2. **Does "everywhere" include the domain and internal code names?** Default: the domain moves to the new one, with the old one redirecting permanently. Internal identifiers stay. If you want the brand only, keeping `acmenotes.com` as the address, phases 3 and 5 drop out and the project shrinks to roughly the size of phase 2.
3. **Do business customers depend on the old name or domain: firewall allowlists, SAML/SSO configurations with `acmenotes.com` callback URLs, contracts or invoices that name the product?** Default: some do. Old URLs keep working indefinitely, and those customers get direct notice before anything they configured changes.
4. **Is there a fixed announcement date?** Default: none. The date is set once the new domain has run alongside the old one without problems (phase 3). If a date is already public, phases 2 and 4 are planned backwards from it, and the domain switch (phase 5) can follow after the announcement.
5. **Does the legal entity change name too?** Default: no. Only the product and the card-statement descriptor change. If yes, there is extra legal and billing work that this plan does not cover: contracts, the data-processing agreement, tax registrations and app store developer accounts.

Answer first: 1 and 2. Question 1 decides whether the project can start. Question 2 decides whether it includes the domain move, which is most of the risk.

## Plan

### Phase 0: Secure the name (before anything public)

- Confirm trademark clearance. Register the domain and the obvious variants. Claim the npm and PyPI names, the App Store and Play Store name, and the social handles.
- Set `acmenotes.com` to auto-renew with a long registration. Losing it later would hand your old links, and inbound e-mail to the old domain, to whoever buys it.
- Check: every name is held by your accounts. Nothing is announced, not even internally to customers, until this is done.

### Phase 1: Inventory and classify (about a day of searching)

Search every repository, config store, CMS, help centre, e-mail provider template, store listing and infrastructure definition for all spellings: `Acme Notes`, `AcmeNotes`, `acme-notes`, `acme_notes`, `acmenotes`, `ACME_NOTES`, plus the logo and icon files. Sort each hit into one of three groups:

| Group | Examples | Treatment |
|---|---|---|
| Seen by users | UI strings, e-mail templates and sender name, push notification text, app display names, store listings, marketing site, docs, help centre, ToS and privacy policy, card-statement descriptor, invoice PDFs, error pages, OAuth consent screen names | Rename (phase 2) |
| External contract | `acmenotes.com` and its subdomains, `api.acmenotes.com`, SDK package names and import names, iOS bundle ID, Android `applicationId`, universal and app links, OAuth redirect URIs, SAML callback URLs, webhook signing headers, e-mail sending domain, API key prefixes | Add the new form alongside, never remove (phases 3 to 5) |
| Internal | Repository names, service names, database and schema names, environment variables, log tags, AWS resource names | Leave alone |

Check: the table exists, with an owner per row. It also catches what no one remembered, such as a `User-Agent` string or an export file name.

### Phase 2: Rename what users see

- Web: strings, titles, meta tags, favicon, logo, e-mail templates and sender display name (still sent from the old domain at this stage).
- iOS and Android: display name, icons, in-app strings, store listing name, screenshots and description. **The bundle ID and `applicationId` do not change.** Changing either creates a new app, without the installs, reviews and update path of the existing one. Submit builds early enough to clear store review, and use manual or phased release so they go live on launch day rather than when review finishes.
- Docs, help centre, ToS and privacy policy (a legal review of the new wording), and the card-statement descriptor with your payment provider.
- Put the new name behind a single switch where the platform allows it (a config value or feature flag for web strings and e-mails), so launch day is a flip, not a deploy.
- Check: a fresh search finds the old name only in the "external contract" and "internal" groups, plus deliberate mentions such as "formerly Acme Notes".

### Phase 3: Run the new domain alongside the old one

Both domains serve the full product, and nothing redirects yet. This is where the problems show up while they are still cheap to fix.

- DNS, TLS certificates, CDN and load balancer for the new domain and its subdomains, including `api.`.
- OAuth providers (Google, Apple, Microsoft and others): add the new redirect URIs alongside the old ones. Update the app name on consent screens. Some providers re-review this.
- Mobile deep links: publish `apple-app-site-association` and `assetlinks.json` on the new domain, and add the new domain to the apps' associated domains in the phase 2 builds.
- E-mail: set up SPF, DKIM and DMARC for the new sending domain, then warm it up by gradually moving a growing share of traffic onto it. A cold domain sending to 40k users at once lands in spam. Keep the old domain receiving mail, since replies will go there for years.
- Cookies are per domain, so a user moving from the old domain to the new one arrives logged out. Default: accept one re-login, announced in advance. The alternative is a one-time signed handoff token on the redirect. That is more work, and it needs a security review because it is a login path.
- If you use passkeys: WebAuthn credentials are bound to the domain (the relying party ID), and passkeys registered on `acmenotes.com` will not work on the new domain unless you keep the old RP ID or use the related-origins mechanism. I am recalling the name of that mechanism (Related Origin Requests, served from `/.well-known/webauthn`) and its browser support from memory. Check current support before relying on it, and if it falls short, keep `acmenotes.com` as the RP ID.
- Saved passwords in password managers are also keyed to the domain. The re-login notice should say this.
- Check: the full product, sign-in with every method, the mobile deep links, the API and SSO all work on the new domain, tested by staff for at least a week.

### Phase 4: Announce and launch the name

- E-mail all users before launch day. It must mention the new card-statement descriptor, because an unrecognised charge is a common cause of chargebacks. Send business customers with SSO or allowlists (question 3) their own notice earlier, with what they need to change and by when.
- Launch day: flip the name switch, release the mobile builds, update the marketing site and store listings, publish the announcement. In-app banner: "Acme Notes is now Inkwell."
- The order is deliberate: users hear about the change before they see it, and nobody hears about it before phase 0 has secured the name.

### Phase 5: Make the new domain primary

- Switch `acmenotes.com` to 301 redirects that keep the path and query string, so `acmenotes.com/s/abc123` lands on the same shared note. Exclude `api.acmenotes.com`: it keeps serving requests directly, permanently. A redirect breaks API clients that do not follow redirects on POST requests.
- Search engines: tell them about the move using your search console's change-of-address tool.
- Switch e-mail sending to the new domain once warm-up is complete.
- **Go/no-go before switching (all must be true):**
  - The phase 3 checks passed, with no open issue on sign-in or deep links.
  - The new sending domain has been delivering at least a quarter of e-mail volume with bounce and spam-complaint rates no worse than the old domain's.
  - Business customers from question 3 have had their notice period.
  - The revert has been tested: removing the redirect takes one config change, without a deploy.
- **Revert rule:** watch sign-in success rate, API error rate and support tickets for 48 hours. If sign-in success drops more than 2 percentage points below the previous week's rate at the same hour, or the 5xx rate on the new domain exceeds the old domain's rate for the same hours of the previous week, remove the redirect and investigate. Both domains still serve the full product, so the revert loses nothing.

### Phase 6: API and SDKs

- API: `api.acmenotes.com` and the new API host serve the same API with the same keys. The docs show the new host. The old host is never switched off without a separate decision, made later and with usage data showing it is idle.
- npm and PyPI: package names cannot be renamed. Publish the same code under the new names (for example `inkwell` or `@inkwell/sdk`, whichever you claimed in phase 0), with the new host as the default base URL. Then publish one last release of the old packages that depends on the new package and re-exports it. Mark the old packages deprecated, with a message pointing to the new ones: `npm deprecate` for npm, and a README notice plus classifier for PyPI. Never unpublish: that breaks every existing install and build.
- Keep the Python import name and the JS export names compatible in the old packages, so existing code works without edits.
- Check: a project pinned to the old package still installs and works. A fresh install of the new package works against both hosts.

## What changes for users, and what covers it

| Free today | After the domain move | Cover |
|---|---|---|
| Users stay logged in | Logged out once when crossing domains | Advance notice, or the signed handoff token |
| Saved passwords autofill | The password manager may not offer them on the new domain | Mention in the notice; the old domain redirects, so stored URLs still lead there |
| Passkeys work | Fail on a new RP ID | Keep the old RP ID, or use related origins after checking support |
| Shared links, links in old e-mails and bookmarks work | Would break without redirects | Permanent path-preserving redirects; the old domain is never let go |
| E-mail sender reputation | A new domain starts cold | Warm-up in phase 3 before switching |
| Search ranking | Temporary dip | 301s plus change of address |

## Found, not touched

- Internal identifiers keep the old name. That is deliberate, and costs nothing except that new engineers will see "acmenotes" in code. They can be renamed one service at a time later, if anyone cares enough.
- Old blog posts, press coverage and third-party integrations (Zapier-style listings, browser extension stores) will keep the old name until each is updated by hand. They belong on the inventory, but they do not block the launch.

## Need from you

- The answers to questions 1 and 2.
- Read access to the repositories (web, iOS, Android, SDKs, infrastructure) so the phase 1 inventory can run.
- The list of business customers with SSO, allowlists or contracts that name the product.
- Which sign-in methods you support, and whether passkeys are among them.
