# Plan: add English and Spanish to the store

The translation of interface text is the small part of this. The three things that decide whether it goes well are: keeping your Portuguese search rankings intact, getting the product catalogue translated and maintained through the admin, and deciding whether you are adding languages or opening new markets. I have planned for languages only (same prices in BRL, same shipping), because that is what you asked for; question 1 below checks that.

I have not seen the codebase, so the first task is a short audit, and the details below may shift with what it finds.

## Decisions I would make up front

| Decision | Recommendation | Why |
|---|---|---|
| URL structure | Portuguese stays at its current URLs with no prefix. English goes under `/en/...` and Spanish under `/es/...`. | Organic search is your main traffic source. Leaving every existing URL untouched means no redirects and no ranking risk for Portuguese. |
| Language detection | Never redirect automatically based on browser language or location. Show a dismissible "View this page in English?" banner and a language switcher, and remember the choice in a cookie. | Automatic redirects confuse search crawlers and annoy users who share links. |
| Library | `next-intl`, with a `[locale]` route segment and middleware that serves Portuguese without a prefix. | It is the best-supported option for the App Router and works in server components. |
| Catalogue translations | Separate translation tables in Postgres, for example `product_translations (product_id, locale, name, description, slug, seo_title, seo_description)`, and the same for categories. | Keeps the existing tables stable, makes "which products lack a translation" a simple query, and lets you add a fourth language without a schema change. |
| Untranslated products | Do not publish a product page in a language until its translation exists. Listings in that language omit it. | Pages that show Portuguese text under an `/en/` URL count as duplicate or low-quality content and can hurt rankings. |
| Slugs | Translated per language, stored in the translation table. | Search results in English and Spanish show readable URLs. |
| Currency | Prices stay in BRL in every language, formatted for the locale and clearly labelled as BRL. | Changing currency means pricing, tax and Stripe changes; that is a market decision, not a language one. |

## The work, in order

**1. Audit (2 to 3 days)**
- Count hard-coded Portuguese strings in components, validation messages, metadata and e-mails.
- List every translatable catalogue field, including attributes, variants, category names and image alt text.
- List every route and the current sitemap, canonical tags and structured data.
- Record the current search baseline from Search Console (impressions, clicks, indexed pages) so a later drop is visible.

**2. Routing and interface text**
- Add the locale segment and middleware, with Portuguese behaving exactly as today. Verify that no existing URL changes or redirects before going further.
- Extract interface strings to message files, Portuguese first, with no visible change.
- Format dates, numbers and prices through the locale.
- Add English and Spanish message files and the language switcher.

**3. Catalogue**
- Add the translation tables and a migration.
- Update the admin: translation fields per language on product and category forms, a "missing translations" view, and a publish toggle per language.
- Update catalogue queries to read by locale.
- Update site search to search within the current language.

**4. Translating the content**
- Machine-translate the catalogue as a first draft, then have a person review it, starting with the best-selling products and the categories.
- Translate fixed pages: shipping, returns, privacy, terms, FAQ. Legal text needs a proper review, not just translation.

**5. Search engines**
- `hreflang` tags on every page listing its Portuguese, English and Spanish versions, plus `x-default` pointing to Portuguese. Only list versions that exist.
- A self-referencing canonical tag per language version.
- Sitemap entries for each language.
- Translated titles, descriptions, Open Graph tags and structured data. Product structured data keeps `priceCurrency: BRL`.
- `lang` attribute on the `<html>` element per locale.

**6. Checkout and e-mails**
- Pass the customer's language to Stripe Checkout (`locale` parameter) and send translated product names in the line items.
- Store the language on the customer and on each order.
- Translate the transactional e-mail templates, and send each e-mail in the order's stored language, including ones triggered later from the admin or a webhook, where there is no browser to ask.

**7. Launch**
- Release English and Spanish with `noindex` first, test the full journey in each language (browse, search, checkout, e-mails), then remove `noindex` and submit the sitemaps.
- Watch Search Console for four weeks: Portuguese traffic should not move, and the new pages should start to be indexed.

Steps 2 and 3 can run in parallel if two people are available. Step 4 is usually the longest and depends on catalogue size, so start it as soon as the translation tables exist.

## Risks worth knowing

- **Portuguese rankings.** The safeguard is that Portuguese URLs do not change. Check this with an automated comparison of the old and new sitemaps before release.
- **Translations going stale.** When someone edits a Portuguese description, the English and Spanish versions fall behind. The admin should flag a translation as outdated when its source changes.
- **Support.** Customers who buy in English or Spanish will write in English or Spanish. Decide who answers.

## Questions I would ask

1. **Are you adding languages or opening markets?** Will you ship abroad and charge in other currencies, or serve English and Spanish speakers under today's prices and shipping?
   Assumed default: languages only, BRL only, current shipping areas. Selling abroad would add currency, tax, shipping and Stripe work that is larger than everything above.
2. **Which Spanish and which English?**
   Assumed default: Latin American Spanish (`es`, written neutrally) and US English (`en`), one version each.
3. **How large is the catalogue, and who will translate it?**
   Assumed default: a few thousand products at most, machine translation with human review of the top sellers before launch and the remainder afterwards.
4. **Are there other customer-facing texts outside the site?** Invoices, SMS, push notifications, marketing e-mails.
   Assumed default: only the transactional e-mails are in scope.
5. **Must both languages launch together?**
   Assumed default: no. English first, Spanish two to three weeks later, reusing everything built.
