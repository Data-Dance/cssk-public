=========
Changelog
=========

All notable changes to **partner_autocomplete_orsf_sk** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.4.0] — 2026-10-03
-------------------------

Added
~~~~~

- **A DIČ-only backfill**, ``action_orsf_fill_missing_dic`` on ``res.partner``.
  Fills ``l10n_sk_dic`` where it is empty, from ``POST /lookup/batch``, and
  writes nothing else.

  Deliberately separate from ``action_orsf_bulk_refresh``, which rewrites
  identity wholesale — name, address, IČ DPH, status. That is right when you
  want the register's current view of a contact and wrong when you want one
  missing number added to a validated dataset: a migration build whose trial
  balance ties to its source should not have partner names rewritten as a side
  effect of needing a DIČ.

  It exists because the Slovak Peppol participant identifier is ``0245:<DIČ>``
  and ``l10n_sk_ubl_bis3`` deliberately never derives the DIČ from the VAT
  number, so every Slovak trading partner needs the number on file before it
  can be e-invoiced. On one real agenda that was 1204 partners, 1165 of them
  with an IČO to resolve from — about a dozen batch calls.

  Writes only into an empty field, so it is safe to re-run and never overrules a
  hand-entered value. Reports what it did split by reason: filled, not in the
  register, in the register but with no DIČ published, and no usable IČO.

[19.0.1.3.0] — 2026-09-29
-------------------------

Changed
~~~~~~~

- The register's NACE maps onto ``res.partner.nace_code`` (``partner_nace``) by
  default, re-applied on upgrade without overwriting a chosen mapping.

Added
~~~~~

- Declares **SK**, so a Slovak partner is looked up in ORSF from any company
  (``partner_autocomplete_dispatcher`` 19.0.1.1.0).

[19.0.1.1.0] — 2026-09-14
-------------------------

Fixed
~~~~~

- **The ORSF session was sent on every request**, not just where it is
  required. Once an account e-mail and password were configured for the
  ownership graph, ``_orsf_probe`` and the two POSTs (``/lookup/batch``,
  ``/refresh``) all carried ``__Secure-orsf.session_token``. ORSF's published
  per-minute limits for signed-in tiers are lower than anonymous — FREE 60/min,
  PRO 300/min against a measured 600/min on anonymous ``/lookup`` — so one gated
  feature could quietly move a database's whole type-ahead onto the account,
  and a lapsed cache made a keystroke trigger a sign-in. ``_orsf_get`` and
  ``_orsf_probe`` now take ``authenticated=False`` by default; only
  ``authenticated=True`` presents the session, an anonymous 401 no longer
  signs in, and an authenticated call with no obtainable session returns
  ``unavailable`` without making the request. Whether ORSF applies the
  account tier to a request that merely carries a session is unverified —
  the fix is right either way.
- ``authenticated`` and ``_retried`` are **keyword-only** on both methods.
  ``authenticated`` was inserted ahead of ``_retried``, so an inheriting module
  calling ``_orsf_probe(path, params, True)`` in the old meaning would have
  silently asked for a session instead — raised in review by GPT-5.3-Codex.
  No caller in this repository passes either positionally.

