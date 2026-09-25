=========
Changelog
=========

All notable changes to **partner_autocomplete_ares_cz** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Added
~~~~~

- A browser tour that re-picks a (mocked) ARES suggestion on an existing company
  whose answer clears and recreates its contacts, and checks the old contact is
  gone after saving.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

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
