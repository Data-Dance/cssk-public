=========
Changelog
=========

All notable changes to **partner_autocomplete_orsf_sk_related_parties** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.2.0.0] — 2026-09-14
-------------------------

Changed
~~~~~~~

- **Renamed from** ``l10n_sk_related_parties``. The module does nothing without
  ORSF — it calls one ORSF endpoint through ``partner_autocomplete_orsf_sk``'s
  transport and session — so it belongs in that family, not among the
  provider-neutral ``l10n_sk_*`` modules. Technical names follow the parent's
  ``orsf_sk_`` prefix: model ``orsf.sk.related.party``, fields
  ``orsf_sk_related_party_ids`` / ``orsf_sk_related_party_count`` /
  ``orsf_sk_related_parties_fetched_at``, methods
  ``action_orsf_sk_fetch_related_parties`` and ``_orsf_sk_parse_graph``.
  **No migration is shipped**: the only database that had the old module
  installed was a demo. Fetched rows are re-fetchable, so a database that has it
  should uninstall ``l10n_sk_related_parties`` and install this one.

Fixed
~~~~~

- The graph request now asks for the session explicitly
  (``authenticated=True``). Before, the provider attached the session to
  **every** ORSF request once credentials were set, so enabling this module
  signed in the whole database's type-ahead — see ``partner_autocomplete_orsf_sk``
  19.0.1.1.0.
- The description said "No password … nothing in this stack asks for, stores or
  transmits an ORSF password", and told administrators to paste a cookie out of
  DevTools. Both stopped being true when the provider moved to e-mail + password
  sign-in. The README now describes what actually happens, including that the
  password is plain text in ``ir.config_parameter``.

[19.0.1.0.2] — 2026-09-13
-------------------------

Fixed
~~~~~

- Gave the technical computed field an explicit ``string=``. Without one Odoo
  derives a label from the field name and exports it — "L10N Sk Jcd Is Sk
  Company" and the like — which is not English in any useful sense and cannot
  be translated into anything better. The field is a view modifier behind
  ``invisible="1"``, so no user reads it; the point is that it stops putting a
  mangled msgid in the catalogue.

[19.0.1.0.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- Slovak catalogue completed. Terms already stated in Slovak in the source are
  deliberately left untranslated — the source IS the translation, per the
  hybrid convention for these modules — so an empty ``msgstr`` there is correct
  rather than missing.

Known gaps
~~~~~~~~~~

- **Not deployable to end users as it stands.** ORSF issues no API key for
  ``/persons`` and ``/graph``; the only auth is a better-auth session cookie
  that the site never displays, that is HttpOnly (so unreadable from the page),
  and that expires with no documented lifetime. Obtaining it means opening
  DevTools and copying ``__Secure-orsf.session_token`` by hand, and re-doing it
  when it lapses. Usable by a consultant on databases they administer; not
  something to hand a customer. The unblock is an API-key tier from ORSF — they
  already run paid tiers, so it is a reasonable ask.

- **The graph response shape is unverified against live ORSF output.** The
  OpenAPI spec gives no schema for the body and the endpoint is gated, so there
  was no anonymous sample to build against. Confirm ``_orsf_sk_parse_graph``
  against a real signed-in response before relying on the rows.

[19.0.1.0.0] — 2026-09-05
-------------------------

Added
~~~~~

- ``orsf.sk.related.party`` — one row per edge of the ownership / officer graph
  touching a partner, keeping the counterpart's IČO and name whether or not it
  exists as a contact, and linking it where it does.
- A **Related parties (SK)** tab on the contact with a per-partner *Fetch from
  register* action, backed by ORSF's ``/companies/{ico}/graph``.
- A parser accepting both graphology serialisations (``key``/``id``, nested or
  flattened ``attributes``), which skips anything unrecognised rather than
  guessing.

Notes
~~~~~

- **No bulk fetching, by design.** ORSF gates the graph and person endpoints
  citing GDPR Art. 6(1)(f) with the instruction "never bulk-fetch persons".
  There is no cron and no batch action; the ``ensure_one`` in the action is
  what keeps the button off a list selection.
- **No password anywhere.** The gate is a better-auth *session cookie*, pasted
  as ``orsf_sk.session_token``. It expires on its own and is not an account
  credential.
- Register kinship is not the § 17 ods. 5 test, which is wider than a shared
  officer. The rows are a shortlist for an accountant, not a conclusion.
