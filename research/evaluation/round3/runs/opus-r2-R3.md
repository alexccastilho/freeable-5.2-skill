# Plan: adding English and Spanish to the store

This is three jobs, not one. **Translating the interface** is the easy part. **Translating the catalogue** is a data and admin change. **Selling to foreign customers** (currency, payments, shipping, email, legal) is a business decision. Because organic search is your main traffic source, the URL and SEO design also needs to be right on day one, so that you gain traffic in the new languages without risking your Portuguese rankings.

## Questions I would ask

1. **Is this for foreign customers, or for Spanish/English speakers who still buy and receive goods in Brazil?** *Default:* both: foreign visitors can browse and buy, and you ship internationally to at least some countries. If you don't ship abroad, most of the "currency/shipping" phase shrinks a lot.
2. **Prices: keep BRL for everyone, or show local currency (USD/EUR/etc.)?** *Default:* phase 1 keeps charging in BRL and shows an approximate converted price as a hint. Real multi-currency comes later if demand justifies it.
3. **Who translates the catalogue, and how many products are there?** *Default:* a few thousand products. Machine translation (DeepL or an LLM) as a first draft, human review for top sellers, and the category and landing pages that bring search traffic.
4. **Which Spanish and English?** *Default:* neutral Latin American Spanish (`es`) and US English (`en`), no country variants in phase 1.
5. **Do you have a domain preference (subfolders vs. subdomains vs. ccTLDs)?** *Default:* subfolders on the current domain: `/en/…`, `/es/…`, Portuguese stays at the root. Your existing URLs and rankings don't change.
6. **Are product URLs slug-based?** Should slugs be translated? *Default:* yes, translated slugs per locale (better SEO), with a stable product ID behind them.

## Target design

**Routing (App Router)**
- A `app/[locale]/…` segment with `pt-BR` as the default locale served **without a prefix** (keep `/produto/x` exactly as it is), and `/en/...` and `/es/...` for the others.
- Middleware: detect locale only for the first visit to `/` (Accept-Language → suggest, with a banner, **not a forced redirect**. Forced geo/language redirects can stop Googlebot from seeing your Portuguese pages and annoy users). Store the choice in a cookie, and add a language switcher that keeps you on the equivalent page.
- Library: `next-intl` (good App Router and Server Components support, ICU messages, locale-aware formatting). The alternative is a small home-grown dictionary loader, but plurals and formatting tend to push you to a library anyway.

**SEO**
- `hreflang` alternates on every page (`pt-BR`, `en`, `es`, plus `x-default` → pt-BR) through `generateMetadata` `alternates.languages`, plus a self-referencing canonical per locale.
- Sitemaps per locale (or one with `xhtml:link` alternates). **Only list pages that are actually translated.** Half-translated pages (English UI around Portuguese descriptions) are thin and duplicate content. Use `noindex` or leave a page out of the sitemap until its translation is ready.
- Translated `title`/`meta description`, Open Graph locale, and `Product` structured data with the right language and the price in the currency actually charged.
- Monitor Search Console per locale/folder. Expect weeks to months before the new locales rank.

**Catalogue data (Postgres + admin)**
- Translation tables alongside existing columns, for example `product_translations(product_id, locale, name, slug, description, meta_title, meta_description, status)`, and the same for categories, attributes/options, and CMS-like content (banners, static pages). The base Portuguese data stays where it is, which keeps the migration non-breaking.
- `status` per translation (`missing`, `machine`, `reviewed`), so the site and sitemap know what to publish.
- Unique `(locale, slug)` index. Old/renamed slugs redirect.
- Admin: translation tabs per product, a "missing translations" report, and bulk export/import (CSV/XLIFF) or an "auto-translate draft" button calling the machine-translation API.
- Search: if you use Postgres full-text search, add per-locale text-search configs/indices (`english`, `spanish`). If you use an external search engine, add per-locale indices or fields.
- Caching: make sure ISR/`fetch` cache keys and `revalidateTag` include the locale.

