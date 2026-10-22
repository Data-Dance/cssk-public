=========
Changelog
=========

All notable changes to **partner_autocomplete_dispatcher** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[18.0.2.0.0] — 2026-09-16
-------------------------

Fixed
~~~~~

- **The JS patch never ran on 18.0.** It patched
  ``onSelectPartnerAutocompleteOption``, 19.0's name for the handler; 18.0 still
  calls ``onSelect``. ``patch()`` adds an unknown method without complaint, so
  core's handler did all the work and the date handling below never happened.
  The patch no longer copies the handler at all: it wraps only
  ``getCreateData``, and core 18.0's ``onSelect`` does the rest — including the
  ``[id, display_name]`` many2one pairs 18.0 still expects (19.0 moved to
  objects; that part of the 19.0 fix does not apply here).
- **Top-level date fields from a register now reach the form**, deserialized to
  luxon objects and skipping unknown fields and empty values, where
  ``deserializeDate(false)`` throws. x2many command payloads are left in server
  format, which is what ``StaticList`` parses them from.
- **A register that answers nothing is reported.** ``enrich_by_duns`` returned
  ``{}``, which core's JS treats as a successful enrichment: nothing was filled,
  nothing was said, and an empty Dun & Bradstreet card was posted to the
  chatter. It now returns an error, so core notifies the user and falls back to
  the suggestion's own values.
- **No Dun & Bradstreet chatter card for a register answer.** Core posts one
  after every successful pick; its fields (entity type, UNSPSC codes, …) are
  D&B's and no register returns them. Register answers now carry
  ``partner_autocomplete_provider``, which the JS uses to suppress it.
- **No blank row in the dropdown.** A provider with nothing to suggest may
  answer ``[{}]`` — ARES always does for a DIČ search — and core rendered it.
- **Saving a new company no longer looks it up in the register.** The
  ``import_enrich_company`` inverse runs on every create, because the field's
  default puts it into the values, so the fallback below would have turned every
  company saved with an IČO into a lookup: overwriting the name and address just
  typed, or warning about a lookup nobody asked for. Only records that actually
  carry an import value are enriched now. (19.0 has the same defect.)
- **The *Update* action looks a partner up by its own registry number**, falling
  back to ``company_registry`` for a company or a partner without a parent, and
  reports updated / skipped / no data / failed. Backported from 19.0, as is the
  removal of a stray ``print(e)``.
- **A CLEAR from a provider now reaches the server.** The CLEAR patch emptied
  the list's ``records``, ``_currentIds`` and ``_commands`` directly, but a
  ``StaticList`` only sends what ``_commands`` holds — so the old rows vanished
  from the form and were still attached after saving. CLEAR is now rewritten
  into UNLINK for saved rows and DELETE for unsaved ones, which core records and
  sends. Backported from 19.0.
- **``StaticList._applyCommands`` is no longer a copy of core.** It handles only
  CLEAR, which core does not implement, and delegates everything else. The copy
  had already drifted from 18.0 core (the index CREATEd rows were spliced in at).
  Backported from 19.0.

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
