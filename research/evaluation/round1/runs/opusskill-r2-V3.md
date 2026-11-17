With 30k users, Redis sessions are not a scaling problem, and issuing tokens is the easy part. The work is in replacing what sessions give you for free: instant logout, logging out everywhere when a password changes, and locking out a banned user. It is also in finding every feature that stores data in `request.session` for reasons other than login, and in moving logged-in users over without signing all 30k of them out at once. For server-rendered pages, the JWT has to live in an HttpOnly cookie, not in browser storage, so CSRF protection stays exactly as it is now.

**Cheaper path, if the goal is the React widget or an API:** keep sessions for everything. If the widget is served from your own domain, it can call Django with the session cookie plus the CSRF header. That is a few hours of work, and you lose nothing. If the goal is a mobile app or third-party API clients, add token auth (JWT or plain DRF tokens) for the `/api/` routes only, next to sessions. Either is the right choice unless something specifically needs stateless tokens on the server-rendered side, such as several services verifying the same login without calling Django. I plan what you asked below.

Not seen: your code, settings, auth flows or the widget's hosting. The plan rests on the defaults below.

## Questions I would ask

1. **What is driving the switch?** Default: a full switch, as asked. If it is the widget, or an API for other clients, take the cheaper path above. Phases 1 to 4 then shrink to a token endpoint for `/api/`.
2. **Is the React widget served from the same domain as the Django pages?** Default: yes. The cookie then works for it unchanged, with `SameSite=Lax`. If it runs on another domain, the cookie needs `SameSite=None; Secure`, plus CORS with credentials and a strict origin allowlist. That widens your CSRF exposure, which then needs a separate review.
3. **Must a logout, password change or ban take effect immediately?** Default: yes. Each request checks a `token_version` on the user, cached in Redis, so you still make one lookup per request. If waiting up to the access-token lifetime is acceptable, drop that check and the requests become truly stateless.
4. **Do you use social login, SSO, 2FA or impersonation?** Default: yes, at least one. Those flows keep a short-lived session for their own state (OAuth `state`, the half-finished 2FA step), so the session framework stays installed.

Answer first: 1 and 2. Question 1 can cancel most of this plan. Question 2 decides the cookie and CSRF design.

## Plan

The cutover is controlled by one setting, `AUTH_MODE` = `session` | `dual` | `jwt`. It is read at runtime (from an environment variable or a database-backed setting) so it can change without a deploy.

### Phase 0: Inventory

- Every use of `request.session`, `SessionMiddleware`, `login()` and `logout()`, `update_session_auth_hash`, and `SESSION_*` settings. Expect to find non-auth uses too: carts, wizards, flash messages (`django.contrib.messages` falls back to session storage), CSRF if `CSRF_USE_SESSIONS` is on, and third-party apps.
- For each non-auth use, decide whether it stays in the session framework or moves (to a cookie, the database, or the URL). Default: it stays. Login state moves to JWT; the session store keeps the other state.
- Current `SESSION_COOKIE_AGE`, which sets how long phase 3 must run. As I recall, Django's default is two weeks; read the real value from your settings.
- A baseline over the last 14 days: logins per day, the share of requests returning 401/403 or redirecting to login, and authenticated requests per minute.

Check: a list of every session use with its decision, and baseline numbers you can compare against later.

### Phase 1: Token issuing and verification (`AUTH_MODE=session`, so nothing changes for users)

