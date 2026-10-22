=========
Changelog
=========

All notable changes to **partner_autocomplete_ares_cz** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[18.0.2.0.0] — 2026-09-16
-------------------------

Added
~~~~~

- Tests for how core 18.0's partner autocomplete reaches ARES through the
  dispatcher — suggestions, the ``enrich_by_duns`` pick, an empty answer — and a
  browser tour that picks an ARES suggestion on a new company and checks the
  saved partner.
- A browser tour that re-picks a (mocked) ARES suggestion on an existing company
  whose answer clears and recreates its contacts, and checks the old contact is
  gone after saving.

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- ARES (Administrativní registr ekonomických subjektů, MFČR) partner-autocomplete
  provider, registered into the ``partner_autocomplete_dispatcher`` registry as
  ``partner.autocomplete.provider.ares_cz`` ("ARES.CZ").
- Completes CZ partner details (name, address, IČO/DIČ) from the ARES REST service
  with a configurable dynamic field mapping.
- Configuration surfaced in Settings (``views/res_config_settings_views.xml``).
