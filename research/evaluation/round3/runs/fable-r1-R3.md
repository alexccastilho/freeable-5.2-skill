# Plan: add English and Spanish to the store

The main risk here is your Portuguese search traffic, so the plan is built around one rule: existing Portuguese URLs do not change. English and Spanish are added under `/en` and `/es`, and each goes live to search engines only when its catalogue is translated.

I have not seen the codebase, so this is a plan from the context you gave; the relative sizes at the end should be checked against the code before committing to dates.

## Decisions I am making up front

| Decision | Choice | Why |
|---|---|---|
| URL structure | Portuguese stays at the root, new languages at `/en/...` and `/es/...` | No redirects on pages that rank today |
| Language detection | No automatic redirect by browser language; a dismissible banner suggests the other language | Auto-redirects confuse crawlers and annoy people who share links |
| Library | `next-intl` with a `[locale]` route segment and middleware | The standard fit for the App Router, works with server components |
| Catalogue translations | Separate translation tables in Postgres (`product_translations` keyed by product and locale), same for categories | Keeps one product, one price, one stock record |
| Missing translations | Fall back to Portuguese on the page, but keep that page out of the sitemap and mark it `noindex` | Avoids indexing half-translated pages |
| Currency | Prices stay in BRL in every language | Translating the site is separate from selling in other currencies (see question 1) |

## Phases

**1. Routing and plumbing, no visible change**

- Add the `[locale]` segment, middleware and `next-intl`, with Portuguese as the only enabled locale.
- Verify that every existing URL still returns the same page, status code and canonical tag. This is the check that protects search traffic, so automate it against a crawl of the current sitemap.

**2. Interface text**

- Extract hard-coded Portuguese strings into message files: navigation, product pages, cart, account, errors, form validation.
- Format dates, numbers and prices through `Intl` with the active locale (`R$ 1.299,00` in Portuguese, `R$1,299.00` in English).
- Translate the message files to English and Spanish, with a human review of checkout and legal text.

**3. Catalogue**

- Add the translation tables and a migration that copies current content in as `pt-BR`.
- Extend the admin so each product and category has name, description, slug and SEO fields per language, with a visible "untranslated" status and a filter for it.
- Translate slugs too (`/en/products/leather-wallet`), since they carry search value.
- Update site search to query the active language.
- Bulk-translate the catalogue by machine as a first draft, then have someone review, starting with the best-selling products.

**4. Checkout and e-mail**

- Pass the locale to Stripe Checkout so the payment page matches the site language.
- Store the customer's language on the order and the account.
- Translate the transactional e-mails (order confirmation, shipping, password reset, refunds) and send each in the stored language, including e-mails triggered later by webhooks or the admin.

**5. Search engine launch**

- `hreflang` links between the three versions of every page, plus `x-default`, in both the HTML and the sitemap.
- Per-locale sitemaps, titles, descriptions, Open Graph tags and structured data.
- Self-referencing canonicals on each language version.
- Launch English first, watch Search Console for two weeks for indexing errors and any dip in Portuguese impressions, then launch Spanish.

## How I would verify it

- Before and after crawl of all Portuguese URLs: identical status codes and canonicals.
- An automated check that no message key is missing in any language.
- End-to-end test per language: browse, add to cart, pay with a Stripe test card, receive the e-mail in the right language.
- Search Console: Portuguese clicks and impressions flat or up through each launch.

## Relative size

Phases 1 and 2 are mostly mechanical and depend on how many strings are hard-coded. Phase 3 is the largest piece because it touches the schema, the admin and every catalogue query. The translation review is the part most likely to set the date, and it depends on catalogue size, not engineering.

## Questions I would ask

1. **Are you only translating, or also selling to customers outside Brazil?** *Default assumed:* translation only. Prices, shipping zones, taxes and payment methods stay as they are. Selling abroad adds multi-currency pricing, international shipping and tax handling, which is a separate project.
2. **Which Spanish and which English?** *Default assumed:* neutral Latin American Spanish (`es`) and US English (`en`), with no regional variants.
3. **How many products, and who reviews translations?** *Default assumed:* a few thousand at most, machine-translated first with staff review of top sellers before launch.
4. **Does the admin itself need to be translated?** *Default assumed:* no, it stays in Portuguese; only the fields for translated content are added.
5. **Are there blog posts, landing pages or legal pages outside the catalogue?** *Default assumed:* legal pages are translated with a legal check; blog content stays Portuguese-only for now.
