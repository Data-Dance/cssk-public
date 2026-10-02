=========
Changelog
=========

All notable changes to **l10n_cz_hr_payroll_surcharges** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- **Renamed from ``l10n_cz_hr_payroll_priplatky``.** The technical name is
  now English, like most of the repository. No migration is shipped, because
  the module was not yet installed in production. A development database
  that had it installed keeps an orphaned ``l10n_cz_hr_payroll_priplatky``
  row. Install ``l10n_cz_hr_payroll_surcharges`` there.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- DISCHARGED 2026-09-30 by 6f9cc41 on branch 18.0-catch-up (reaches 18.0
  when that branch lands) — do not port this again.
  **The rename (2026-09-30), not yet on 18.0.** 18.0 still ships
  ``l10n_cz_hr_payroll_priplatky``. Rename it together with the rest of the
  2026-09-30 batch (the fiscal-year closing, surcharges, annual tax
  settlement and inventory verification modules). Rename every reference
  too: dependent manifests, ``odoo.addons.*`` imports, the ``.pot`` file
  name and ``module_*`` settings toggles. The 19.0 commit is the checklist.

Carry-over to 20.0
~~~~~~~~~~~~~~~~~~

- DISCHARGED 2026-09-30 by 51a5085 on branch 20.0 — do not port this again.
  **The rename (2026-09-30), not yet on 20.0.** 20.0 still ships
  ``l10n_cz_hr_payroll_priplatky``. Rename it together with the rest of the
  2026-09-30 batch (the fiscal-year closing, surcharges, annual tax
  settlement and inventory verification modules). Rename every reference
  too: dependent manifests, ``odoo.addons.*`` imports, the ``.pot`` file
  name and ``module_*`` settings toggles. The 19.0 commit is the checklist.

[19.0.1.0.0]
------------

Added
~~~~~

- Baseline: Engine-neutral statutory wage surcharges for overtime, public
  holiday, night, weekend and difficult-environment work (§§ 114–118
  zákoníku práce), plus the minimum wage and the top-up to it.
