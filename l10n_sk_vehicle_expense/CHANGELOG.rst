=========
Changelog
=========

All notable changes to **l10n_sk_vehicle_expense** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Fixed
~~~~~

- The *non-deductible account* picker in Settings listed other companies'
  accounts: Odoo drops a string domain when it copies a field into a related
  one.

[19.0.1.1.0] — 2026-10-27
-------------------------

Fixed
~~~~~

- **The fuel split keeps the bill total with prices that include tax.** It
  split the net subtotal and wrote the parts back as unit prices; with a
  tax included in the price Odoo took the VAT out of them a second time, so
  a 123.00 bill became 100.00. The split now works on the price as entered.
- **The deducted half of the 19 % vehicle tax is booked on 343110**, the
  account of Odoo's own 19 % purchase tax, instead of 343120 (the 23 %
  account). Upgrading moves existing taxes still on 343120; posted entries
  are not changed.

Removed
~~~~~~~

- The *Vehicle VAT deduction (%)* setting. It changed nothing: § 85n fixes
  the share at 50 %, and it is built into the two vehicle taxes, where the
  VAT return reads it.

[19.0.1.0.3] — 2026-10-27
-------------------------

Fixed
~~~~~

- **The two vehicle taxes are created on installation for Slovak companies
  that already have the chart.** They were added only when the chart was
  loaded, so on an existing database the module installed without the taxes
  it is for. Taxes a company already has are left untouched, never
  duplicated; a company whose chart lacks an account the taxes need is
  skipped with a warning in the log.
- User guide: the non-deducted § 85n VAT is **not** a tax expense and, on a
  vehicle, not part of its entry price — § 52zzzk of the Income Tax Act,
  in force from 1. 1. 2026, overrides the general rules the guide cited.

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
