=========
Changelog
=========

Unreleased
----------

- **Renamed from ``l10n_sk_hr_payroll_priplatky_oca``**, as on 19.0
  (2026-09-30). The technical name is now English, like most of the
  repository. No migration is shipped, because the module was not yet
  installed in production. A development database that had it installed
  keeps an orphaned ``l10n_sk_hr_payroll_priplatky_oca`` row. Install
  ``l10n_sk_hr_payroll_surcharges_oca`` there.

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
