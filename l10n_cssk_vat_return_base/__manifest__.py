{
    "name": "CZ/SK VAT Return — Shared Framework (DPH priznanie / DPHDP3)",
    "version": "19.0.1.10.5",
    "summary": "Country-neutral framework for the Slovak and Czech VAT return: "
               "numbered report lines computed from tax tags + aggregate "
               "formulas, with an XSD-validated XML export. CE-clean (own "
               "tax-tag evaluator, no account_reports engine).",
    "description": """
CZ/SK VAT Return — Shared Framework
===================================

The country-neutral engine behind the Slovak **daňové priznanie k DPH**
(DPHv25) and Czech **DPHDP3**. The VAT return is a fixed set of numbered lines
(riadky), each computed as a signed sum of move-line balances carrying given
**tax tags**, plus aggregate lines (totals) over other lines.

**CE-clean:** the tax tags and the resolution helper
(``account.account.tag._get_tax_tags``) live in Odoo CE; this module ships its
own small evaluator, so it does **not** depend on the EE ``account_reports``
engine. Works on Community and Enterprise, 18.0 and 19.0.

Provides:

* ``cssk.vat.return.version`` — versioned line definitions + template + schema.
* ``cssk.vat.return.line.def`` — a line: ``tags`` (tax-tag formula, e.g. ``-03``),
  ``aggregate`` (formula over other line codes, e.g. ``r04 + r06``) or ``manual``.
* ``cssk.vat.return`` (mail.thread; draft → preview → exported → submitted) with
  the evaluator and ``action_export_xml``.
* ``cssk.vat.return.line`` — a computed line value.

Country modules ship the line definitions (wired to the country's tax tags),
the XML template and the schema.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["account", "mail", "l10n_cssk_core",
        "l10n_cssk_submission_base"],
    "data": [
        "security/ir.model.access.csv",
        "security/record_rules.xml",
        "views/account_tax_views.xml",
        "views/cssk_vat_return_version_views.xml",
        "views/cssk_vat_return_views.xml",
        "views/cssk_vat_return_menus.xml",
    ],
    "installable": True,
}
