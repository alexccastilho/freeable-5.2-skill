# Sessions → JWT for the Django app

Before planning the migration, I want to push back a bit. For a server-rendered Django monolith, moving all of auth to JWT usually makes things worse, and I'd like to know what problem we're solving first.

## Why I'm hesitant

- **You lose instant logout and revocation.** Today, logout, "sign out everywhere", password reset, and banning a user all work by deleting a session from Redis, and the effect is immediate. A JWT stays valid until it expires. Getting revocation back means a denylist or token-version check on every request, which needs a server-side store (Redis again). At that point you're running sessions with extra steps.
- **CSRF protection is still needed.** Server-rendered pages need the token in a cookie for full page loads, and that brings back the same CSRF exposure. If you put it in `localStorage` to avoid that, any XSS can steal it.
- **Django's ecosystem assumes sessions.** That includes `request.user` through `AuthenticationMiddleware`, the admin, `login_required`, messages, `django-allauth`, and so on. Every piece needs a custom JWT backend, or keeps using sessions anyway.
- **30k users in Redis is tiny.** Session lookups aren't a scaling problem at this size.

The React widget doesn't need JWT either. If it's served from the same site, it can call Django endpoints with the existing session cookie plus the `csrftoken` header. That works today with no auth changes.

## Questions I would ask

1. **What's driving this?** For example: a mobile app or third-party API clients coming, the widget being embedded on *other* domains, a split into separate services, Redis cost or ops pain, or a security or compliance requirement.
   *Default: I'll assume the real need is token auth for non-browser or cross-origin API clients (most often the widget or a planned mobile app). I'll plan for **adding** JWT for the API while keeping sessions for the browser, not ripping sessions out.*
2. **Where's the widget served from: same origin as Django, or embedded on other sites?**
   *Default: same origin.*
3. **Do you need "log out everywhere" and immediate account bans?**
   *Default: yes. That's why I'm keeping server-side state for revocation.*
4. **What do you use for auth today:** plain `django.contrib.auth`, allauth, SSO/SAML?
   *Default: `django.contrib.auth` with the Redis session backend.*
5. **Is it OK for users to be logged out once during the cutover?**
   *Default: no. The plan below avoids a forced logout.*

## Recommended plan (default: hybrid)

**Browser pages keep sessions. The API also accepts JWT.**

1. **Add `djangorestframework-simplejwt`** (or DRF if the API isn't on it yet).
   - Access token lifetime 5–15 minutes. Refresh token lifetime 7–30 days, with rotation and blacklisting turned on, so a reused refresh token gets rejected and its family revoked.
   - Sign with RS256 or ES256 if any other service will verify tokens. HS256 is fine if only Django does. Put the key in your secret manager and plan for a `kid` header so keys can be rotated.
2. **API authentication classes:** `SessionAuthentication` first, then `JWTAuthentication`. The same-origin widget keeps working on cookies, and new clients use bearer tokens.
3. **Token endpoints:** `/api/token/` (login with credentials), `/api/token/refresh/`, `/api/token/revoke/`. Optionally add an endpoint that exchanges a valid session for a JWT pair, so a logged-in browser user can hand tokens to a cross-origin widget without typing their password again.
4. **Revocation:** add a `token_version` integer on the user, and put it in the token claims. Bump it on password change, "log out everywhere", and deactivation. Check it on refresh (cheap). If bans must be instant, also check it on access (one cached lookup). The refresh-token blacklist lives in the DB or Redis.
5. **Rate-limit** the token and refresh endpoints the same way login is today.
6. **Tests:** API works with either session or JWT. Expired access token gets 401. Rotated or reused refresh token is rejected. A password change invalidates existing refresh tokens. Pages and the admin still behave exactly as before.

Nothing changes for current users. There's no migration and nobody gets logged out, and Redis stays as it is.

## If you really do want sessions gone entirely

If the answer to question 1 is something like "we're moving to stateless services and Redis has to go", here's how I'd do it safely:

1. **Auth layer:** write a custom middleware or auth backend that reads the access JWT from an `HttpOnly; Secure; SameSite=Lax` cookie and sets `request.user`. Refresh happens through a second cookie scoped to `/auth/refresh`. Keep Django's CSRF middleware on, since cookie auth still needs it.
2. **Dual-read period:** accept the session *or* the JWT cookie. When a request arrives with a valid session and no JWT, issue JWT cookies on the spot. Active users migrate silently, and nobody is forced to log out.
3. **Anything else in the session:** flash messages, cart or wizard state, `next` URLs. Move these to cookies, the DB, or `CookieStorage` for messages. Audit `request.session` usage first, because that's usually the hidden part of the work.
4. **Admin:** decide whether the Django admin moves too, or stays on sessions behind staff-only access. Keeping it on sessions is simpler and safer.
5. **Revocation:** the `token_version` check from above, plus a short access-token lifetime. Be clear that "instant ban" then depends on that lifetime or on a per-request lookup.
6. **Rollout:** behind a flag, first for staff, then a percentage of users. Watch 401 rates and refresh failures. After about one refresh-token lifetime with all traffic on JWT, stop reading sessions and retire the Redis session store.
7. **Rollback:** during the dual-read period, turning the flag off falls back to sessions with no user impact. Keep it that way until you're confident.

Scope is a few days for the hybrid. For the full replacement it's 2–3 weeks, mostly the `request.session` audit, the admin, and testing.

---

Tell me what's behind the request (question 1) and I'll go with the hybrid or the full plan. If it's the widget, I'd first try having it use the existing session and CSRF token. That might be a one-afternoon fix.
