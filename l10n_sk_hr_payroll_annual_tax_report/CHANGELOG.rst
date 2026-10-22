Unreleased
~~~~~~~~~~

* **Renamed from ``l10n_sk_hr_payroll_hlasenie`` to ``l10n_sk_hr_payroll_annual_tax_report``.**
  Carries 19.0's c81297e1 to this branch. The technical name is English now, like
  every other module here; the statutory form keeps its Slovak name in the module
  title, in the models and in the data file names, exactly as ``kv_dph``, ``eldp``
  and ``pvpoj`` keep theirs. These were the last two modules whose technical name
  was an ordinary Slovak word.

  **No migration ships with this, and it matters more here than it did for
  závierka and inventarizácia.** This is a declaration module: it holds submitted
  filings. On a database that already has the old module installed, the old record
  stays behind with no code and the new module installs fresh, so the module
  record must be renamed BEFORE upgrading, or the filings are left behind under a
  module that no longer exists.

18.0.1.0.1 (2026-07-06)
~~~~~~~~~~~~~~~~~~~~~~~

* Normalized all user-facing strings to clean English (removed mixed-language
  parentheticals). Added a Slovak (``i18n/sk.po``) translation and the
  extraction template (``i18n/<module>.pot``).

18.0.1.0.0 (2026-07-05)
~~~~~~~~~~~~~~~~~~~~~~~

* Ported to Odoo 18.0. Report logic unchanged; the runtime test's data
  setup was adapted to the 18.0 ``hr.contract`` API.

19.0.1.0.0 (2026-07-05)
~~~~~~~~~~~~~~~~~~~~~~~~~

* Initial release of the annual Slovak employer income-tax report **Hlásenie o
  vyúčtovaní dane a o úhrne príjmov zo závislej činnosti** (§ 39 ods. 9 zák.
  595/2003 Z. z.).
* Engine-neutral (built on ``l10n_cssk_payroll_declaration_base``; works with
  the ``payroll`` engine and the ``hr_payroll`` engine).
* Aggregates a full calendar year of payslips into the aggregate part
  (telo/cast1..cast3) and a full per-employee annex Časť V (telo/cast5, two
  employees per page).
* XML validated against the official Finančná správa schema ``rh2023.xsd``.
