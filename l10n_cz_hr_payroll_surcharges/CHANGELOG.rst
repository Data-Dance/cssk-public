=========
Changelog
=========

All notable changes to **l10n_cz_hr_payroll_surcharges** are documented here.
Versioning follows the Odoo manifest (``18.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- **Renamed from ``l10n_cz_hr_payroll_priplatky``**, as on 19.0
  (2026-09-30). The technical name is now English, like most of the
  repository. No migration is shipped, because the module was not yet
  installed in production. A development database that had it installed
  keeps an orphaned ``l10n_cz_hr_payroll_priplatky`` row. Install
  ``l10n_cz_hr_payroll_surcharges`` there.

[18.0.1.0.0]
------------

Added
~~~~~

- Baseline: Engine-neutral statutory wage surcharges for overtime, public
  holiday, night, weekend and difficult-environment work (§§ 114–118
  zákoníku práce), plus the minimum wage and the top-up to it.
