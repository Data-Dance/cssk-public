# Copyright 2026 Data Dance s.r.o.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
{
    "name": "Slovakia — VAT Tax Template + Report Tags (18.0 backport of 19.0)",
    "version": "18.0.1.0.0",
    "summary": "Backports the full Odoo 19.0 core l10n_sk VAT tax set (43 taxes) "
               "and DPH report-tag set onto the smaller 18.0 l10n_sk chart, "
               "bringing 18.0 SK to VAT parity with 19.0.",
    "description": """
Slovakia — VAT Tax Template + Report Tags (18.0 backport)
=========================================================

Odoo 18.0 CE ``l10n_sk`` ships only 7 VAT taxes and **no** tax tags / tax
report — the DPH report-tag set and the extended tax template (5 % rate,
service/goods scope, reverse-charge, intra-EU acquisition, triangular, import
with postponed accounting, customs, bad-debt, § 53b unpaid correction,
special-regime) were only added to CE ``l10n_sk`` in 19.0.

This module backports that 19.0 data onto the 18.0 chart:

* **53 DPH report tags** (``account.account.tag``, codes 01..29 + lettered
  sub-codes + 24_PR) with stable XML-IDs.
* **43 VAT taxes** (adapted from the 19.0 ``account.tax-sk.csv``), each bound to
  its DPH tags via ``@template('sk', 'account.tax')`` — so any SK company's
  chart is augmented on install, and posted moves carry the tags the SK
  VAT/KV/EC evaluators read.
* The **5 % VAT tax group** (``tax_group_vat_5``), absent from 18.0.

It is CE-clean: the tags are consumed by our own
``account.account.tag._get_tax_tags`` evaluators (l10n_sk_vat_return / _kv_dph /
_ec_sales), NOT by the EE ``account_reports`` engine. The on-screen Odoo SK tax
report (``account.report`` from 19.0 ``tax_report.xml``) is intentionally **not**
loaded — see README (it would auto-create a duplicate +/- tag set diverging from
the controlled XML-ID tags, and our statutory filing does not use it).
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations/Account Charts",
    "depends": ["l10n_sk"],
    "data": [
        "data/account_tax_report_tags.xml",
    ],
    "installable": True,
}
