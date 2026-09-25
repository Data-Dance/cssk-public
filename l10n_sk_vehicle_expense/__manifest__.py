# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "SK Vozidlá a PHL — paušály (§ 85n, § 19/2/l)",
    "summary": "50 % VAT deduction on mixed-use vehicles and the 80 % fuel "
               "tax-expense paušál — two independent Slovak regimes.",
    "description": """
SK Vozidlá a PHL — paušály
==========================

A car used for both business and private purposes is restricted **twice**, and
since 1 January 2026 the two restrictions are **independent of each other**:

* **DPH — § 85n zákona 222/2004** (zavedené zák. 261/2025, tretí konsolidačný
  balík): a flat **50 %** input-VAT deduction on personal vehicles (**M1, L1e,
  L3e**) used also privately — covering the purchase, long-term rental, fuel,
  repairs, technical improvements, vignettes. 100 % requires registering the
  exclusive business use and keeping detailed **electronic trip records**
  (§ 85n ods. 6). Exempt: taxi, autoškola, prenájom vozidiel, predvádzacie and
  náhradné vozidlá. **In force 1. 1. 2026 – 30. 6. 2028.**
* **Daň z príjmov — § 19 ods. 2 písm. l) bod 3 zákona 595/2003**: spotrebované
  PHL are a tax expense as a paušál of up to **80 %**, with no kniha jázd. This
  was **not** changed by the VAT reform.

The old link between them — § 49 ods. 5, which let the platiteľ deduct VAT up to
the income-tax paušál — was **deleted**, as it went beyond Directive 2006/112/ES.
A module that still ties the two together is now wrong.

How each half is implemented
----------------------------

* **VAT** — through the tax itself. This module adds ``vs_auto_23`` /
  ``vs_auto_19`` to the SK chart, whose **repartition** sends 50 % of the VAT to
  343 carrying the deduction tag and 50 % to a non-deductible expense account
  carrying none. That is the only way the DPH return stays right: splitting VAT
  with journal lines afterwards would report the full amount.
* **Income tax** — through a wizard on the vendor bill, which moves the non-tax
  share of the fuel cost to the non-deductible account. Totals, VAT and payable
  are untouched; only the expense classification changes.

The non-deducted VAT is itself **not a tax expense**, so it lands in the same
account as the non-tax fuel share and is picked up together as a *pripočítateľná
položka* in the DPPO.

Honesty flags
-------------

* The **50 % regime is time-boxed** and the ratios are configuration, not
  hard-coded — but this module does **not** date-gate them automatically. A
  company still on an older period, or one past 30. 6. 2028, must set its own.
* Vehicle **category** (M1/L1e/L3e) and the exempt activities are **not**
  modelled: the module does not know which of your vehicles the restriction
  applies to. Use the ``vs_auto_*`` taxes on the bills where it does.
* The 80 % paušál is an **election** with conditions — notably the "primeraný
  počet najazdených kilometrov podľa stavu tachometra" test — which is the
  accountant's call, not this module's.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.0.2",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["l10n_sk"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/l10n_sk_fuel_split_views.xml",
        "views/account_move_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
