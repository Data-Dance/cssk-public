=========
Changelog
=========

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
