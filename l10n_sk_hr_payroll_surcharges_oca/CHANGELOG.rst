=========
Changelog
=========

Unreleased
----------

- **19.0.1.0.8 (2026-11-21): overtime hours are paid at the wage achieved.**
  *Overtime Pay* is the monthly salary over the hours of the month, or the
  exact hourly rate, times the overtime hours (§ 121 ods. 1 Zákonníka
  práce); only *Overtime Surcharge* is on average earnings. See
  ``l10n_sk_hr_payroll_surcharges`` 19.0.1.3.0. Tests with the figures of
  the Enterprise bridge: after a raise from 1 600 to 2 100, eight hours in
  April 2026 are 95.46 and 18.75; at an hourly rate raised from 6.125 to
  7.333 they are 58.67 and 12.25; with an unpaid day in June 2026 on 2 000
  they are 90.91 and 22.73. The rules themselves are unchanged.

- **19.0.1.0.7 (2026-11-21): overtime hours are time worked for the average
  earnings.** Overtime pay was in the wage of the decisive quarter while the
  overtime hours were missing from the hours worked (§ 134 ods. 1 Zákonníka
  práce). 2 000 a month with ten overtime hours each month of the second
  quarter of 2026 gave 6 432.92 / 520 = 12.3710; it is 6 432.92 / 550 =
  11.6962.

- **19.0.1.0.7 (2026-11-21): no minimum wage top-up for a month of maternity,
  parental or paternity leave or of a § 142 obstacle.** See
  ``l10n_sk_hr_payroll_surcharges`` 19.0.1.2.9.

- **The surcharge rules are shared by every company.** They took the
  company of whoever installed the module, so no other company saw them
  and its payslips paid no Slovak surcharges. Upgrading the module repairs an
  existing database.

- **Installs without accounting.** The install hook assumed the Accounting
  app and failed the whole install on a payroll-only database.

- **Renamed from ``l10n_sk_hr_payroll_priplatky_oca``.** The technical name
  is now English, like most of the repository. No migration is shipped,
  because the module was not yet installed in production. A development
  database that had it installed keeps an orphaned
  ``l10n_sk_hr_payroll_priplatky_oca`` row. Install
  ``l10n_sk_hr_payroll_surcharges_oca`` there.

Carry-over to 18.0:

- **19.0.1.0.7 (2026-11-21), not yet on 18.0:** the overtime hours in the
  divisor of the average earnings.

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

[19.0.1.0.6] — 2026-11-05
-------------------------

Fixed
~~~~~

- Czech catalogue: translated the strings that were still English.

[19.0.1.0.4] — 2026-10-27
-------------------------

**Changed**

- **Slovak translation.** The module had no Slovak translation, so the surcharge fields on the payslip (*Wage Surcharges* and the hours fields) showed in English; a translation is added.

[19.0.1.0.3] — 2026-10-27
-------------------------

**Fixed**

- Installed after the accounting bridge, the surcharge rules now get the wage account 521000 instead of none; only these rules are touched.

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
