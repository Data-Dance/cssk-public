=========
Changelog
=========

All notable changes to **partner_autocomplete_dispatcher** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Added
~~~~~

- **Dispatch by the partner's country.** A provider declares the countries
  whose register it reads (``_autocomplete_country_codes``); a search for a
  partner in one of them goes there whatever the company's own provider is,
  and anything else still goes to the company's choice. The country comes
  from the search's ``query_country_id``, else the VAT prefix. Each suggestion
  is stamped with the provider that produced it, and ``enrich_by_duns`` goes
  back to that provider: a Czech and a Slovak IČO are both eight digits. With
  two companies in two countries sharing contacts, neither could autocomplete
  a partner from the other country before.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- **Country dispatch (19.0.1.1.0, 2026-09-27).** 18.0 still dispatches by the
  company's provider only. 18.0 is what DURWEN runs, so port with its upgrade
  rehearsal (see the 18.0.2.0.0 notes) rather than straight to production.

Fixed
~~~~~

- **A CLEAR from a provider now reaches the server.** The CLEAR patch emptied
  the list's ``records``, ``_currentIds`` and ``_commands`` directly, but a
  ``StaticList`` only sends what ``_commands`` holds — so the old rows vanished
  from the form and were still attached after saving. Re-picking a suggestion
  on an existing company whose answer replaces a one2many
  (``partner_autocomplete_orsf_sk`` does so for its activity, filing and history
  mirrors) appended the new rows to the old ones. CLEAR is now rewritten into
  UNLINK for saved rows and DELETE for unsaved ones, which core records and
  sends.
- **Saving a new company no longer looks it up in the register.** The
  ``import_enrich_company`` inverse runs on every create, because the field's
  default puts it into the values, so the ``company_registry`` fallback below
  turned every company saved with an IČO into a lookup: overwriting the name
  and address just typed, or warning about a lookup nobody asked for. Only
  records that actually carry an import value are enriched now.
- **The *Update* action did nothing for most partners.** It looked the partner
  up by ``partner_gid``, which is only ever set on a record that came in
  through the autocomplete dropdown. A partner that was imported or typed by
  hand carries its registry number in ``company_registry`` and nothing else —
  and for these providers that number *is* the key the register is searched by.
  In one real database, 86 partners had an IČO and only 40 had a
  ``partner_gid``, so the action silently enriched none of the other 46.
  It now falls back to ``company_registry``.
- Removed a stray ``print(e)`` in the same handler, which is why those failures
  went to stdout instead of the log.
- **The action now reports what it did** — updated / no data returned / failed.
  Every provider here reads a rate-limited register, so a large selection stops
  returning data partway through; without a count that is indistinguishable
  from those partners simply not being in the register.
- **The one2many patch converted values the wrong way, and raced.** The date
  and datetime conversion inside x2many command payloads was doing the reverse
  of what the framework wants. A command's values dict is handed to
  ``StaticList._createRecordDatapoint``, which builds a ``Record`` from it and
  **does** run ``_parseServerValues`` — so server-format strings are what it
  expects, and those are what the provider already sends. The conversion also
  wrote to ``command[i][subfield]`` instead of ``command[i][2][subfield]``,
  setting properties on the command array itself while reading ``undefined``,
  and ran inside an ``async`` callback passed to ``Array.forEach``, which is
  never awaited — so its work could land after ``record.update()`` had already
  run. The block is gone; the payloads are passed through untouched.
- **The top-level date conversion is kept, and now guarded.** That direction is
  genuinely needed — ``record.update()`` reaches ``_applyChanges()``, which
  writes values into ``record.data`` verbatim without parsing, so a date has to
  arrive as a luxon object. It now skips unknown fields and empty values, where
  ``deserializeDate(false)`` used to throw.
- **``StaticList._applyCommands`` is no longer a stale fork of core.** It was a
  whole copy of core's method with a CLEAR branch bolted on, and it had drifted:
  it lost core's LINK de-duplication against ``_currentIds`` (duplicate rows),
  still called ``_parseServerValues(changes, record.data)`` after core moved the
  second argument to an options object (so current values were dropped), and
  pinned an older ``_currentIds.splice`` index. Replaced with a patch that
  handles only CLEAR — the one command core genuinely does not implement, and
  the one a provider needs to replace a partner's bank accounts — and delegates
  everything else to ``super``. The unused ``reload`` option is gone.
- **Autocomplete never filled Country, State or Industry.** The JS patch
  rewrote many2one values from the provider's ``{id, display_name}`` into the
  pre-17.0 ``[id, display_name]`` pair before handing them to
  ``record.update()``. In 17.0+ every many2one goes through
  ``Record._completeMany2OneValue``, which reads ``.id`` and ``.display_name``
  off the value — an array has neither, so it returns ``false`` and the field
  is cleared. Those three fields were exactly the ones the patch touched, which
  is why every scalar beside them filled in correctly and the failure looked
  like a provider bug. Core 19.0 passes the object through untouched; so do we
  now.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.0.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Technical dispatcher framework for partner-autocomplete providers: abstract
  ``partner.autocomplete.provider.registry`` and ``partner.autocomplete.provider``
  models with ``read_by_vat`` / ``enrich_company`` / ``autocomplete`` extension hooks
  for concrete providers (e.g. ARES CZ) to register against.
- Lets the active autocomplete provider be assigned per company, so multi-company
  databases route lookups to the appropriate national registry.
- Config-settings, company, and partner view/JS integration wiring the dispatcher
  into the standard ``partner_autocomplete`` UI.
