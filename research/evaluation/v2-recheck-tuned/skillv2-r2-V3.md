By default I'd keep server-side sessions for the server-rendered pages and only add tokens where a client actually can't use a cookie session. Two things matter more here than the choice of token format.

First, your pages are rendered by Django in the browser. That means a cookie has to carry the credential anyway. A JWT in an HttpOnly cookie is still a session, but one you can't revoke: logout, password change and disabling an account all stop working until the token expires, unless you build a server-side denylist, which puts the Redis lookup back.

Second, 30k users on a Redis session store isn't a scaling problem. So it matters what's driving the request. If it's the React widget, a same-origin widget can call Django with the session cookie plus a CSRF token, and no JWT is needed. If it's a mobile app, partners or a separate service, JWT goes on the API only, next to the sessions.

I haven't seen the code, so the plan rests on the defaults below. If the reason is stateless auth across several services or domains with no shared session store, the full switch at the end applies.

## Questions I would ask

1. **What is driving this: the React widget, a mobile or partner API, other services that need to verify users, or a sense that sessions don't scale?** Default: the widget, so no JWT is issued, and sessions plus CSRF cover it. If it's a mobile or partner client, Phase 2 adds JWT for `/api/` only. If several services must verify users without a shared store, the full switch applies.
2. **When a user logs out, changes their password or is disabled, how quickly must access stop?** Default: immediately for browsers, which is what sessions give you today. For API tokens, within the access-token lifetime (15 minutes, as a setting). If API access must also stop immediately, refresh and access checks go through a per-user token version, which is one cache lookup per request.
3. **Is the widget served from the same domain as the Django pages?** Default: yes, so the session cookie reaches the API with no CORS changes. If it's on another domain, it either moves under the main domain (cheapest) or becomes an API client in Phase 2.
4. **Are there any clients besides browsers today (a mobile app, scripts, integrations)?** Default: none. Phase 0 checks the logs for them.
5. **Can I see the repository and the access logs?** Default: no. Phase 0 lists what to look for.

Answer first: 1 and 3. If the widget is the driver and it's same-origin, the work shrinks to one small change.

## Plan

**Phase 0: Inventory (no change to production)**
- List what depends on sessions as well as authentication: `request.session` uses (carts, wizards, flash messages if `SessionStorage` is used), the admin, password reset, any impersonation or "log out other devices" feature, and social login.
- Find out how the widget calls the backend today: which endpoints, what auth, and same origin or not.
- Group the access logs by path and user agent for 7 days, to find non-browser callers.
- Check: a written list of callers and session uses. Nothing here is a question any more.

**Phase 1: Widget on the session (default driver)**
- The widget reads the CSRF token (from the `csrftoken` cookie, or a value rendered into the page) and sends it as `X-CSRFToken` on unsafe methods, with `credentials: 'same-origin'`.
- API views use session authentication. In DRF that's `SessionAuthentication`, which enforces CSRF.
- Failure modes:
  - Expiry: if the session expires while the widget is open, the API returns 401/403 and the widget redirects to login instead of failing silently.
  - Many callers at once: doesn't apply, because sessions have no refresh race.
  - Redis down: same behaviour as today, nothing new.
- Check: a test that a POST without the CSRF header gets 403 and one with it gets 200. Then a manual run through logout, after which the widget's next call fails.

**Phase 2: JWT for non-browser clients, only if Q1 or Q4 says so**
- Add `djangorestframework-simplejwt` on `/api/` routes alongside `SessionAuthentication`, so browsers keep working untouched.
- Access tokens last 15 minutes and refresh tokens 14 days, both as settings. Rotate refresh tokens and blacklist the old one.
- The setting names (`ROTATE_REFRESH_TOKENS`, `BLACKLIST_AFTER_ROTATION`, the `token_blacklist` app) are from memory. Check them against the installed version's documentation before relying on them.
- Failure modes:
  - Revocation: a `token_version` field on the user goes into the token and is checked on refresh. Changing the password or disabling the account bumps it, so a revoked user loses access within one access-token lifetime.
  - Many callers at once: a client that refreshes from two threads loses one request to the blacklist. Allow a grace window of a few seconds for the token being replaced, or make the client serialise refreshes.
  - Clock skew: allow 30 seconds of leeway.
  - Key handling: a dedicated signing key, not `SECRET_KEY`, with a key ID in the header so it can be rotated without logging everyone out.
  - Unknown caller: tokens aren't accepted on the HTML views, so a leaked token can't drive the site through a browser.
  - Storage: tokens are for clients that keep secrets well (a mobile app's keychain, a server). They're never put in browser `localStorage`.
- Rollout: behind a flag, enabled for one client first. Revert rule: if the 401 rate on `/api/` for that client goes above 1% over its baseline for an hour, turn the flag off. Sessions are unaffected either way.

**Branch: full switch to JWT, selected by "several services or domains must verify users without a shared store"**
- Phases:
  1. The Phase 0 inventory.
  2. Move every `request.session` use to the database or the client.
  3. Middleware that accepts a JWT in an HttpOnly, Secure, `SameSite=Lax` cookie alongside the session (CSRF protection stays).
  4. Dual-accept for at least one session lifetime.
  5. Stop issuing sessions.
  6. Remove the session store.
- Largest cost: rebuilding revocation (a per-user token version checked on every request) and retesting every authentication path, including the admin and password reset.
- Rollback: simple until step 6. After the session store is removed, rolling back means everyone logs in again.
- Go/no-go before step 5:
  - The dual-accept period has run for 14 days with authentication error rates no more than 0.5% above baseline.
  - Logout, password change and account disable have each been tested to cut off access within the stated window.
  - No code path reads `request.session`, which a grep and a test run with the session middleware removed both confirm.

What sessions give you for free today, and what would replace each under the branch:
- Logging out instantly everywhere: replaced by a token version check.
- Somewhere to keep per-user state: replaced by database tables.
- A small cookie: JWTs grow with their claims, so keep the claims minimal.
- Django's built-in integration for the admin, messages and login: replaced by custom middleware, which needs its own tests.
