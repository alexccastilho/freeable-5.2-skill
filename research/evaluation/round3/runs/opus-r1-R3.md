# Plan: add English and Spanish to the Next.js store

Translating interface strings is the easy part. On a store where organic search is the main traffic source, the decisions that matter are the URL structure and SEO signals, how translated product content is stored and edited in your admin, what currency foreign customers see and pay in, and making sure Stripe and the e-mails follow the customer's language. Get those right first; the string extraction is mechanical.

## Questions I would ask

1. **Who is this for?** Are you selling to and shipping to customers abroad (Spanish-speaking Latin America, the US, Europe), or serving English/Spanish speakers in Brazil?
   *Default: you want to reach and sell to buyers in other countries, but shipping and tax rules stay as they are for now.*
2. **Currency.** Keep charging in BRL for everyone, or show and charge local currencies (USD, EUR, MXN, ARS…)?
   *Default for phase 1: **charge in BRL**, and optionally show an approximate converted price labelled "approx.". Multi-currency pricing is a separate project (pricing rules, rounding, Stripe settlement, refunds).*
3. **Who translates the product catalogue, and how many products are there?** Human translators, machine translation with review, or machine translation only?
   *Default: machine translation as a first draft, reviewed by a person for the top-selling products, with a "needs review" flag in the admin.*
4. **Which variants exactly?** English: generic or en-US? Spanish: es-419 (Latin America) or es-ES?
   *Default: `en` and `es` (neutral/Latin American Spanish), with Portuguese as `pt-BR`.*
5. **Can the current Portuguese URLs change?** They carry the existing search ranking.
   *Default: **no**. Portuguese stays at the current URLs (no prefix), and the new languages go under `/en/...` and `/es/...`.*
6. **Translated slugs** (e.g. `/es/productos/camiseta-azul`) or the same slugs in every language?
   *Default: translated slugs for products and categories. They help search, and since they live in the DB we need old-slug redirects anyway.*

## Key design decisions (under the defaults)

| Area | Decision |
|---|---|
| Routing | App Router `app/[locale]/...` with middleware. `pt-BR` is the default with no prefix; `/en` and `/es` are prefixed. Use `next-intl` (good App Router and Server Component support). |
| Language detection | Use `Accept-Language` only to **suggest** a switch (a banner), never to auto-redirect. Auto-redirects confuse search crawlers and annoy users. Remember the choice in a cookie. |
| SEO | Per-locale `<title>`/description via `generateMetadata`, `hreflang` alternates including `x-default`, self-referencing canonicals per locale, a sitemap with `alternates` for each locale, localized structured data (`Product` with `priceCurrency: BRL`), and the `lang` attribute on `<html>`. |
| UI strings | Message files `messages/{pt-BR,en,es}.json`, organized by namespace. Use ICU message format for plurals. A CI check fails when keys are missing. |
| Formatting | `Intl.NumberFormat` / `Intl.DateTimeFormat` with the active locale. A BRL price renders as `R$ 129,90` in pt-BR, `R$129.90` in en, and so on. |
| Catalogue data | A translation table per entity, e.g. `product_translations(product_id, locale, name, description, slug, meta_title, meta_description, status)`, unique on `(locale, slug)`. Fall back to pt-BR when a translation is missing, and mark those pages `noindex` (or leave them out of the sitemap) so untranslated pages aren't indexed. |
| Admin | Language tabs on the product and category editors, a translation status per locale, and a list of "missing / needs review" items. |
| Checkout | Pass `locale` (`en`, `es`, `pt-BR`) to Stripe Checkout Sessions so the hosted page matches. Save the customer's locale on the order and the customer record. |
| E-mails | Templates per locale. Choose the language from the locale **stored on the order** at send time, not from the current request. This also covers Stripe webhooks and other background sends. |

## Plan in phases

### Phase 0: groundwork (about 1 week)
- Inventory the hard-coded Portuguese: components, `metadata`, `alt` text, validation and error messages, toast messages, 404/500 pages, the cookie banner, legal pages, and e-mails. A quick grep for accented characters and string literals in JSX gets most of them.
- Benchmark current organic traffic and rankings per top page (Search Console), so we can confirm that nothing regresses for pt-BR.
- Agree on the answers to the questions above, especially currency and URL structure.

