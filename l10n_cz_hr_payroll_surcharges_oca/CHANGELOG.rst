=========
Changelog
=========

All notable changes to **l10n_cz_hr_payroll_surcharges_oca** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- **Renamed from ``l10n_cz_hr_payroll_priplatky_oca``.** The technical name
  is now English, like most of the repository. No migration is shipped,
  because the module was not yet installed in production. A development
  database that had it installed keeps an orphaned
  ``l10n_cz_hr_payroll_priplatky_oca`` row. Install
  ``l10n_cz_hr_payroll_surcharges_oca`` there.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- DISCHARGED 2026-09-30 by 6f9cc41 on branch 18.0-catch-up (reaches 18.0
  when that branch lands) — do not port this again.
  **The rename (2026-09-30), not yet on 18.0.** 18.0 still ships
  ``l10n_cz_hr_payroll_priplatky_oca``. Rename it together with the rest of
  the 2026-09-30 batch (the fiscal-year closing, surcharges, annual tax
  settlement and inventory verification modules). Rename every reference
  too: dependent manifests, ``odoo.addons.*`` imports, the ``.pot`` file
  name and ``module_*`` settings toggles. The 19.0 commit is the checklist.

Carry-over to 20.0
~~~~~~~~~~~~~~~~~~

- DISCHARGED 2026-09-30 by 51a5085 on branch 20.0 — do not port this again.
  **The rename (2026-09-30), not yet on 20.0.** 20.0 still ships
  ``l10n_cz_hr_payroll_priplatky_oca``. Rename it together with the rest of
  the 2026-09-30 batch (the fiscal-year closing, surcharges, annual tax
  settlement and inventory verification modules). Rename every reference
  too: dependent manifests, ``odoo.addons.*`` imports, the ``.pot`` file
  name and ``module_*`` settings toggles. The 19.0 commit is the checklist.

[19.0.1.1.1] — 2026-10-27
-------------------------

**Changed**

- **Czech translation.** The module had no Czech translation, so the surcharge fields on the payslip (*Wage Surcharges* and the hours fields) showed in English; a translation is added.

[19.0.1.1.0] — 2026-10-27
-------------------------

Added
~~~~~

- **Overtime Wage (§ 114).** Overtime hours are paid their own wage — the
  hourly wage, or the monthly wage over the month's scheduled hours — next to
  the overtime surcharge. Only the surcharge was paid before.
- **Minimum Wage Top-up (§ 111).** A wage below the minimum wage is topped up
  on the payslip, before gross pay, so it is insured and taxed. Overtime pay,
  the surcharges and wage replacements do not count towards the minimum.

[19.0.1.0.1] — 2026-10-27
-------------------------

Fixed
~~~~~

- **The five surcharge rules now run.** They were created but never added
  to the *Czech Republic: Regular Pay* structure, so no Czech payslip on the
  OCA engine computed a surcharge. They are now part of the structure.

[19.0.1.0.0]
------------

Added
~~~~~

- Baseline: Statutory Czech wage surcharges (§§ 114–118 zákoníku práce) as
  salary rules for the OCA payroll engine.