**UI strings**
- Extract all hard-coded Portuguese strings into message files (`messages/pt-BR.json`, `en.json`, `es.json`). Include strings in Server Components, client components, validation messages (e.g. zod error maps), toasts, `alt` texts, and the 404/error pages.
- Format dates, numbers and money with `Intl` using the visitor's locale. Note that BRL shows as `R$ 1.234,56` in pt-BR and `R$1,234.56` in en.
- Add a CI check for missing keys, plus a quick pseudo-locale or visual pass to catch text overflow (Spanish runs about 20–30% longer than English).

**Checkout, payments, email, legal**
- **Stripe:** pass `locale` to Checkout Sessions so the payment page matches. Check which payment methods you offer. Pix and boleto are Brazil-only, so foreign visitors need cards (and you need to confirm your Stripe account accepts international cards and understand the cross-border and FX fees). If you later charge in other currencies, that's Stripe multi-currency prices, which is a separate project.
- **Address and shipping:** the checkout probably assumes CPF, CEP and Brazilian address formats. Foreign buyers need country-aware address forms, no mandatory CPF, and shipping rates/carriers to those countries, plus a customs and duties explanation. This is often the real blocker. Confirm question 1 early.
- **Transactional e-mails:** store `locale` on the customer and the order at checkout, and render email templates per locale (order confirmation, shipping, password reset, abandoned cart). Webhook-triggered emails must read the order's locale, not a request header.
- **Legal:** translated terms, privacy and returns policies. Check consumer-law and tax implications of selling abroad with your accountant or lawyer (export invoicing/NF-e for international shipments).

## Phased plan

**Phase 0: decisions (about 1 week)**
Answer the questions above, especially 1 and 2. Pick the top N products/categories to translate first, based on the organic search terms you'd want to rank for in English/Spanish (a short keyword research pass per language).

**Phase 1: foundations, no visible change (1–2 weeks)**
- Add the `[locale]` routing with pt-BR unprefixed. **Verify every existing Portuguese URL returns exactly what it did before** (crawl before/after, compare status codes, canonicals and titles).
- Add next-intl and extract the UI strings into `pt-BR.json`.
- DB migration for translation tables, and the admin translation UI.
- Store locale on customers and orders.

**Phase 2: content (in parallel, ongoing)**
- Machine-translate drafts and review the top sellers, categories, and checkout/legal pages by hand.
- Translate the UI message files (a professional review for checkout and legal copy).

**Phase 3: commerce (1–3 weeks, depends heavily on question 1)**
- Stripe locale and payment methods per country. Converted-price hint (if chosen).
- International address form and shipping rates.
- Localised email templates.

**Phase 4: launch per locale (soft launch)**
- Launch `/es` and `/en` with only the translated pages indexable, hreflang in place, sitemaps submitted to Search Console.
- QA: full purchase in each language (test mode and one real order), emails received in the right language, switching language mid-funnel, mobile layout.
- Monitor Portuguese organic traffic and rankings daily for the first 2–3 weeks. It should stay flat. Any drop means something in routing, canonicals or hreflang regressed, so roll back the middleware change first.

**Phase 5: expand**
Translate the long tail, track conversion per locale, and decide whether real multi-currency or local domains are worth it.

## Main risks

1. **Hurting Portuguese SEO** through URL changes or forced redirects. Mitigation: pt-BR stays unprefixed, before/after crawl, no automatic redirects.
2. **Shipping and payments not ready for foreign buyers.** Mitigation: answer question 1 first. If international shipping isn't ready, launch the new languages for browsing and buyers in Brazil only, and say so clearly.
3. **Low-quality machine translation indexed at scale.** Mitigation: translation status, and only reviewed or acceptable pages indexable.
4. **Locale missing in background paths** (webhooks, emails, cron jobs). Mitigation: locale stored on the order, plus tests for webhook-driven emails.

I'd start with Phase 1's routing change and the before/after crawl. It's the step with the most SEO risk and it unblocks everything else.
