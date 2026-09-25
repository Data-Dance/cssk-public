=========
Changelog
=========

All notable changes to **l10n_sk_vehicle_expense** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.2] — 2026-09-13
-------------------------

Fixed
~~~~~

- Gave the technical computed field an explicit ``string=``. Without one Odoo
  derives a label from the field name and exports it — "L10N Sk Jcd Is Sk
  Company" and the like — which is not English in any useful sense and cannot
  be translated into anything better. The field is a view modifier behind
  ``invisible="1"``, so no user reads it; the point is that it stops putting a
  mangled msgid in the catalogue.

[19.0.1.0.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- Slovak catalogue completed. Terms already stated in Slovak in the source are
  deliberately left untranslated — the source IS the translation, per the
  hybrid convention for these modules — so an empty ``msgstr`` there is correct
  rather than missing.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.0.0] — 2026-08-05
-------------------------

Added
~~~~~

- ``vs_auto_23`` / ``vs_auto_19`` — vehicle taxes whose repartition deducts only
  **50 %** of the VAT (§ 85n), the other half landing untagged on a non-deductible
  expense account so it reaches no row of the DPH return.
- Wizard on the vendor bill moving the non-tax share of fuel (**80 %** paušál,
  § 19 ods. 2 písm. l) bod 3) to that same account, without touching totals or VAT.
- Company settings for both ratios and the account, wired from the chart template
  and a post-init hook.
- 6 tests, incl. the assertion that only the deducted half carries tag 21.

Note on the rates
~~~~~~~~~~~~~~~~~

Built first against a 2017 Finančná správa guidance that gave **80 %** for both
sides, tied together by § 49 ods. 5. That is **obsolete**: the third consolidation
package (zák. **261/2025**, in force 1. 1. 2026) deleted § 49 ods. 5 and introduced
the § 85n flat **50 %** VAT deduction, while leaving the § 19 income-tax paušál at
80 %. The module was rebuilt around the two now-independent regimes. Dated sources
are worth re-checking before trusting a rate.
