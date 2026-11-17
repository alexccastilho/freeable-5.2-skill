For a server-rendered Django monolith, moving to JWT mostly takes away things that sessions give you for free:
- instant logout and revocation;
- "log out other devices" after a password change;
- `request.session` storage;
- admin and messages-framework integration.

To keep logout and bans working you end up storing refresh tokens server-side, which brings back the state you set out to remove. The real work is replacing those losses and moving 30k logged-in users across without logging anyone out, not issuing tokens.

I have not seen the codebase, so the plan rests on the defaults below. Phase 0 checks them.

**Cheaper path.** If the trigger is the React widget, it can call your Django views with the existing session cookie plus the CSRF token: same origin, no tokens, a few hours of work. If the trigger is a mobile app or third-party API clients, issue JWTs for the API only and leave the pages on sessions. Both keep Redis sessions and change no user's login. If neither describes the driver, the full switch below is the plan. I plan what you asked below.

## Questions I would ask

1. **What is driving the switch: the React widget, a mobile app or external API, horizontal scaling, or getting rid of Redis?** Default: a full switch, as asked. If the answer is the widget, the cheaper path covers it. If it is a mobile app or API, JWT is added for `/api/` only and sessions stay for pages.
2. **Must logout, password change and account bans take effect at once?** Default: yes, so revocation stays possible:
   - access tokens are short-lived (`JWT_ACCESS_LIFETIME`, starting value 10 minutes, a guess to tune);
   - refresh tokens are rotated, and each one is recorded in a server-side table (or Redis) that can be revoked.

   If a delay up to the access-token lifetime is acceptable, the revocation list goes away and the design is simpler.
3. **Is the React widget served from the same origin as the Django pages?** Default: same origin, so tokens travel in `HttpOnly`, `Secure`, `SameSite=Lax` cookies, with no CORS and no tokens in JavaScript. If it is on another origin, tokens need `SameSite=None` cookies plus CORS, or a header, and the CSRF design changes.
4. **What else uses `request.session` besides login (carts, multi-step forms, impersonation, messages)?** Default: some uses exist. They stay on a slimmed-down session (keyed by an anonymous cookie, still in Redis) rather than being stuffed into the token. So Redis stays, holding less.
5. **Social login, SSO or 2FA (django-allauth, django-otp)?** Default: plain `django.contrib.auth` login. If allauth is used, its OAuth flow needs session state during the redirect. Keep sessions for that flow only.

Answer first: 1 and 2. Question 1 may shrink this to a few hours. Question 2 decides whether there is a server-side token store at all.

## Plan

### Phase 0: Inventory and baseline

- Grep for `request.session`, `login(`, `logout(`, `update_session_auth_hash`, `SESSION_`, `django.contrib.messages`, and any session-based packages (hijack, allauth, axes).
- List every page and endpoint the React widget calls.
- Record today's baseline over a normal week: login success and failure rate, 401/403 rate, and the "redirected to login" rate. The rollback rules below compare against it.

Check: a written list of every session use, with a replacement for each, or a decision to keep it on the slim session.

### Phase 1: Token plumbing behind a flag, no behaviour change

- **Library.** Add `djangorestframework-simplejwt`, or a small PyJWT wrapper if you do not use DRF. Two things are recalled, not verified:
  - simplejwt signs with `SECRET_KEY` unless `SIGNING_KEY` is set;
  - the rotation and blacklist options are `ROTATE_REFRESH_TOKENS` / `BLACKLIST_AFTER_ROTATION` with the `token_blacklist` app.

  Check both against the installed version.
- **Signing key.** Use a dedicated key, stored like your other secrets, with a `kid` header so it can be rotated without logging everyone out.
- **Middleware.** Write a `JWTCookieAuthenticationMiddleware`, placed after `AuthenticationMiddleware`. It reads the access cookie, validates the signature, expiry, issuer and audience, and sets `request.user`. Then `@login_required`, templates and permissions keep working unchanged. If the access token has expired and the refresh cookie is valid, it rotates both and sets the new cookies on the response.
- **Feature flag.** `AUTH_MODE` = `session` | `dual` | `jwt`, changeable without a deploy.
- **CSRF.** `CsrfViewMiddleware` stays on. Cookie-borne tokens are just as exposed to CSRF as session cookies.

Check: unit tests for an expired token, a bad signature, an unknown `kid`, rotation, and a revoked refresh token. The whole existing test suite passes with `AUTH_MODE=session`.

### Phase 2: Replace what sessions gave you (see the table below)

This must ship before any user is on JWT:
- logout revokes the refresh token;
- a password change revokes all of the user's refresh tokens;
- deactivating a user revokes their tokens;
- "log out everywhere" exists in account settings and in the admin.

Check: tests for each one, showing that the old refresh token is rejected right away and the access token is rejected within its lifetime.

### Phase 3: Dual mode, silent migration

- Set `AUTH_MODE=dual`. Requests authenticated by an existing session get JWT cookies minted on the response. New logins get JWTs. Both are accepted, so nobody is logged out.
- Leave it in place for at least `SESSION_COOKIE_AGE`. Django's default is two weeks; check your setting. After that, almost every active user has been moved across.
- **Revert rule:** if the login failure rate or the redirected-to-login rate rises more than 20% above the phase 0 baseline for an hour, set `AUTH_MODE=session`. Sessions are still being written in dual mode, so nobody is logged out by the revert.

### Phase 4: JWT only

GO / NO-GO, all must be true:
- At least 14 days in dual mode with no revert.
- Under 1% of authenticated requests still arrive on a session alone. Measure this with a counter in the middleware.
- Every item in the phase 0 inventory is replaced or deliberately kept on the slim session.
- Key rotation has been rehearsed in staging: a new `kid` is added and the old one retired without logging anyone out.

Then set `AUTH_MODE=jwt`. Remove the session auth backend from the login path, and keep the slim session only for the uses listed in question 4.

**Limit of rollback:** until you flush the old session keys in Redis, rollback is the flag. After the flush, rolling back logs everyone out once. So wait two weeks after the switch, then flush.

## What you lose, and what replaces it

| Today, free with Redis sessions | Replacement |
|---|---|
| Logout ends the session at once | Refresh token revoked on logout. The access token lives on until it expires (up to `JWT_ACCESS_LIFETIME`). |
| Password change logs out other devices (`update_session_auth_hash`) | Revoke all of the user's refresh tokens on password change |
| Ban or deactivate takes effect immediately | Revocation on deactivate, plus an `is_active` check during refresh |
| Admin can kill a user's session | "Revoke tokens" admin action |
| `request.session` storage | Slim anonymous session for the uses in question 4 |
| Django admin login | Keep admin on sessions (simplest), or move it to the JWT middleware |
| Messages framework (falls back to session storage) | `CookieStorage` for messages |
| Sliding expiry on activity | Refresh rotation in the middleware |

What the new design will hide: a stolen refresh token keeps working until it is used twice. Add reuse detection (an already-rotated token presented again revokes the whole family) and log it.

## Need from you

- `settings.py` (`MIDDLEWARE`, `AUTHENTICATION_BACKENDS`, the `SESSION_*` settings).
- The output of the phase 0 grep.
- Where the React widget is served from.
- What prompted the switch (question 1).
