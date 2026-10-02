=========
Changelog
=========

Unreleased
----------

- **Renamed from ``l10n_sk_hr_payroll_priplatky_oca``.** The technical name
  is now English, like most of the repository. No migration is shipped,
  because the module was not yet installed in production. A development
  database that had it installed keeps an orphaned
  ``l10n_sk_hr_payroll_priplatky_oca`` row. Install
  ``l10n_sk_hr_payroll_surcharges_oca`` there.

Carry-over to 18.0:

- DISCHARGED 2026-09-30 by 6f9cc41 on branch 18.0-catch-up (reaches 18.0
  when that branch lands) — do not port this again.
  **The rename (2026-09-30), not yet on 18.0.** 18.0 still ships
  ``l10n_sk_hr_payroll_priplatky_oca``. Rename it together with the rest of
  the 2026-09-30 batch (the fiscal-year closing, surcharges, annual tax
  settlement and inventory verification modules). Rename every reference
  too: dependent manifests, ``odoo.addons.*`` imports, the ``.pot`` file
  name and ``module_*`` settings toggles. The 19.0 commit is the checklist.

Carry-over to 20.0:

- DISCHARGED 2026-09-30 by 51a5085 on branch 20.0 — do not port this again.
  **The rename (2026-09-30), not yet on 20.0.** 20.0 still ships
  ``l10n_sk_hr_payroll_priplatky_oca``. Rename it together with the rest of
  the 2026-09-30 batch (the fiscal-year closing, surcharges, annual tax
  settlement and inventory verification modules). Rename every reference
  too: dependent manifests, ``odoo.addons.*`` imports, the ``.pot`` file
  name and ``module_*`` settings toggles. The 19.0 commit is the checklist.

19.0.1.0.0 (2026-08-03)
-----------------------

* Initial release.
* Salary rules ``PRIPLATOK_NOC``, ``PRIPLATOK_SOBOTA``, ``PRIPLATOK_NEDELA``,
  ``PRIPLATOK_SVIATOK``, ``NADCAS_MZDA``, ``PRIPLATOK_NADCAS``,
  ``PRIPLATOK_STAZENY``, ``PRIPLATOK_POHOTOVOST`` and ``MIN_WAGE_TOPUP``,
  attached to the Slovak structure and sequenced before ``GROSS`` so every
  surcharge is insurable and taxable.
* Each surcharge rule declares its hours input, so the engine prefills the
  payslip with the codes to fill in.

19.0.1.0.1 (2026-08-03)
-----------------------

* Override ``_l10n_sk_work100_is_gross`` to True. The OCA engine's
  ``_compute_worked_days`` returns the full scheduled month and puts absences
  on separate negative lines, so the absence hours have to come back off
  ``WORK100`` before the minimum-wage comparison. See the base module's
  changelog for the overpayment this fixes.

19.0.1.0.2 (2026-08-26)
-----------------------

* Relicensed from ``Other proprietary`` to **AGPL-3**. The module depends on
  ``l10n_sk_hr_payroll_oca``, which is AGPL-3 and carries third-party
  copyright, so a proprietary licence here was not sustainable. This also
  brings it in line with its Czech counterpart
  ``l10n_cz_hr_payroll_priplatky_oca``, which has been AGPL-3 since its
  initial release.
