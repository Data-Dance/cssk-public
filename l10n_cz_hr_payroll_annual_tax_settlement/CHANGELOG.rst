=========
Changelog
=========

Unreleased
----------

- **Renamed from ``l10n_cz_hr_payroll_vyuctovani``**, as on 19.0
  (2026-09-30). The technical name is now English, like most of the
  repository. No migration is shipped, because the module was not yet
  installed in production. A development database that had it installed
  keeps an orphaned ``l10n_cz_hr_payroll_vyuctovani`` row. Install
  ``l10n_cz_hr_payroll_annual_tax_settlement`` there.

18.0.1.0.1 (2026-07-06)
-----------------------

* Normalized user-facing strings to clean English (form name, selection labels,
  field labels/help and error messages; authority codes kept as tokens). Added
  a Czech translation (``i18n/cs.po``).

18.0.1.0.0 (2026-07-05)
-----------------------

* Ported to Odoo 18.0. Report logic unchanged; the runtime test's data
  setup was adapted to the 18.0 ``hr.contract`` API.

19.0.1.0.0 (2026-07-05)
-----------------------

* Initial release: annual CZ Vyúčtování daně ze závislé činnosti (DPZVD6) EPO
  reconciliation, aggregating advance income tax (``INCOMETAX``) over the
  calendar year — annual total in Part II, per-month rows in Part I — validated
  against the official ``dpzvd6_epo2.xsd``.
* WHTAX (srážková daň) excluded (separate form); Part II difference rows and
  non-resident annexes left for manual completion (documented human-verify
  notes).
