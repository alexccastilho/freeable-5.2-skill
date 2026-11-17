# Renaming Acme Notes to Inkwell

I would not do this as one find-and-replace. Changing the name people see is safe; changing the identifiers that customers' code, devices and logins depend on would break things for your 40k paying users. So my plan is to change the first group everywhere now and move the second group over with both names working for a transition period.

I have no access to your repositories here, so this is the plan I would follow, not a report of changes made.

## 1. What gets renamed outright

These are text that people read. I would change every occurrence in one coordinated release:

- UI strings in the web, iOS and Android clients, including localized strings, onboarding, empty states and error messages.
- App display name, launcher icon label, splash screen, logos and favicons.
- Transactional and marketing e-mail templates, push notification text, invoices and receipts.
- Marketing site, help centre, API documentation, SDK READMEs, changelogs.
- Page titles, Open Graph and SEO metadata, app store listing names, descriptions and screenshots.
- Legal text (terms, privacy policy), subject to the legal entity question below.

## 2. What must keep working under the old name

For each of these I would add the new name alongside the old one, and only retire the old one later, if ever:

| Item | What I would do | Why not a straight rename |
|---|---|---|
| Domain `acmenotes.com` | Serve the app on the new domain, 301-redirect web pages from the old one, keep the old domain registered indefinitely | Bookmarks, links in old e-mails, search ranking |
| API hostname | Serve the API on both hostnames with no redirect | Many HTTP clients drop the auth header or the POST body on redirect |
| npm and PyPI packages | Publish new packages; keep the old ones as thin wrappers that depend on the new ones and print a deprecation notice | Existing installs and lockfiles pin the old names |
| SDK symbols (`AcmeNotesClient` and similar) | Add new names, keep the old ones as deprecated aliases for at least one major version | Renaming breaks customers' builds |
| HTTP headers, env vars, API key prefixes, webhook signature headers | Accept and send both; keep issued keys valid | Customers' integrations parse these |
| iOS bundle ID and Android application ID | Do not change | A new ID is a new app: users lose the install, their purchases and push tokens |
| Deep links and custom URL schemes | Add the new scheme, keep the old one registered | Old links in e-mails and other apps |
| OAuth redirect URIs, SSO/SAML entity IDs, sign-in-with-Apple/Google config | Register the new ones, keep the old ones | Changing them locks enterprise users out |
| Cookies, session and local-storage keys | Leave, or migrate on read | A rename logs everyone out and drops offline drafts |
| Sending e-mail domain | Set up SPF, DKIM and DMARC on the new domain and warm it up before switching | A cold domain lands in spam |
| Payment descriptor on card statements | Change with advance notice to customers | An unfamiliar name on a statement causes chargebacks |

## 3. What I would leave alone

Internal names nobody outside the team sees: database and table names, AWS resource names, queue names, repository names, internal package and module names, metric and log names. Renaming them carries real risk and no customer benefit. They can be cleaned up opportunistically later.

## 4. Order of work

1. **Inventory.** Search every repository for `Acme Notes`, `AcmeNotes`, `acmenotes`, `acme-notes`, `acme_notes` and `ACME_NOTES`, and sort each hit into the three groups above. This list is the first deliverable and decides the size of everything else.
2. **Prepare the dual-name plumbing** (group 2), behind the old brand: new domain and certificates, API on both hosts, new packages published, e-mail domain warming.
3. **Put the display name behind a single config value or flag** in each client, so the visible switch is one flip and can be reverted.
4. **Submit mobile builds early.** App review and store listing changes take days and users update slowly, so the mobile apps need to read the name from the flag, not from the build.
5. **Tell customers before the switch**: e-mail and in-app notice covering the new name, the new domain, the statement descriptor, and what API users must do (nothing immediately).
6. **Launch day**: flip the flag, turn on web redirects, publish store listings and docs.
7. **Afterwards**: watch login failure rates, API errors by hostname, e-mail bounce and spam rates, and support volume. Publish a deprecation timeline for the old package names and API host only once usage has fallen.

## 5. What I would check before calling it done

- A fresh search for the old name returns only the intentional leftovers from groups 2 and 3.
- An existing customer integration built on the old SDK version and old API host still works unchanged.
- An existing mobile install updates in place and stays logged in with its data.
- SSO login works for at least one enterprise tenant.

## Questions I would ask

1. **Is there a fixed launch date, and is it tied to an announcement?**
   Default: no fixed date; allow about 6 to 8 weeks, driven by app review and e-mail domain warm-up.
2. **Have the Inkwell domain, trademark, npm and PyPI package names and store names been secured?**
   Default: not yet confirmed, so this is the first check; package names in particular may already be taken.
3. **Is the company's legal entity changing too, or only the product name?**
   Default: only the product name, so contracts, invoices' legal lines and the data processing agreement keep the existing entity.
4. **How long must the old API host, package names and SDK symbols keep working?**
   Default: at least 12 months for packages and symbols, and indefinitely for the API host and the old domain.
5. **Do you want internal names (repositories, infrastructure, database) renamed as well?**
   Default: no.
6. **Which repositories should I work in, and who owns the non-code items (stores, DNS, payment provider, e-mail provider)?**
   Default: I do the inventory and code changes across all product repositories; the non-code items go on a checklist for their owners.
