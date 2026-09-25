==========================
SK Vozidlá a PHL — paušály
==========================

A car used for both business and private purposes is restricted **twice**, and
since 1 January 2026 the two restrictions are **independent**.

============================ ===================================== ========
Regime                       Provision                             Share
============================ ===================================== ========
Odpočet DPH                  § 85n zák. 222/2004 (zák. 261/2025)   **50 %**
Daňový výdavok na PHL        § 19 ods. 2 písm. l) bod 3, 595/2003  **80 %**
============================ ===================================== ========

The old link between them — **§ 49 ods. 5**, which let the platiteľ deduct VAT up
to the income-tax paušál — was **deleted**, as it went beyond Directive
2006/112/ES. A module that still ties the two together is now wrong.

§ 85n in detail
===============

* Applies to **M1, L1e, L3e** vehicles used also privately.
* Covers the purchase, long-term rental, fuel, repairs, technical improvements,
  vignettes — not just fuel.
* **100 %** deduction requires registering the exclusive business use and keeping
  detailed **electronic trip records** (§ 85n ods. 6).
* Exempt: taxi, autoškola, prenájom vozidiel, predvádzacie and náhradné vozidlá;
  utility (non-M1) vehicles are unaffected.
* **In force 1. 1. 2026 – 30. 6. 2028.**

How each half is implemented
============================

**VAT — in the tax itself.** This module adds ``vs_auto_23`` / ``vs_auto_19``,
whose repartition sends 50 % of the VAT to 343 *carrying the deduction tag* and
50 % to a non-deductible expense account *carrying none*. That is the only way
the DPH return stays correct — splitting VAT with journal lines afterwards would
report the full amount as deducted.

**Income tax — in a wizard** on the vendor bill, which moves the non-tax share of
the fuel cost to the non-deductible account. Totals, VAT and the payable are
untouched; only the expense classification changes.

The non-deducted VAT is itself **not a tax expense**, so it lands in the same
account as the non-tax fuel share, and the two are picked up together as a
*pripočítateľná položka* in the DPPO.

Honesty flags
=============

* The 50 % regime is **time-boxed**, and this module does **not** date-gate the
  ratios. Periods before 2026 or after 30. 6. 2028 need their own setting.
* Vehicle **category and the exempt activities are not modelled** — the module
  does not know which of your vehicles the restriction covers. Use the
  ``vs_auto_*`` taxes on the bills where it applies.
* The 80 % paušál is an **election** with conditions attached, notably the
  "primeraný počet najazdených kilometrov podľa stavu tachometra" test. That is
  the accountant's call.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
