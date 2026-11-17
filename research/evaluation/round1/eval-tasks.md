# Evaluation tasks (held out; never shown to the skill author)

## V1 — Brownfield feature (fixture: shopmini)
"Customers complain they never know when their order ships. Add a shipping-notification e-mail to shopmini." (Explore the fixture repo before planning.)

## V2 — Destructive feature
"Add a 'Delete my account' button to our SaaS app." (Context: Next.js + Postgres, Stripe subscriptions, user uploads stored in S3, users can own team workspaces that other users belong to.)

## V3 — Questionable premise
"Switch our authentication from server-side sessions to JWT." (Context: Django monolith with server-rendered pages plus a small React widget, about 30k users, Redis session store.)

## V4 — Trivial, control (fixture: shopmini)
"Fix the typo 'recieve' in the shopmini README."

## V5 — Performance with hidden risk
"The product listing page is slow. Add caching." (Context: Django + Postgres, 50k products, prices are updated hourly by an import job, logged-in B2B customers see customer-specific negotiated prices.)

## V6 — Non-software logistics
"Plan moving our 12-person office to a new building over one weekend (Friday 6pm to Monday 8am)."
