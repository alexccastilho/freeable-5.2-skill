Translating the interface strings is the small part. The work is in three places. The first is the product catalogue: a translations schema, admin screens, and someone who actually writes and reviews the English and Spanish copy for every product. The second is not putting your organic traffic at risk: the Portuguese URLs must stay exactly as they are, and the new languages need proper hreflang, sitemaps and canonicals. The third is the checkout and e-mails, which need to know the customer's language. Language is not market, though. I plan for English and Spanish speakers buying with the same prices, currency and shipping as today. Selling abroad would be a different, larger project.

**Not seen:** your repository, schema, admin or e-mail setup. Library names and Next.js details below are from memory, and each is flagged where it appears.

## Questions I would ask

Q1. Who are the English and Spanish pages for: foreigners buying for delivery in Brazil (tourists, expats, gifts), or customers in other countries? - Default: delivery to the same places as today, prices in BRL, Stripe in BRL. If other countries, the project also needs international shipping, local currencies or conversion, taxes and duties, payment methods per country, and translated legal terms. That is a separate plan, and this one becomes its first phase.

Q2. How many products and categories are there, and who will translate them? - Default: machine-translated drafts, with a human review of the products that bring the most revenue or traffic first. A product appears in English or Spanish only after its translation is marked reviewed. Until then it is left out of that language's listings and sitemap, and not shown half-translated. If you have professional translators or a budget for them, the same workflow applies with them as reviewers.

Q3. Do you want translated URLs (`/es/productos/camiseta-azul`) or just a language prefix with the Portuguese slug (`/es/produtos/camiseta-azul`)? - Default: translated slugs per language, stored per product, because organic search is your main channel and slugs in the reader's language help a little. A prefix-only scheme is cheaper: no slug columns and no slug redirects when translations change.

Q4. Besides products, what content earns organic traffic (blog, landing pages, category descriptions)? - Default: category texts are translated. Blog and landing pages are not in version 1 unless Search Console shows they bring in significant traffic.

Answer first: Q1, then Q2. Q1 decides whether this is a language project or a market expansion. Q2 sets the largest cost and the timeline.

## Plan

**Phase 0: Inventory and a baseline (before any code).**
- Crawl the live site and save every indexable Portuguese URL with its status, canonical and title. Export 28 days of Search Console data (clicks per page). Count the interface strings, products, categories and e-mail templates.
- Check: a URL list and a traffic baseline you can compare against after each release.

**Phase 1: Internationalization plumbing, Portuguese only (no visible change).**
- Add an i18n library (next-intl is the usual choice for App Router; check its current docs for the routing and middleware setup, since this changed between versions). Also check whether your Next.js version calls the request interceptor `middleware.ts` or `proxy.ts`, because recent versions renamed it.
- Routing: Portuguese stays the default with **no prefix**, so every current URL is unchanged. English and Spanish are served under `/en` and `/es`. No automatic redirect based on `Accept-Language` or IP: crawlers and shared links must always get the URL they asked for. Visitors whose browser prefers another language get a dismissible banner instead.
- Move the interface strings into `messages/pt-BR.json`. Format money and dates with `Intl` using the page locale while the currency stays BRL (for example `R$ 129,90` in Portuguese and `R$129.90` in English).
- **Check before deploying:** re-crawl staging and compare against the phase 0 list. Every Portuguese URL returns the same status, canonical and title. If one changes, it does not ship.

**Phase 2: Catalogue data and admin.**
- Add a `product_translations` table (product_id, locale, name, description, slug, seo_title, meta_description, status `draft|reviewed`, updated_at) and the same for categories. Portuguese stays in the existing columns, so nothing that reads them today breaks.
- Admin: a tab per language on the product and category forms, a "machine draft" button, a reviewed toggle, and a list of untranslated or outdated products (the Portuguese text changed after the translation was reviewed).
- Storefront queries: look up the translation for the page locale and only show `reviewed` rows. A product with no reviewed translation returns 404 in that language and is left out of its listings.
- Check: a product with no Spanish translation is missing from `/es` listings and from the Spanish sitemap, and still works in Portuguese.

**Phase 3: Translation work (runs alongside phases 2 and 4).** Translate the interface strings, then categories, then products in order of revenue. Write a short glossary first (sizes, materials, shipping terms) so product names stay consistent.

**Phase 4: Checkout and e-mails.**
- Save the locale on the cart and the order at checkout. Pass it to Stripe Checkout's `locale` parameter (currency stays BRL). Check which payment methods you offer: Pix and boleto need a Brazilian tax ID (CPF), so make sure foreign card holders get a clear card option.
- Transactional e-mails: templates per language, chosen from `order.locale`, including e-mails sent later from Stripe webhooks (payment confirmed, shipped, refunded), not from the visitor's current page.
- Translate the terms, privacy policy, returns and shipping pages, or link clearly to the Portuguese legal text, with your lawyer's agreement on which version applies.
- Check: a full test purchase in each language, in Stripe test mode, receiving every e-mail in the order's language.

**Phase 5: SEO setup, then launch in two stages.**
- Each page gets a self-referencing canonical and reciprocal `hreflang` links (`pt-BR`, `en`, `es`, `x-default` → Portuguese), listing only the languages where that page actually exists. One sitemap per language, or a sitemap with alternates.
- **Stage A (observe):** deploy English and Spanish to production with `noindex` and without hreflang. Review real pages in context and fix layout issues (Spanish text runs longer than Portuguese).
- **Stage B (index):** remove `noindex`, add hreflang, submit the sitemaps, add the language switcher.

## Go / no-go before stage B

All of these must be true:
- The re-crawl of every Portuguese URL matches the phase 0 baseline (status, canonical, title).
- A hreflang validator shows no missing return links or language-code errors on a sample from each template.
- No unreviewed product appears in an English or Spanish sitemap or listing.
- A test purchase in each language has completed, with every e-mail in that language.

**Revert rule after stage B:** watch Portuguese organic clicks in Search Console against the phase 0 baseline, adjusted for the usual weekly variation. If they fall beyond that range and any Portuguese URL now redirects, returns an error or has a changed canonical, remove the hreflang and the routing change until that's fixed. English and Spanish pages taking time to rank is expected, not a reason to revert.

## Found, not touched

- Structured data (`Product`/`Offer` JSON-LD) should be translated with each page, and must keep `priceCurrency: BRL`.
- Customer support in English and Spanish: if no one can answer e-mails in those languages, say so on the contact page.
- Site search: Postgres full-text search set up for Portuguese won't stem English or Spanish well. Index per language later if search is important.

## Need from you

- Answers to Q1 and Q2 (with the product count).
- Repository access and a staging environment with a copy of the catalogue.
- Where the e-mail templates live (code or an e-mail provider), and who on the team will review translations.
