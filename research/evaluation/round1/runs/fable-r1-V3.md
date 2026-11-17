Before planning a full switch, I would want to know what problem it is meant to solve. For a Django monolith with server-rendered pages, replacing sessions with JWT usually costs more than it gains. My default plan is narrower: keep sessions for the pages and add JWT only where a token is needed.

## Why a full switch is a poor fit here

- **Server-rendered pages still need a cookie.** The browser has to send something on every page load. A JWT in a cookie is a session cookie with more moving parts.
- **You lose instant revocation.** Today, logout, password change, or banning a user takes effect immediately by deleting the session. A JWT stays valid until it expires unless you keep a server-side denylist, which puts you back on Redis.
- **Django is built around sessions.** The admin, `login_required`, the messages framework, CSRF handling, and most third-party packages assume `django.contrib.sessions`. Replacing it means custom middleware and re-testing all of them.
- **Scale is not the reason.** A Redis session store handles 30k users with ease.

## Questions I would ask

1. **What is driving this?** A mobile app, third-party API clients, the widget moving to another domain, separate services needing to verify users, or Redis problems? Default: the React widget, or a future client, needs token auth for the API.
2. **Is the React widget served from the same origin as the Django pages?** Default: yes. In that case it can already use the session cookie plus the CSRF token and needs no change.
3. **Does the API use Django REST Framework?** Default: yes.
4. **How fast must logout or a ban take effect?** Default: within 5 minutes is acceptable for API tokens; immediately for the web pages.
5. **May users be forced to log in again at cutover?** Default: no.

## Default plan: sessions for pages, JWT for the API

1. **Leave the pages and admin alone.** Session auth and the Redis store stay as they are.
2. **Add token auth to the API** with `djangorestframework-simplejwt`:
   - access tokens that live 5 minutes;
   - refresh tokens that rotate on use, with the old one denylisted;
   - a signing key separate from `SECRET_KEY`.
3. **Accept both on API views.** Set the authentication classes to session first, then JWT. Existing callers keep working and new clients use tokens.
4. **Token endpoints:** obtain, refresh, and revoke. Logout, password change, and deactivation revoke that user's refresh tokens.
5. **Widget:** if it is same-origin, leave it on the session cookie. If it is or will be cross-origin, it keeps the access token in memory and the refresh token in an `HttpOnly`, `Secure`, `SameSite` cookie. Neither goes in `localStorage`, where any injected script could read it. CORS is limited to the widget's origin.
6. **Tests:** token expiry, refresh rotation, reuse of a rotated refresh token, revocation on logout and password change, and both auth methods on the same API view.

Nobody is logged out, there is no cutover, and rollback means removing one authentication class.

## If you do want sessions gone entirely

This is a much larger change, and I would only take it on with a clear reason from question 1. In outline:

1. **Custom auth middleware** that reads a JWT from an `HttpOnly` cookie and sets `request.user`, replacing `SessionMiddleware` and `AuthenticationMiddleware`.
2. **Replacements for what sessions gave you:** CSRF protection for cookie-borne tokens, cookie-based message storage, and anything of yours stored in `request.session` (cart, wizard state, and the like). That last item needs an inventory of the codebase first.
3. **The admin:** it either keeps sessions, so they aren't really gone, or gets its own adapter.
4. **Revocation:** a denylist or a per-user token version checked on every request. That is a Redis lookup per request, the same cost as today.
5. **Migration without mass logout:** run both for at least the session lifetime. The middleware accepts either; a request with a valid session and no token is issued a token. Sessions are removed only after the dual period, behind a flag that can be turned back.
6. **Key management:** a rotation procedure and a plan for a leaked signing key, which would otherwise let an attacker mint a token for any user.

Tell me what is behind the request and I can make either plan specific to your code.