[19.0.1.0.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- Slovak catalogue completed. Terms already stated in Slovak in the source are
  deliberately left untranslated — the source IS the translation, per the
  hybrid convention for these modules — so an empty ``msgstr`` there is correct
  rather than missing.

Changed
~~~~~~~

- **Field mapping trimmed from thirteen selectors to four.** IČO, DIČ, the
  register coordinates, status, dissolution date and the VAT paragraph are all
  written into real fields now, so offering a mapping for them was busywork
  whose only prize was a second, silently divergent copy of the same value.
  What is left is what genuinely has no field of its own: **SK NACE, právna
  forma, veľkostná kategória, dátum vzniku**.

Added
~~~~~

- **Bulk identity refresh** (*Contacts ▸ Action ▸ Refresh identity from ORSF*)
  over ``POST /lookup/batch``: 100 IČOs a call, 60 calls a minute. 86 partners
  refresh in one call, in about a third of a second, where the dispatcher's
  *Update* would have needed three minutes of rate-limit waiting and silently
  returned nothing past the first twenty.

  It carries **identity only** — name, address, IČ DPH, DIČ, status — because
  that endpoint carries nothing more: no ``vatRegistration``, no register
  office or číslo zápisu, no activities, filings or history. It therefore
  **never clears** a list it did not fetch; a bulk run over a partner enriched
  from the full record leaves that partner's deeper data intact, which is
  pinned by a test and verified live.

- Uses ``GET /lookup/{ico}`` for the type-ahead dropdown and for confirming a
  VAT lookup. It carries exactly the identity fields the dropdown needs, at
  ~1 KB against the full record's ~100 KB, and is rate-limited at **600
  requests/minute where ``/companies/{ico}`` allows 30**. Enrichment still
  reads the full record, which is the only place the register coordinates and
  the VAT-registration paragraph appear.
- Optional **Bearer token** (``orsf_sk.api_token``) raising the quota and
  unlocking a sole trader's full address.
- **ORSF account sign-in** for the gated person and graph endpoints:
  ``orsf_sk.login_email`` / ``orsf_sk.login_password``. The provider exchanges
  them for a *better-auth* session cookie, caches it, and signs in again
  automatically when a gated call answers 401.

  This is deliberately a password and not a token, because ORSF has no token to
  give: the only security scheme in its OpenAPI document is ``sessionCookie``,
  it never displays that cookie, and the cookie is HttpOnly and expires. The
  alternative was an administrator copying it out of DevTools and re-copying it
  whenever it lapsed, which is not a deployment.

  **The password sits in ``ir.config_parameter``, which is plain text in the
  database and in every backup.** Use a dedicated ORSF account, never a
  personal one. It is never logged, and a rejected sign-in logs the status code
  without echoing the response body.
- Fills ``l10n_cssk_core``'s **DIČ** natively, rather than only through a
  mapping pointed at it.
- Fills ``l10n_sk_vat_registration``'s § 4 / § 7 / § 7a category and
  ``l10n_sk_trade_registry``'s register coordinates, **register status,
  dissolution date and check timestamp** when those modules are
  installed, by feature detection rather than a manifest dependency — the same
  move ``partner_autocomplete`` makes for ``base_address_extended``.

Notes
~~~~~

- **Enrichment reads ``/companies/{ico}``, which allows 30 requests a minute.**
  Refreshing a partner base by looping it exhausts that in about twenty
  contacts, after which the provider correctly returns nothing and looks like
  a mapping bug. Bulk work belongs on ``POST /lookup/batch`` — 100 IČOs a call,
  against the 600/min ``/lookup`` budget.
- Unlike the other register values, the **status is written even when it is
  False**. "The register no longer answers for this subject" has to be able to
  replace a stale "aktívna", or storing it achieves nothing.
- **ORSF carries no bank accounts.** Neither the OpenAPI document nor a full
  company record mentions one. For SK bank accounts the source is the Finančná
  správa's published-accounts list, which ``l10n_sk_payment_reliability``
  already reads; Finstat also sells them.
- ORSF's published documentation page understates the API. The OpenAPI
  document at ``/v1/openapi.json`` is **readable anonymously** and describes
  ``/lookup/{ico}``, ``POST /lookup/batch`` (100 IČOs a call), ``GET /companies``
  and ``GET /tiers``, none of which the docs page mentions — and contradicts it
  on tokens, which it says do not exist. Where the two disagree, the spec and
  the live response headers have been right.

[19.0.1.0.0] — 2026-09-04
-------------------------

Added
~~~~~

- ORSF (https://orsf.sk) partner-autocomplete provider, registered into the
  ``partner_autocomplete_dispatcher`` registry as
  ``partner.autocomplete.provider.orsf_sk`` ("ORSF.SK"). ORSF aggregates RPO,
  ORSR, ŽRSR, RÚZ and the Finančná správa VAT-payer list, and the endpoints
  used here need no API key.
- Completes SK partner details — name, address, PSČ, IČ DPH, IČO and company
  type — with a configurable dynamic field mapping for DIČ, SK NACE, právna
  forma, register / číslo zápisu / registrový súd, stav subjektu, veľkostná
  kategória, dátum vzniku a zániku, druh registrácie DPH (§) and platiteľ DPH od.
- Lookup by name (fulltext), by IČO (direct register read) and by IČ DPH
  (ORSF's exact DIČ index, falling back to an exact match over the fulltext
  index — the fuzzy index answers a VAT query with lexical neighbours).
- The register's status word rides in the dropdown label for any subject that
  is not active, so a *zrušená* IČO is not picked by accident.
- Configuration surfaced in Settings (``views/res_config_settings_views.xml``),
  including the CC-BY 4.0 attribution ORSF's licence requires. The three
  behaviour switches (fill Company ID, set company type, format PSČ) live on
  ``res.company``, alongside the dispatcher's own provider selection.

Notes
~~~~~

- ``vat`` is written **only while the register shows a live VAT registration**.
  ORSF retains the historical ``vatRegistration`` row after a deregistration
  but clears ``icdph``/``vatId``; writing the lapsed IČ DPH onto an invoice is
  what makes VIES reject it.
- Unlike ``partner_autocomplete_ares_cz``, every request carries a timeout, a
  429 or an outage degrades to "no suggestions" rather than a traceback, and
  nothing is written into ``website``.
- The dynamic mapping declares each value's kind (``char`` / ``date``)
  explicitly instead of inferring it from a ``_date`` suffix on the config
  parameter name, so a parameter can be renamed without silently changing how
  its value is parsed.
- A VAT lookup confirms the DIČ-index hit against the company record before
  offering it. Holding a DIČ is not holding an IČ DPH, and ORSF's ``mode: dic``
  hits report ``icDph: null`` even for a live payer — so the hit alone cannot
  answer "who holds this VAT number".
- The behaviour switches are ``res.company`` fields rather than
  ``config_parameter`` Booleans on purpose: ``set_param`` *unlinks* the row for
  a falsy value and ``res.config.settings`` reads an absent key back through
  the field default, so a default-True ``config_parameter`` Boolean cannot be
  switched off at all.
