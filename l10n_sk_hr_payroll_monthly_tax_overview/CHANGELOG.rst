=========
Changelog
=========

Unreleased
----------

* **Renamed from ``l10n_sk_hr_payroll_prehlad`` to ``l10n_sk_hr_payroll_monthly_tax_overview``.**
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
-----------------------

* Normalized all user-facing strings to clean English (removed mixed-language
  parentheticals). Added a Slovak (``i18n/sk.po``) translation and the
  extraction template (``i18n/<module>.pot``).

18.0.1.0.0 (2026-07-05)
-----------------------

* Ported to Odoo 18.0. Report logic unchanged; the runtime test's data
  setup was adapted to the 18.0 ``hr.contract`` API.

19.0.1.0.0 (2026-07-05)
-----------------------

* Initial release: monthly SK Prehľad o zrazených a odvedených preddavkoch na
  daň (Finančná správa), employer-aggregate, validated against the official
  ``prehlad2026.xsd`` (PREHLAD_2026).
* Line mapping r00↔GROSS, r01↔income-tax advance (INCOMETAX19+25 / INCOMETAX),
  r05↔CHILD_BONUS (daňový bonus § 33), r08 = r04 − r05, with the § 33 bonus
  recap in II. časť.
