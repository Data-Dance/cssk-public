# partner_autocomplete_orsf_sk_related_parties: developer notes

Not user documentation: this file is not rendered into a page.

## Authentication

ORSF issues **no API key** for persons and graphs; the only scheme its OpenAPI
document defines for them is a *better-auth* session cookie
(`__Secure-orsf.session_token`, HttpOnly, never displayed). So the provider
signs in for you:

`partner_autocomplete_orsf_sk` then posts those to
`https://orsf.sk/api/auth/sign-in/email` when a session is needed, caches the
token for 12 hours, and on a 401 signs in once more and retries once. The
password is never logged, and a refused sign-in logs only the status code.

**Why the session goes nowhere else.** Anonymous `/lookup` measures
600 requests a minute per IP. ORSF's published tiers are slower per minute —
FREE 60, PRO 300; only TEAM reaches 600 (pricing page, read 2026-09-06). If the
session rode along on every request, configuring this module could move a
database's whole type-ahead onto the account's lower limit, and trigger a
sign-in on a keystroke whenever the cached session had lapsed. So only
`_orsf_get(..., authenticated=True)` carries it, and an anonymous 401 never
triggers a sign-in. Whether ORSF actually applies the account tier to a request
that merely carries a session is **not verified**; the code does not rely on the
answer either way.
