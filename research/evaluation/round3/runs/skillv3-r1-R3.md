Translating the interface text is the small part of this. The work, and the risk, sit in three places. First, organic search: the new language URLs must not disturb the Portuguese pages that bring in your traffic today. Second, the catalogue: products in Postgres have one language, and every place that writes them, including the admin, needs a place to store translations and a way to track them. Third, everything that runs without a browser request, such as e-mails sent from Stripe webhooks or jobs, has to know the customer's language from saved data. The plan keeps every Portuguese URL exactly where it is, adds `/en` and `/es`, keeps prices in BRL, and treats this as a change of language, not a launch in new countries (Q1). I have not seen your code, schema or admin, so the file and table names below are placeholders. The first steps are the commands that find the real ones.

## Questions I would ask

Q1. Who are the English and Spanish visitors: people abroad you plan to sell and ship to, or people in Brazil (tourists, expats, neighbouring-country buyers who collect in Brazil)? - Default: language only. You still sell in BRL and deliver in Brazil only, and the EN and ES pages say so. If you are selling abroad, you also need other currencies, international shipping, duties and taxes, and payment methods. That project is bigger than the translation, and I would plan it separately.
Q2. May a product appear in English or Spanish before it has been translated? - Default: yes, but it shows the Portuguese text inside the translated page, is marked `noindex`, and stays out of that language's sitemap until translated. If no, untranslated products are hidden in that language, which means filters and category counts must handle missing products.
Q3. Who will translate the catalogue and keep it current? - Default: machine translation fills a draft when a product is saved, staff review the best-selling products first, and the admin shows each translation as missing, draft, reviewed or outdated.
Q4. Does checkout require a CPF or a Brazilian address (for example, for the nota fiscal)? - Default: yes. A visitor from Argentina reading the Spanish site would stop at checkout, so the EN and ES pages state both requirements before the cart. If not, no change.
Q5. Can I get read access to the repository, a read-only database connection and Google Search Console? - Default: yes. Otherwise, someone with access runs the first steps and sends me the output.

Answer first: Q1 and Q2. Q1 decides whether this is a translation or a market launch, and Q2 decides how much translation must be finished before launch.

## Plan

### Phase 1 - Inventory and routing (week 1)

1. **Routing.** Move pages under `app/[locale]/` with locales `pt-BR`, `en` and `es`. Portuguese is served with no prefix: middleware rewrites `/produto/x` to the `pt-BR` route internally, so no Portuguese URL changes or redirects. I would use next-intl for messages and routing. Its "as-needed" prefix mode does this, but the option names are from memory, so check them against the version you install. The locale comes only from the path, never from a cookie or `Accept-Language` on its own. That way a CDN or ISR cache cannot serve English to a Portuguese visitor, and each URL has one language for Google.
2. **No automatic redirect by browser language.** Googlebot mostly crawls without a Portuguese `Accept-Language`, so redirecting `/` to `/en` on that header could hide your Portuguese pages from Google. Instead, show a dismissible banner offering the other language, and remember the visitor's choice in a cookie that only affects which link the banner offers.
3. **Interface strings.** Extract them into `messages/pt-BR.json`, `en.json` and `es.json`. A missing key falls back to Portuguese, never to the raw key. CI fails on keys present in `pt-BR` and missing in the others, and on `next build` errors. Set `<html lang>` from the locale.

**First steps (need no answers):**
- `ls app/ && grep -rn "generateStaticParams\|middleware" app/ middleware.* --include=*.ts --include=*.tsx | head -50` to map the routes and any existing middleware.
- `grep -rln "[ãõçáéíóú]" app/ components/ --include=*.tsx | wc -l` to size the hardcoded Portuguese strings.
- In Postgres: `SELECT table_name, column_name FROM information_schema.columns WHERE table_schema='public' AND data_type IN ('text','character varying') ORDER BY table_name;` to find every catalogue text column (name, description, slug, SEO fields, category names).
- `grep -rn "INSERT INTO\|UPDATE products\|prisma.product.\(create\|update\|upsert\)" .` (adjust for your ORM) to list every writer of the catalogue, including import scripts, not only the admin.
- Export the top 500 Portuguese landing pages by clicks over the last 3 months from Search Console. This list is the regression check for steps 1 and 9.

### Phase 2 - Catalogue translations (weeks 2-3)

4. **Schema, additive only.** Add `product_translations (product_id, locale, name, description, slug, seo_title, seo_description, status, source_hash, updated_at)` with `UNIQUE (locale, slug)`, plus the same for categories and any other table found in the first steps. Portuguese stays in the existing columns as the source, so the migration changes no existing row and is reverted by dropping the new tables.
5. **Outdated translations.** `source_hash` stores a hash of the Portuguese text it was translated from. When any writer from the inventory changes the Portuguese text, the translation's status shows `outdated` in the admin. The check runs in the database or the shared save function, not only in the admin form, so imports are covered.
6. **Admin.** Add language tabs on the product form, a "translate draft" action (machine translation, Q3), and a list filtered by missing or outdated status, sorted by revenue. Check: edit one product's Portuguese description, and its English and Spanish translations show `outdated`.
7. **Pages.** Product and category queries join the translation for the current locale, falling back to Portuguese and applying the Q2 rule. Translated slugs resolve in their own locale. An old or unknown slug in a locale returns 404, not another product. If the site's own search uses Postgres full-text search, English and Spanish need their own text-search configuration; check how search is built in the first steps.

### Phase 3 - Money, checkout and e-mail (week 3)

8. **Prices and checkout.** Prices stay in BRL, formatted with `Intl.NumberFormat(locale, { style: 'currency', currency: 'BRL' })`, so an English visitor sees "R$1,234.56", clearly in reais. Pass the page locale to the Stripe Checkout session's `locale` parameter (from memory: accepts `pt-BR`, `en`, `es`; check against Stripe's API reference). Save `locale` on the order and on the customer when the session is created. The Stripe webhook and any e-mail job have no browser request, so they read the language from the order. E-mail templates exist per locale, and a missing template falls back to Portuguese. Check: place an order on `/es`, and the confirmation e-mail sent from the webhook arrives in Spanish. If Stripe sends its own receipts, set the customer's preferred language too (from memory: `preferred_locales` on the Stripe customer).

### Phase 4 - Search engines and launch (week 4)

9. **Search tags.** In `generateMetadata`, emit a self-referencing canonical URL and `alternates.languages` for `pt-BR`, `en`, `es` and `x-default` (pointing to the Portuguese URL). Only translated pages appear in each other's alternates. Use one sitemap per locale with the same alternates, and product structured data per locale with `priceCurrency: "BRL"`.
10. **Staged launch.** Deploy with EN and ES set to `noindex` site-wide, controlled by an environment setting, and have staff test the site and place a real order in each language. Before allowing indexing, all of these must be true:
    - each of the 500 Portuguese URLs returns 200 with the same canonical URL as before, with no redirect;
    - a crawl of `/en` and `/es` finds no broken links and no page whose canonical URL points to another language;
    - an order placed in each language completes and its e-mail arrives in that language;
    - the reviewed products are translated (whatever count Q3 agrees).
    Then switch on indexing for translated pages. Revert rule: if Portuguese organic clicks in Search Console fall more than 15% against the same weekday of the previous four weeks for three days in a row, set EN and ES back to `noindex`, remove the alternates, and check canonical URLs and alternates before trying again.

I am not moving Portuguese under `/pt-BR/`. It would put 301 redirects on every page that ranks today, and that is hard to undo. Leaving it unprefixed gives up only URL symmetry.
