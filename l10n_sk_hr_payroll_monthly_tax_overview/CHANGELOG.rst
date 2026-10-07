=========
Changelog
=========

Unreleased
==========

* **Renamed from ``l10n_sk_hr_payroll_prehlad`` to ``l10n_sk_hr_payroll_monthly_tax_overview``.** The technical
  name is English now, like every other module here; the statutory form keeps its
  Slovak name in the module title, in the models and in the data files, exactly as
  ``kv_dph``, ``eldp`` and ``pvpoj`` keep theirs. No migration ships with this: on a
  database that already has the old module installed, the old record stays behind
  with no code and the new module installs fresh, so rename the module record
  before upgrading if the old one holds data.

* Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

19.0.2.0.0 (2026-09-16)
=======================

* **No longer declares ``res.company.l10n_sk_dic`` itself.** It was a plain
  stored ``Char`` here, and an identical one in ``l10n_sk_hr_payroll_hlasenie``,
  each so the module would be self-contained. That is safe between two identical
  definitions and unsafe against a third: ``l10n_sk_base`` declares the same
  field as ``related="partner_id.l10n_sk_dic"``. Install this module first, let
  an accountant fill the column, then install anything that pulls in
  ``l10n_sk_base`` — ``l10n_sk_invoice``, ``l10n_sk_dppo``, ``l10n_sk_dppo_fs``
  or ``l10n_sk_datadance`` — and the merged field acquires ``related=``, the ORM
  stops reading the column, and the value goes invisible with nothing having
  moved it. The Prehľad then refuses to file, correctly but confusingly, on a
  company whose DIČ was filled in last month.

  The field now comes from ``l10n_sk_base``, which is a new dependency and which
  migrates that column. **Breaking** only in that the dependency is required;
  no data is lost and nothing needs re-entering.

19.0.1.1.0 (2026-08-06)
=======================

* **The Prehľad can now be filed as an opravný.** ``riadny`` and ``opravny``
  were both hardcoded in the render context — ``"riadny": "1", "opravny": "0"``
  — so the form could only ever produce a regular Prehľad, with no way to
  amend one already sent. Both flags are now driven by the shared
  ``correction_type``. The FS wire format carries no dodatočný and no storno,
  so only those two are offered.

19.0.1.0.1 (2026-07-06)
~~~~~~~~~~~~~~~~~~~~~~~

* Normalized all user-facing strings to clean English (removed mixed-language
  parentheticals). Added a Slovak (``i18n/sk.po``) translation and the
  extraction template (``i18n/<module>.pot``).

19.0.1.0.0 (2026-07-05)
-----------------------

* Initial release: monthly SK Prehľad o zrazených a odvedených preddavkoch na
  daň (Finančná správa), employer-aggregate, validated against the official
  ``prehlad2026.xsd`` (PREHLAD_2026).
* Line mapping r00↔GROSS, r01↔income-tax advance (INCOMETAX19+25 / INCOMETAX),
  r05↔CHILD_BONUS (daňový bonus § 33), r08 = r04 − r05, with the § 33 bonus
  recap in II. časť.

19.0.1.0.2 (2026-08-03)
~~~~~~~~~~~~~~~~~~~~~~~

* Read the engine-dependent salary-rule codes from
  ``l10n_cssk_payroll_declaration_base.rule_codes`` instead of restating
  them locally. No behaviour change; the local tuples were correct, but
  the knowledge now has one home rather than three.