- **Access token:** a JWT signed with HS256 and a dedicated key, not `SECRET_KEY`, with a `kid` header so the key can be rotated. Lifetime is a setting; the default is 10 minutes, which is a guess. Claims: `sub`, `exp`, `iat`, `jti`, `ver` (the user's `token_version`). Verification accepts exactly one algorithm.
- **Refresh token:** an opaque random value stored hashed in a `refresh_tokens` table (user, device or user agent, created, last used, expires). It is rotated on every use. If a token that was already used is presented again, its whole family is revoked. This table is the server-side state that remains, and it is what lets you list active devices and log one out.
- **Cookies:** `access` and `refresh`, both `HttpOnly; Secure; SameSite=Lax`, with `refresh` limited to `Path=/auth/refresh`. Django's CSRF middleware stays on.
- **Middleware** `JWTAuthenticationMiddleware`, placed where `AuthenticationMiddleware` sits now. It verifies the access token, checks `ver` against the cached `token_version`, and sets `request.user`. If the access token has expired but the refresh token is valid, it refreshes during the request and sets new cookies on the response, so page navigation never shows a 401. `login_required`, permissions and the admin keep working, because they only read `request.user`.
- Library: `djangorestframework-simplejwt` covers the token format, plus a blacklist app if you want it. I am recalling it from memory; check that its current release supports your Django version. The middleware for server-rendered pages is custom either way, because that library authenticates DRF views only.

Check: unit tests for expiry, a tampered token, the wrong algorithm, a refresh token reused after rotation, and a `token_version` bump rejecting an access token that has not yet expired.

### Phase 2: Revocation hooks

Bump `token_version` and revoke refresh tokens on: logout ("this device" revokes one family; "everywhere" revokes all), password change and reset, deactivation or ban, an admin "force logout", and any 2FA reset.

Check: one test per trigger. After the trigger, the next request with the old cookies is anonymous.

### Phase 3: Dual mode (`AUTH_MODE=dual`)

Both mechanisms are accepted. A request carrying a valid session but no JWT is authenticated by the session, and JWT cookies are set on the response. That moves active users across without asking them to log in again. New logins issue JWT cookies and still create the session, so falling back stays possible. Log the authentication method used on each request.

Enable it for staff first for two days, then for everyone. It runs for at least one full `SESSION_COOKIE_AGE`.

Revert rule: if the share of 401/403 responses and login redirects rises more than 20% above the phase 0 baseline, or support tickets about unexpected logouts appear, set `AUTH_MODE=session`. Sessions are still being written, so the fallback takes effect immediately.

### Phase 4: JWT only (`AUTH_MODE=jwt`)

Go / no-go, all true:

- Dual mode has run for at least one full `SESSION_COOKIE_AGE`.
- Session-authenticated requests are under 1% of authenticated traffic for 3 consecutive days.
- Every revocation trigger in phase 2 passes in staging against the production configuration.
- The widget works with the cookies in every supported browser, including Safari, which limits cookies most aggressively.

At the switch, the middleware stops reading login state from the session. Users still on a session only (people inactive since dual mode began) log in once. Logins stop creating auth sessions.

The limit of rollback: until phase 5, switching back to `dual` works, but only for users who logged in before the switch, because new logins no longer create sessions. Keep that window short.

### Phase 5: Cleanup, at least two weeks after phase 4

Remove session-based authentication code and the auth keys in the session store. Do not flush Redis wholesale, because the non-auth session data from phase 0 still lives there. Rotate the JWT signing key once, to prove that rotation by `kid` works.

## What you lose, and what replaces it

| Free with server-side sessions today | Replacement |
|---|---|
| Logout deletes the session and takes effect at once | Refresh token revoked plus a `token_version` check on each request |
| Password change logs out other devices (session auth hash) | `token_version` bump in phase 2 |
| Banning or force-logging-out a user from the admin | The same bump, exposed as an admin action |
| One opaque cookie with nothing readable in it | A JWT whose claims anyone can read: no e-mail, roles or other personal data in the claims |
| One secret to manage | A signing key with rotation, kept out of logs |
| A list of active sessions per user | The `refresh_tokens` table |

The `token_version` check also means you keep one cached lookup per request, as you have now. The gain is a smaller and simpler store, not a stateless one.

## Need from you

- The reason for the switch (question 1). It decides whether most of this plan is needed.
- Where the widget is hosted, and how it calls Django today.
- `settings.py` (middleware, `SESSION_*`, auth backends, installed apps) and a search of the code for `request.session`.
- Access to request logs or metrics, to build the phase 0 baseline.
