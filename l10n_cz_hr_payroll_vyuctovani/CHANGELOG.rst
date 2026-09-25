=========
Changelog
=========

Unreleased
----------

* Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

19.0.1.0.1 (2026-07-06)
-----------------------

* Normalized user-facing strings to clean English (form name, selection labels,
  field labels/help and error messages; authority codes kept as tokens). Added
  a Czech translation (``i18n/cs.po``).

19.0.1.0.0 (2026-07-05)
-----------------------

* Initial release: annual CZ Vyúčtování daně ze závislé činnosti (DPZVD6) EPO
  reconciliation, aggregating advance income tax (``INCOMETAX``) over the
  calendar year — annual total in Part II, per-month rows in Part I — validated
  against the official ``dpzvd6_epo2.xsd``.
* WHTAX (srážková daň) excluded (separate form); Part II difference rows and
  non-resident annexes left for manual completion (documented human-verify
  notes).
