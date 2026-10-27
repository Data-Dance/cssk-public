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

[19.0.1.1.0] — 2026-10-27
-------------------------

Added
~~~~~

- **Minimum wage top-up comparison** on the contract: hourly (the default,
  as § 111 odst. 2 písm. a) of the Labour Code prescribes) or monthly, where
  that was agreed in advance.
- The arithmetic for the wage of overtime hours (§ 114 odst. 1) and for the
  minimum wage top-up on the contract's basis, used by the engine bridges.

Fixed
~~~~~

- Citations of the minimum wage rules point to § 111 odst. 1 and 2, as
  renumbered from 2025.

[19.0.1.0.1] — 2026-10-27
-------------------------

Fixed
~~~~~

- **Part-time employees are no longer overpaid the difficult-environment
  surcharge.** The hourly minimum wage behind § 117 was raised by the
  employee's own calendar, so a 20 h/week employee was paid on twice the
  hourly minimum wage. § 111 odst. 5 zákoníku práce raises it only for the
  employer's shorter standard week; the company calendar is now the
  reference.
- Help texts cite nařízení vlády č. 443/2024 Sb. (in force since 1. 1. 2025)
  instead of the repealed č. 567/2006 Sb., and the missing-rate errors point
  to *Employees ▸ Configuration ▸ Czech Wage Surcharges*.

[19.0.1.0.0]
------------

Added
~~~~~

- Baseline: Engine-neutral statutory wage surcharges for overtime, public
  holiday, night, weekend and difficult-environment work (§§ 114–118
  zákoníku práce), plus the minimum wage and the top-up to it.
