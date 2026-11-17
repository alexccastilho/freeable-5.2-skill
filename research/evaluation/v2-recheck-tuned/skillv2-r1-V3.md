By default I'm planning **not** to replace sessions. Instead I'd keep server-side sessions for the server-rendered pages and get the React widget authenticating cleanly with the session it already has. If something really needs a token, I'd add JWT for the API only, alongside sessions. Replacing sessions everywhere would take weeks. It would also give up something the app depends on today: you can revoke a login instantly with one Redis delete (logout, password change, a disabled account, "log out everywhere"). With JWT, revocation has to be rebuilt, and the rebuilt version needs a server-side lookup again. For a monolith that renders its own pages, 30k users and a Redis store are no load at all, so scale isn't a reason to switch. Most of the effort is in two places: whatever the widget actually needs, and every piece of code that reads `request.session` for something other than login. I haven't seen the code, so this plan rests on the defaults below. Full replacement is still possible, as the branch at the end. You'd pick it by answering Q1 with an outside mandate (SSO/OIDC, a security policy) or with clients that can't hold a cookie for this domain.

## Questions I would ask

**Q1. What's driving this?** Default: the React widget needs to call the backend, and the session cookie can do that.
- If a mobile app, a third-party integration or another domain needs to call the API: step 3 adds JWT for `/api/` only, and pages stay on sessions.
- If the reason is Redis cost or running it: change `SESSION_ENGINE` (cached_db or signed cookies). No JWT needed.
- If it's a mandate (SSO, policy): the full-replacement branch applies.

**Q2. When someone logs out, changes their password or is disabled, how quickly must their access stop?** Default: immediately, as it does today. So any JWT gets an access lifetime of 5 minutes or less, plus a refresh token that is stored and revoked on the server. If 15 to 60 minutes of lingering access is acceptable, token handling gets simpler.

**Q3. Is the widget served on the same site as the Django pages?** Default: yes, it's embedded in your own pages. If it's embedded on other sites or domains, `SameSite` cookies won't reach it, and that is a real case for a token (step 3).

**Q4. Does the session hold anything besides the login (cart, multi-step forms, impersonation, `messages`)?** Default: yes, some of it does. This only matters for the full-replacement branch, where each of those needs a new home.

**Q5. Can I see the repository, and who will do the work?** Default: I have no access yet. Step 1 is read-only so that anyone can run it.

Answer first: **Q1 and Q3**. Between them they decide whether this is a few days of widget work or a multi-week change of architecture.

## Plan

**Step 1. Inventory (read-only, about a day).**
- Find how the widget authenticates today and what exactly fails or feels awkward.
- List the API endpoints it calls.
- List the DRF `DEFAULT_AUTHENTICATION_CLASSES`, the `AUTHENTICATION_BACKENDS` and the session cookie settings.
- Find every use of `request.session`, `login()`, `logout()` and `update_session_auth_hash`.

Check: a written list of the widget's calls and of what is stored in the session. This list answers Q3 and Q4 without anyone having to.

**Step 2. Widget on session auth (default path, a few days).**
- The API views use DRF `SessionAuthentication`.
- The widget sends `fetch(..., {credentials: 'same-origin'})` and sends the CSRF token in the `X-CSRFToken` header on unsafe methods, read from the `csrftoken` cookie or from a value rendered into the page.
- Cookies: `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY`, `SameSite=Lax`.

Failure modes:
- *Session expires while the widget is open:* the API returns 403 and the widget shows "Your session expired, reload" instead of failing silently.
- *CSRF token rotates at login:* the widget reads it per request, not once at load.
- *Several tabs:* they share one session, so there's no conflict.
- *Redis down:* logins and pages already fail today. Same exposure, nothing new.
- *Unknown caller:* any client that isn't a browser on your domain is refused (403). The 403s are logged per endpoint for a week, which shows whether anything like that exists (that would answer Q1 with evidence).

Verification:
- Tests: anonymous gets 403; logged in with CSRF gets 200; a POST without CSRF gets 403; after logout, the widget's next call gets 403.

**Step 3. JWT for the API only (if Q1 or Q3 calls for it).** Pages keep sessions.
- Issue tokens with `djangorestframework-simplejwt`.
- Access lifetime 5 minutes. Refresh lifetime 7 days, rotated, with the blacklist app turned on.
- Logout, password change and deactivation revoke the user's refresh tokens.
- Use a signing key separate from `SECRET_KEY`, with a documented way to rotate it.
- For a browser widget, keep the refresh token in an HttpOnly cookie, never in `localStorage` (XSS exposure).
- The setting names (`ACCESS_TOKEN_LIFETIME`, `ROTATE_REFRESH_TOKENS`, `BLACKLIST_AFTER_ROTATION`) are from memory. I'd check them against the installed version.

Failure modes:
- *Two tabs refresh at the same moment with rotation on:* the second uses a refresh token that's already blacklisted, and the user gets logged out. The widget serialises refreshes, with one in-flight refresh shared across tabs.
- *Clock skew:* allow a few seconds of leeway.
- *Stolen access token:* it stays valid for up to 5 minutes. State this as accepted under Q2.
- *Blacklist grows without limit:* simplejwt's `flushexpiredtokens` runs daily.

Rollout: turned on by a setting for the token endpoints only. Session auth keeps working throughout, so turning the setting off reverts the change.

Revert rule: if the token endpoints raise the API's 401/403 rate above the session-only baseline for a day, turn the setting off.

## Branch: full replacement (if Q1 selects it)

1. Build middleware that reads a JWT from an HttpOnly cookie and sets `request.user` on every view. CSRF protection stays, because cookies are still sent automatically.
2. Rebuild revocation as a per-user `token_version` checked on every request. That is a lookup per request again, likely in Redis.
3. Move every non-login use of `request.session` (Q4) to the database or the client.
4. Bridge period of about 2 weeks: the middleware accepts either credential and swaps a valid session for a JWT, so the 30k users aren't all logged out at once.
5. Remove session auth only after a week with no session-only logins, and make sure Django admin is covered.

Largest cost: steps 2 and 3. The step you can't simply undo is retiring the session store.
