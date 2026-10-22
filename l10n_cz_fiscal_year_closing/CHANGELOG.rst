=========
Changelog
=========

All notable changes to **l10n_cz_fiscal_year_closing** are documented here.
Versioning follows the Odoo manifest (``18.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- **Renamed from ``l10n_cz_zavierka``**, as on 19.0 (2026-09-30). *Závierka*
  is Slovak (the Czech word is *závěrka*), and the technical name is now
  English like most of the repository. No migration is shipped, because the
  module was not yet installed in production. A development database that
  had it installed keeps an orphaned ``l10n_cz_zavierka`` row. Install
  ``l10n_cz_fiscal_year_closing`` there.

[18.0.1.0.0]
------------

Added
~~~~~

- Baseline: Make the Czech year-end closing postable: retype 701/702/710
  from off_balance, which Odoo refuses to mix with any other account in one
  entry.