### Phase 1: i18n framework with no visible change (about 1–2 weeks)
- Add `next-intl` and the `[locale]` segment with middleware. Portuguese stays unprefixed, so **all existing URLs must return the same page**. Write an automated test over a sample of current URLs: status 200, same canonical.
- Extract strings into `pt-BR.json`. Ship this to production while only Portuguese is enabled. It's a pure refactor and lowers the risk of the later steps.
- Check caching: make sure static and ISR pages and any CDN cache vary correctly by locale (by path, not by cookie).

### Phase 2: data model and admin (about 1–2 weeks, can overlap Phase 1)
- Database migration: translation tables for products, categories, and any CMS content (banners, pages). Backfill pt-BR from the current columns.
- Data access: every catalogue query takes a `locale` and falls back to pt-BR.
- Slugs: look up products by `(locale, slug)`. Generate `alternates` from the sibling translations.
- Admin: language tabs, a translation status field, and optionally a "translate with machine translation" draft button.
- Search inside the store: index the product name and description per locale (Postgres full-text search needs the right dictionary per language: `portuguese`, `english`, `spanish`).

### Phase 3: translation and content (ongoing; starts in parallel)
- Translate the UI strings (a few hundred keys; quick to do professionally).
- Translate the catalogue, best-sellers first. Put "needs review" items behind a gate so they aren't indexed until they're approved.
- Legal content: terms, privacy, returns. These need a proper translation and probably a legal review per market. Note that LGPD still applies. Shipping and returns information must be honest about international delivery.

### Phase 4: checkout, payments, e-mail (about 1 week)
- Stripe: pass `locale` to the Checkout Session and keep `currency: 'brl'`. Confirm that the payment methods offered make sense for foreign cards. Pix and boleto are Brazil-only, so hide them or explain them for other locales. Look at foreign-card acceptance and fraud rules in Stripe Radar.
- Store `locale` on the order. Make the e-mail templates locale-aware: order confirmation, shipping, password reset, and any Stripe-triggered e-mails (receipts are sent in the customer's preferred locale if you set `preferred_locales` on the Stripe Customer).
- Taxes and duties: if you ship abroad, show clearly that import duties may apply. That's a business decision, but it affects the copy.

### Phase 5: SEO launch (about 1 week)
- Add the `hreflang` and canonical links, the localized sitemaps, and the localized JSON-LD. Validate with Search Console and a crawler (Screaming Frog or similar).
- Add `/en` and `/es` to Search Console and submit the sitemaps.
- Launch with **only the fully translated pages indexable**. Expand as translations are approved.
- Language switcher in the header: it keeps the current page (links to the translated slug of the same product) and uses real `<a href>` links so crawlers follow them.

### Phase 6: QA and rollout
- Test matrix: each locale × home, category, product, search, cart, checkout, e-mails, 404.
- Visual checks for text expansion (Spanish runs about 20–30% longer than English and breaks tight buttons and layouts).
- Release behind a flag, or by making the locales indexable gradually. Watch pt-BR organic traffic every week for regressions, and watch conversion by locale.

## Risks to watch
- **Hurting Portuguese SEO** through URL changes, auto-redirects, or broken canonicals. That's the biggest risk, which is why I default to no prefix for pt-BR and a test over current URLs.
- **Thin or machine-translated pages getting indexed** and dragging down the domain's quality signals. Gate them behind the review status.
- **Currency confusion at checkout.** If prices are in BRL, say so clearly on product pages and in the cart for non-Portuguese visitors.
- **E-mails sent in the wrong language from background jobs.** Always use the locale stored on the order.

## Rough effort
About 5–7 weeks of engineering for one or two developers, plus translation time, which depends on catalogue size. Multi-currency pricing, if you want it, would add a separate project of about 3–4 weeks.

Once you confirm the defaults (above all currency and the "no prefix for pt-BR" URL rule), I'd start with Phase 1 on a branch: install `next-intl`, add the `[locale]` routing, and extract strings with zero visible change.
