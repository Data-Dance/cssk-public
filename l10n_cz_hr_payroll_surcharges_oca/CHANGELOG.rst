=========
Changelog
=========

All notable changes to **l10n_cz_hr_payroll_surcharges_oca** are documented here.
Versioning follows the Odoo manifest (``18.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- **Renamed from ``l10n_cz_hr_payroll_priplatky_oca``**, as on 19.0
  (2026-09-30). The technical name is now English, like most of the
  repository. No migration is shipped, because the module was not yet
  installed in production. A development database that had it installed
  keeps an orphaned ``l10n_cz_hr_payroll_priplatky_oca`` row. Install
  ``l10n_cz_hr_payroll_surcharges_oca`` there.

[18.0.1.0.0]
------------

Added
~~~~~

- Baseline: Statutory Czech wage surcharges (§§ 114–118 zákoníku práce) as
  salary rules for the OCA payroll engine.
