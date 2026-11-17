# Sessions → JWT: before planning the switch

I can plan this migration, but first, a straight answer: **for a Django monolith that renders its pages on the server, replacing sessions with JWT usually makes things worse, not better.** I'd want to know what problem we're solving before committing, because the right plan depends on it.

What you'd give up or take on:

- **Revocation gets hard.** Today "log out", "log out everywhere", "password changed", and "ban this user" all come down to deleting a session from Redis. With stateless JWTs, a stolen or old token stays valid until it expires. The usual fix is a deny-list or token-version check in Redis on every request. That brings back the server-side lookup JWT was supposed to remove, so you'd end up with sessions under a different name.
- **Server-rendered pages need a cookie anyway.** Browsers don't attach `Authorization` headers to normal page loads and form posts. The JWT would live in a cookie, so you still need CSRF protection. Putting it in `localStorage` instead exposes it to any XSS.
- **You lose Django's built-in pieces:** `login()`/`logout()`, the `login_required` flow, admin auth, `messages`, session-based password-reset invalidation, and anything third-party that assumes `request.session`. Each needs replacing or a workaround.
- **The cost of what you have today is small.** 30k users in Redis is a tiny amount of data. Session lookups are sub-millisecond, and scale isn't a reason to move.

## Questions I would ask

1. **What's driving the change?** This is the main one. Common answers, and what I'd do for each:
   - *"The React widget needs to call our API."* If it's served from the same domain, it can **already use the session cookie**: Django REST Framework `SessionAuthentication` plus the CSRF token header. No JWT needed.
   - *"We're adding a mobile app / a separate frontend on another domain / third-party API clients."* Add token auth **for those clients only** (DRF + `djangorestframework-simplejwt`, or OAuth2 via `django-oauth-toolkit` for third parties). Pages keep sessions. This is the common, low-risk setup.
   - *"We're splitting into services that need to verify identity without calling the monolith."* That's a real reason for signed tokens. Even then, I'd have the monolith issue short-lived JWTs to the services and keep browser sessions as they are.
   - *"Someone said sessions don't scale / Redis is a single point of failure."* That's better solved with Redis replication/Sentinel than with an auth rewrite.
2. **Is a forced logout for all 30k users acceptable at cutover?** Default: **no**. Plan a transition where both work.
3. **Any SSO, social login, or admin users with special requirements?** Default: Django admin keeps session auth regardless.
4. **What token lifetime and "log out everywhere" behavior do you need?** Default: 5-minute access tokens, 14-day rotating refresh tokens, and "log out everywhere" supported.

**Default if no one answers:** I'd assume the driver is the React widget plus likely future API clients. I'd recommend the **hybrid** below: keep sessions for the Django pages, and add JWT only for API clients that can't use cookies. If you confirm you really do want sessions gone entirely, the full-replacement plan follows it.

## Recommended: hybrid (sessions for pages, tokens for API clients)

1. **Widget:** move its API calls to DRF with `SessionAuthentication`. Send `X-CSRFToken` from the `csrftoken` cookie and set `credentials: 'same-origin'`. Often this is just a small fetch-wrapper change.
2. **Token endpoint for non-browser clients:** add `simplejwt`, with `/api/token/` and `/api/token/refresh/`, and refresh-token rotation plus a blacklist (the `token_blacklist` app). Set `DEFAULT_AUTHENTICATION_CLASSES = [SessionAuthentication, JWTAuthentication]` so each API view accepts either.
3. **Revocation:** add a `token_version` field to the user. Put it in the JWT claims and check it in a small custom authentication class. Bump it on password change, "log out everywhere", and deactivation, and delete that user's Redis sessions at the same moment so both kinds of credential are revoked together.
4. **Tests:** API views accept a session + CSRF or a valid JWT, and reject expired, tampered, or old-version tokens. A password change kills both. Pages are unchanged, and the existing test suite should pass untouched.

Nobody gets logged out, the pages don't change, and the risk is low. Effort is roughly a few days.

## If you really want to remove sessions entirely

Only if question 1 gives a reason that requires it. Shape of the plan:

1. **Token design:** short-lived access JWT (5 min) and a rotating refresh token (14 days), both in `HttpOnly; Secure; SameSite=Lax` cookies scoped to your domain. Not `localStorage`. Asymmetric signing (RS256/EdDSA) if other services verify tokens. Key rotation via `kid`.
2. **Server-side state you still need:** a refresh-token table or Redis set (for rotation, reuse detection, and "log out everywhere") plus `token_version` on the user. Be clear that this is still state. You're moving it, not removing it.
3. **Middleware:** a custom Django authentication middleware reads the access cookie and sets `request.user`. When it's expired but the refresh token is valid, it issues new tokens inside the response. CSRF middleware stays on, because the tokens are cookies.
4. **Replace session-dependent features:** `login()`/`logout()` views, `messages` (switch to `CookieStorage`), anything storing data in `request.session` (grep for it: carts, wizards, "next" URLs), password-reset invalidation, and admin login (or keep sessions just for `/admin/`).
5. **Migration without mass logout:** run both auth methods in parallel. A request with a valid Django session and no JWT cookie gets JWT cookies issued transparently. After about 2 weeks, plus the longest session age, stop accepting sessions, then retire the Redis session store.
6. **Rollout:** behind a feature flag, staff first, then a percentage of users. Watch login error rates and 401/403s. Rollback means turning the flag off, and sessions still work because we haven't deleted them yet.
7. **Security review before going live:** XSS surface (cookies are HttpOnly, but check), CSRF on every state-changing endpoint, refresh-reuse detection, clock skew, and the allowed algorithm list (reject `none`/HS-with-public-key confusion).

Effort is realistically a few weeks including testing, with ongoing complexity afterwards. That's why I'd only take this path with a concrete reason.

---

**Next step:** tell me what's prompting the switch (question 1). If it's the React widget, the fix is probably small and doesn't touch login at all.
