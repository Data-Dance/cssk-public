=========
Changelog
=========

Unreleased
----------

* Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

19.0.1.0.1 (2026-09-07)
-----------------------

* Resetting a payslip to draft now runs the garnishment reset guard first, so
  a payslip whose deduction is already with the payee cannot go back to draft
  and have that deduction counted a second time. The guard and its assertions
  live in ``l10n_cssk_hr_payroll_garnishment_base``; the tests are declared
  here because they need a real payslip lifecycle.

19.0.1.0.0 (2026-07-27)
-----------------------

* Initial release.
