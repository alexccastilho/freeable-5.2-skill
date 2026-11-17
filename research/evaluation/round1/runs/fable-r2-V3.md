Before planning a full switch, I'd question it: for a Django monolith that renders its own pages, replacing sessions with JWT across the board costs a lot and gains little. I recommend adding JWT for the React widget's API calls and keeping sessions for the server-rendered pages. The plan below assumes that; a full replacement is outlined after it in case that is what you need.

## Why not a full switch

- **You still need server state.** Logout, "sign out everywhere", banning a user and password changes all require revoking tokens, which means a revocation list or refresh-token store, most likely in Redis. The session store does not go away; it changes shape.
- **Django leans on sessions.** The admin, `login_required`, the messages framework, CSRF handling and anything in `request.session` (carts, multi-step forms) all assume them.
- **Security does not improve by default.** A JWT in `localStorage` is readable by any script injected into the page. A JWT in an httpOnly cookie is as safe as the session cookie is today and still needs CSRF protection.
- **Scale is not a reason.** 30k users is a small load for Redis sessions.

JWT does earn its place when something other than the monolith's own pages has to authenticate: a widget on another origin, a mobile app, or another service that must verify users without calling Django.

## Questions I would ask

1. **What is driving this?** Default assumed: the React widget, or future API clients, need token auth. If the driver is instead removing Redis, or single sign-on across several services, the plan changes.
2. **Is the widget served from the same origin as the Django pages?** Default assumed: yes. If it is embedded on other sites, the token delivery in step 2 changes and CORS rules are needed.
3. **Does the widget's API use Django REST Framework?** Default assumed: yes, so `djangorestframework-simplejwt` fits. If not, I'd use PyJWT with a small auth class.
4. **Will any other service verify the tokens?** Default assumed: no, so a symmetric key (HS256) is enough. If yes, use an asymmetric key (RS256 or EdDSA) so other services can verify without being able to issue.
5. **Can users be forced to log in again at cut-over?** Default assumed: no.

## Recommended plan: JWT for the API, sessions for the pages

**1. Token issuing.** Add SimpleJWT with a 10-minute access token and its own signing key, separate from `SECRET_KEY`, so it can be rotated independently.

**2. Getting a token to the widget.** A session-authenticated endpoint, `POST /api/token/`, returns a short-lived access token. The widget keeps it in memory, not `localStorage`, and asks again when it expires. No refresh token is needed, because the session plays that role; logging out or being deactivated stops new tokens within 10 minutes.

**3. API authentication.** Set the widget's API views to accept JWT. Keep session auth accepted alongside it during the rollout, then remove it from those views.

**4. Rollout.** Ship the endpoint and dual auth first, then the widget change, then drop session auth on the API once logs show no session-authenticated API calls. No user is logged out at any point, and each step can be reverted on its own.

**5. Tests.**
- Token is refused when expired, tampered with, or signed with the wrong key.
- The token endpoint refuses anonymous requests.
- A deactivated user cannot get a new token.
- The widget recovers from an expired token without the user noticing.

This is roughly a few days of work and touches only the API layer.

## If you do want a full replacement

The outline, so you can judge the cost:

- **Token storage:** access token (about 15 minutes) and rotating refresh token (about 14 days) in httpOnly, Secure, SameSite=Lax cookies. CSRF protection stays.
- **Middleware:** replace `SessionMiddleware`/`AuthenticationMiddleware` behaviour with one that sets `request.user` from the token and refreshes it transparently.
- **Revocation:** a refresh-token store in Redis, plus a per-user token version that changes on password change or "sign out everywhere".
- **Audit of `request.session`:** every use that is not login state needs a new home, for example signed-cookie sessions.
- **Django admin:** either keep sessions for `/admin/` only or make it work on the new middleware.
- **Migration:** accept both for one full session lifetime (`SESSION_COOKIE_AGE`, two weeks by default). Issue tokens at login and to any request that arrives with a valid session, so nobody is logged out. Remove session auth after that window, behind a flag for rollback.
- **Key handling:** key ids in the token header so signing keys can be rotated without logging everyone out.

I'd estimate this at several weeks including the audit, and the auth middleware becomes code you own and have to keep secure.

## What I need from the repo

- Where `request.session` is used beyond login.
- How the widget authenticates today, and its origin.
- Whether DRF is installed.
- Session settings: cookie age, and whether sessions are extended on each request.
