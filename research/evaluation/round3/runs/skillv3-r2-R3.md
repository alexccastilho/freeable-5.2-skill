Translating the interface strings is the small part of this. Most of the effort sits in three places. First, the product catalogue: it lives in Postgres behind your admin, so every product needs per-language fields, an admin screen to fill them, and someone to write the translations. Second, organic search: the Portuguese URLs that bring in your traffic today must not move or change, and the new languages should only become indexable once they are actually translated. Third, the parts of the site that run without a browser request, Stripe Checkout and the transactional e-mails: they need the customer's language stored on the order. The plan keeps Portuguese exactly where it is, adds `/en` and `/es`, keeps prices in BRL, and opens each new language to search engines only after a go/no-go check. I have not seen your repository, schema or Search Console, so the first steps below are the commands that would show them. The library and option names are as I remember them, flagged where they appear.

## Questions I would ask

Q1. What is driving this: serving English and Spanish speakers who buy and receive orders in Brazil, or selling abroad? Default: language only. Prices stay in BRL, with the same shipping and the same payment methods. If you want to sell abroad, currency display, international shipping, duties and taxes, and which payment methods Stripe enables per country become a separate project after this one. That is several more weeks.

Q2. Who writes the catalogue translations, and how many products are there? Default: machine-translated drafts, reviewed by a person in the admin. Each language goes live with the products that make most of the revenue, and the rest follow. There is no product-count target until I know the total.

Q3. Can English or Spanish pages show some Portuguese text at launch? Default: yes, but any product page that is not fully translated stays out of that language's sitemap and is marked `noindex`, so a half-translated page is never what search engines see.

Q4. Which Spanish? Default: neutral Latin American Spanish, `es`, with the hreflang tag set to `es`. If you mean Spain, it becomes `es-ES`, with different wording in places.

Q5. Can I see the repository, the database schema and Search Console? Default: no, so someone with access runs the first steps.

Answer first: Q1 and Q2. Q1 decides whether this is a language project or a market project. Q2 decides most of the timeline.

## Plan

### Phase 1: inventory and baseline

**First steps** (none needs an answer):
1. Save today's search baseline. In Search Console, export the top 500 landing pages by clicks for the last 3 months, and crawl the live site with Screaming Frog or a similar crawler, recording each URL's status code and canonical. This is what launch is checked against.
2. Find the catalogue tables and columns: `SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_schema = 'public' AND table_name ILIKE ANY (ARRAY['%product%','%categor%','%collection%','%page%']) ORDER BY 1;`
3. Find every writer of product text, because a translation that one writer ignores goes stale: `grep -rnE "INSERT INTO products|UPDATE products|products\.(create|update|upsert)" --include=*.ts --include=*.tsx --include=*.sql .`. Look for imports and ERP or feed syncs as well as the admin.
4. Find the places Portuguese is assumed: `grep -rnE "pt-BR|'pt'|toLocaleString|Intl\.|portuguese|lang=" app/ src/ lib/`. This covers date and price formatting, `<html lang>` and Postgres full-text search configured as `portuguese`.
5. List the e-mail templates, and find where each e-mail is triggered: a request handler, a Stripe webhook or a job.

### Phase 2: routing and interface strings (Portuguese unchanged)

- Portuguese stays unprefixed at its current URLs. `/en/...` and `/es/...` are added through a `[locale]` segment, with middleware that rewrites unprefixed paths to `pt-BR`. One way to do this is `next-intl` with prefixes on every locale except the default (I remember this as its `localePrefix: 'as-needed'` option; check it against the installed version's documentation), or the hand-rolled dictionaries pattern from the Next.js internationalization guide. Check: every URL from first step 1 returns the same status code, canonical and HTML title as in the baseline crawl.
- **No automatic redirect based on `Accept-Language`.** Googlebot crawls mostly from the US with English headers. A redirect would send it away from the Portuguese pages that rank today. Visitors get a dismissible "Ver em / View in" banner instead, and their choice is kept in a cookie.
- Move the interface strings into message files: `messages/pt-BR.json`, `en.json` and `es.json`. Format prices with `Intl.NumberFormat(locale, { style: 'currency', currency: 'BRL' })`, so the amount stays in BRL in every language.
- While translation is incomplete, `/en` and `/es` carry `noindex` and appear in no sitemap. This is a single setting per locale. Check: `curl -s https://<site>/en/ | grep -i noindex` returns a match.

### Phase 3: catalogue translations

- Add a `product_translations` table: `product_id`, `locale`, `name`, `description`, `slug` and SEO fields, with a unique index on `(locale, slug)`. Do the same for categories and content pages. Portuguese stays in the existing columns, so nothing moves and the change can be undone by dropping the new tables.
- In the admin, add a tab per language, with a "translated and reviewed" flag and an "outdated" marker. The marker is set whenever the Portuguese text changes, by every writer found in first step 3.
- Machine-translation drafts are written as unreviewed, never published directly.
- On the storefront, a product with no reviewed translation shows Portuguese text, gets `noindex` and stays out of that language's sitemap.
- If a translated slug changes, the old slug redirects with a 301.
- Search: if it uses Postgres full-text search, index each language with its own text-search configuration (`english`, `spanish`).

### Phase 4: checkout and e-mails follow the customer's language

- Add a `locale` column to orders, and to customers if accounts exist. It is set at checkout from the route the customer is on. E-mails are sent from webhooks and jobs, which have no cookie or URL to read, so the stored column is the only reliable source. Orders that existed before have no value and default to `pt-BR`.
- Pass the locale to the Stripe Checkout Session (I remember the values as `pt-BR`, `en` and `es`; check them against Stripe's API reference).
- E-mail templates are written per locale and fall back to Portuguese when one is missing. Check: place one test order in each language in Stripe test mode, and confirm that the Checkout page, the confirmation e-mail and the shipping e-mail all arrive in that language.
- Legal pages (terms, privacy, returns) need a translation reviewed by whoever owns them, before checkout is offered in that language.

### Phase 5: open each language to search engines, one at a time

All of these must be true before the `noindex` comes off a language:
- The products that make up most of revenue (the share decided by Q2) have reviewed translations.
- The legal pages and every e-mail template exist in that language.
- The baseline crawl shows no change to any Portuguese URL.
- Every indexable page carries reciprocal `hreflang` alternates (`pt-BR`, `en`, `es`, `x-default` pointing to Portuguese). Check: a crawler's hreflang report shows no missing return links.

Then remove the `noindex` and submit that language's sitemap. Check: Search Console shows the sitemap processed with no errors within a week.

**Revert rule:** if clicks to Portuguese pages fall by more than about 10% against the same weeks of the baseline for two weeks in a row, and there is no seasonal reason, put the new language back on `noindex` while you investigate. The 10% is a starting threshold, to be adjusted once you see normal week-to-week variation.

Spanish follows English using the same gate. Phase 4 comes before phase 5 on purpose: a customer who arrives from search in English should not end up with a Portuguese checkout and Portuguese receipts.
