=========
Changelog
=========

Unreleased
----------

- **Renamed from ``l10n_cz_hr_payroll_vyuctovani``.** The technical name is
  now English, like most of the repository. No migration is shipped, because
  the module was not yet installed in production. A development database
  that had it installed keeps an orphaned ``l10n_cz_hr_payroll_vyuctovani``
  row. Install ``l10n_cz_hr_payroll_annual_tax_settlement`` there.

Carry-over to 18.0:

- DISCHARGED 2026-09-30 by 6f9cc41 on branch 18.0-catch-up (reaches 18.0
  when that branch lands) — do not port this again.
  **The rename (2026-09-30), not yet on 18.0.** 18.0 still ships
  ``l10n_cz_hr_payroll_vyuctovani``. Rename it together with the rest of the
  2026-09-30 batch (the fiscal-year closing, surcharges, annual tax
  settlement and inventory verification modules). Rename every reference
  too: dependent manifests, ``odoo.addons.*`` imports, the ``.pot`` file
  name and ``module_*`` settings toggles. The 19.0 commit is the checklist.

Carry-over to 20.0:

- DISCHARGED 2026-09-30 by 51a5085 on branch 20.0 — do not port this again.
  **The rename (2026-09-30), not yet on 20.0.** 20.0 still ships
  ``l10n_cz_hr_payroll_vyuctovani``. Rename it together with the rest of the
  2026-09-30 batch (the fiscal-year closing, surcharges, annual tax
  settlement and inventory verification modules). Rename every reference
  too: dependent manifests, ``odoo.addons.*`` imports, the ``.pot`` file
  name and ``module_*`` settings toggles. The 19.0 commit is the checklist.

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
