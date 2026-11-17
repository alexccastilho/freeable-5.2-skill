"Everywhere" can't be taken literally here: some places where "Acme Notes" appears can't be renamed, and others will break customers if they are. This is the plan I would follow, and it starts with one check that could stop the whole thing.

## Check first

**Is "Inkwell" cleared for use?** It is a common word, so there is a real chance it is already taken somewhere you need it. Before any engineering work I would want confirmation of trademark clearance in your markets, the domain you will use, the App Store and Google Play listing names, the npm and PyPI package names, and the social handles. Any of those being taken changes the plan.

## What changes, in three groups

### 1. What users see: change all of it

- **Product UI:** web app, iOS and Android strings, including every localisation, plus logos, icons, splash screens and the favicon.
- **Store listings:** app display name, screenshots, descriptions and keywords.
- **Messages:** transactional e-mail templates and sender name, push notification text, in-app messages.
- **Sites:** marketing site, help centre, API docs, status page, changelog.
- **Legal and billing text:** terms, privacy policy, invoices and receipts.
- **Card statement descriptor:** an unfamiliar name on a statement causes chargebacks, so this one needs advance notice to customers.
- **Third-party consent screens:** OAuth app names for "Sign in with Google/Apple" and any integrations directory listings.

This is mostly a search-and-replace with review, and it should ship together on one date.

### 2. Identifiers others depend on: add the new name, keep the old one working

| Thing | What I would do |
|---|---|
| `acmenotes.com` web | Serve the app on the new domain and 301 the old one. Keep the old domain registered indefinitely. |
| API host | Add the new host and keep the old one serving, not redirecting. Many HTTP clients drop the body or the auth header on a redirect. |
| npm and PyPI packages | Neither registry supports renaming. Publish under the new name, release a final version of the old package that wraps the new one and prints a deprecation notice, and mark it deprecated. |
| SDK surface | Class names, environment variables such as an `ACME_*` API key, and custom HTTP headers get new names, with the old ones kept as aliases for at least one major version. |
| Webhooks | Keep the existing signature header names and user agent, or send both, until customers have migrated. |
| Sending e-mail domain | Set up SPF, DKIM and DMARC on the new domain and ramp volume gradually. A cold switch for 40k customers will land in spam. |
| Login sessions and cookies | Cookies are tied to the old domain, so a domain move logs everyone out, and password managers won't offer saved logins. Plan a handoff or warn users. |
| SSO and OAuth redirect URIs | Customers with SAML or OAuth set up have the old URLs registered on their side. Both must keep working. |
| Mobile deep links | Universal links and app links are verified against the domain. Add the new domain and keep the old association files in place. |

### 3. Identifiers that should stay as they are

- **iOS bundle ID and Android application ID.** These can't be changed on a published app. A new ID is a new app, which loses the installed base, ratings and subscriptions.
- **Internal names.** Repository names, database and table names, cloud resource names, metric and log names. Renaming these carries real outage risk and no customer benefit. I would leave them, or handle them later as separate low-priority work.
- **Historical records.** Old invoices, changelog entries and release notes should keep the name that was true at the time.

## Order of work

1. **Inventory.** Search every repository, the CMS, e-mail templates, store listings and third-party dashboards for `Acme Notes`, `AcmeNotes`, `acmenotes`, `acme-notes`, `acme_notes` and `ACME`. Sort each hit into the three groups above. This list is the real scope; everything else here is an estimate until it exists.
2. **Compatibility groundwork, shipped quietly ahead of time.** New domain and API host live, e-mail domain warming, new SDK packages published, mobile builds that accept both domains.
3. **Customer notice.** Tell the 40k paying users and API customers before launch: what changes, what doesn't, the new statement descriptor, and that nothing they have built will break.
4. **Launch day.** Flip the visible layer in one release: web, mobile builds already approved by the stores and held for manual release, e-mail templates, docs, store listings.
5. **Afterwards.** Watch redirects, e-mail deliverability, login failures and support tickets. Set deprecation dates for the old SDK names, and no end date for the old domain.

Mobile store review is the scheduling constraint: submit both apps a week or more ahead and release them manually on the day.

## Questions I would ask

1. **Is the name legally cleared and is a domain secured?** Default assumed: yes, and the new domain is in hand.
2. **Is this a hard cutover on a date or a gradual transition?** Default assumed: one public launch date, with compatibility work done beforehand.
3. **Should the public API and SDKs change at all?** Default assumed: yes, with the old names working for at least 12 months.
4. **Does the legal entity change too, or only the product name?** Default assumed: product only, so contracts and the company name on invoices stay.
5. **Which repositories and systems can I get at?** Default assumed: I do the code and string changes; store listings, DNS, payment provider and e-mail provider settings are done by whoever owns those accounts, from a checklist I produce.
6. **Do customers use SSO or webhooks in volume?** Default assumed: yes, so both old and new URLs are supported indefinitely.
