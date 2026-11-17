Translating the interface text is the small, mechanical part. Two other parts carry most of the effort and risk.
- **Protecting Portuguese search traffic.** Organic search is your main traffic source, so the Portuguese URLs must not move, and the new language versions must be linked to them with hreflang. A wrong redirect or canonical can cost the rankings you already have.
- **The catalogue.** Product names, descriptions and slugs live in Postgres and are edited in your admin. They need a per-language schema, admin screens, and someone to translate every product, and to keep translating as products change.

Prices stay in BRL under the default below, so this plan is about language, not about selling abroad.

I have not seen the codebase, schema, admin or e-mail setup, so the plan rests on the defaults below.

## Questions I would ask

1. **Is the goal to serve people who buy and ship within Brazil (expats, tourists, Spanish-speaking neighbours shipping to Brazil), or to sell to customers abroad?** Default: language only. BRL prices and Brazilian shipping, payment methods and taxes stay as they are, and every page states that prices are in BRL. If the goal is selling abroad, this becomes a market-expansion project (currency display and charging, international shipping, taxes, Stripe payment methods, terms of sale), which needs its own plan. The language work below is still its first half.
2. **Who will translate the catalogue, and how many products and categories are there?** Default: machine translation as a draft, then human review, starting with the top sellers and the category pages. A product page is indexed in English or Spanish only after its translation has been reviewed. Until then it shows the Portuguese content and carries `noindex` in that language.
3. **Should Portuguese keep its current URLs at the root, with English and Spanish under `/en` and `/es`?** Default: yes. Every existing Portuguese URL stays exactly as it is today. If you prefer separate domains, routing changes, but the rest of the plan does not.
4. **Which variants: neutral Latin American Spanish and general English?** Default: yes, as `es` and `en`. The hreflang values can be narrowed later.
5. **Do legal pages (terms, privacy, returns) need professional translation?** Default: yes, translated by a professional. Machine translation is not used for these. Customer reviews are shown in their original language.

Answer first: 1 and 2. Question 1 decides whether this is a language project or a new-market project. Question 2 sets the size of the largest phase, and nobody can estimate that without a product count and a translator.

## Plan

**Phase 0: inventory (short).** Count UI strings, products, categories, CMS pages and transactional e-mail templates. List the current URL patterns, sitemap, canonical tags and structured data. Export the top Portuguese landing pages from Search Console with clicks and impressions for the last 8 weeks. That is the baseline phase 5 is measured against.

**Phase 1: routing with no visible change.** Move the route tree under `app/[locale]/` with `pt-BR` as the default locale, served without a prefix, and `en` and `es` added but not linked or indexed yet. I would use `next-intl` for App Router routing and messages. The middleware and config API names are from memory, so check them against the current version's docs before building. **Do not redirect automatically based on `Accept-Language` or IP.** Googlebot mostly crawls with English headers from the US, so an automatic redirect would hide the Portuguese pages from it. Offer a language switcher and a dismissible suggestion banner instead. Make sure static generation and caching are keyed per locale (`generateStaticParams` for each locale).
*Check:* crawl the top Portuguese URLs from phase 0 before and after deploy. Same status codes, same canonical, same HTML title and meta tags. **Revert rule:** any difference in that crawl blocks the release.

**Phase 2: interface text and formatting.** Extract strings into `pt-BR`, `en` and `es` message files. Format numbers, dates and currency with `Intl` per locale (BRL in every locale, so `R$ 1.234,56` in Portuguese and `R$1,234.56` in English). Add a build check that fails when a key is missing in any locale.

**Phase 3: the catalogue (the bulk of the work).**
- Schema: `product_translations (product_id, locale, name, description, slug, meta_title, meta_description, status, source_updated_at)`, with the same pattern for categories. Portuguese stays in the existing columns as the source. Slugs are unique per locale.
- Admin: a per-language tab on the product form, a "needs review" status, and a list of untranslated or outdated products, sorted by sales.
- **What this hides:** a change to the Portuguese description silently leaves the English and Spanish versions out of date. When the Portuguese source changes after a translation was made, mark the translation "outdated" so it shows up in that list.
- Translation pipeline: a machine-translation draft goes in as "needs review", and the reviewer approves it. Only approved translations are indexed (question 2).
*Check:* a product with no translation renders in Portuguese with `noindex` under `/en`, and an approved product renders in English with its own slug.

**Phase 4: SEO wiring.** On every page, add hreflang alternates for `pt-BR`, `en` and `es`, plus `x-default` pointing to Portuguese. List only the language versions that are actually indexable, so a page with no approved translation does not advertise one. Each language version gets a canonical pointing to itself. Use a sitemap per locale with alternates. Put metadata and Product structured data in each language, with `priceCurrency: BRL`.
*Check:* validate a sample with Search Console's URL Inspection and a hreflang checker. Every alternate must link back to the others; tags that are not reciprocal are ignored.

**Phase 5: checkout and e-mail.** Store the customer's language on the session, the account and the order. Pass the language to Stripe Checkout (`locale`: `pt-BR`, `en`, `es`; recalled values, check them in Stripe's docs). For receipts that Stripe itself sends, set the customer's `preferred_locales`. Your own transactional e-mails use templates for each language, picked from the language stored on the order, not from the browser at send time.
*Check:* place a test order in each language and confirm that the Checkout page, the Stripe receipt and every e-mail of yours arrive in that language.

**Phase 6: launch in stages.** Make `en` and `es` public, with the switcher visible but every page in those languages set to `noindex`. Finish phase 3 for the top sellers, then remove `noindex` from approved pages in batches, highest-selling first.
- **Stop rule for each batch:** if Portuguese organic clicks on the phase 0 pages fall by more than their normal week-to-week variation (measured over the 8-week baseline), pause further batches and check canonicals and hreflang before going on.

The order is deliberate. Routing ships first, with no visible change, so that any SEO regression can be traced to it alone and not mixed up with content changes.

## What changes in the way you work

| Today | After |
|---|---|
| One field per product, edited once | Three languages per product. A Portuguese edit flags the other two as outdated, and someone has to update them |
| One URL per page, one cache entry | Three of each. Cache invalidation on product updates has to cover every locale |
| E-mails in one language | The language is stored per order and used for every e-mail sent about that order |

## Found, not touched

- Prices in BRL may confuse foreign visitors. Showing an approximate conversion is out of scope under question 1's default.
- Support (chat, e-mail replies) in English and Spanish is a staffing question, outside the code.

## Need from you

- Answers to questions 1 and 2, with the product and category counts.
- Read access to the repository and the Postgres schema.
- Access to Search Console for the baseline in phase 0.
