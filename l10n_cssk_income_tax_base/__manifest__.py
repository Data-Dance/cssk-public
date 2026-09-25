{
    "name": "CZ/SK Income Tax Return — framework",
    "summary": "Country-neutral framework for the corporate income-tax return "
               "(DPPO): versioned line definitions, accounting-result + "
               "aggregate evaluator, manual-override UI and XSD-validated XML "
               "export. Country layers supply the line set + schema.",
    "description": """
CZ/SK Income Tax Return — framework
===================================

The shared engine for the corporate income-tax return (DPPO), mirroring the VAT
return / financial-statement framework. CE-clean (depends on ``account`` only).

* ``cssk.income.tax.version`` + line definitions (``account`` = P&L result,
  ``aggregate`` = tax-computation spine, ``manual`` = accountant adjustments) +
  submission types.
* ``cssk.income.tax.return`` (mail.thread) — evaluator, manual-override that is
  preserved and fed into dependent aggregate lines on recompute, and
  XSD-validated statutory XML export.
* Create a statement (New), then set the period/version and Compute.

The country layer (``l10n_sk_dppo`` …) supplies the actual line set, the header
mapping and the official schema. The accounting→tax transformation (the
adjustment lines) is the accountant's domain — this framework auto-computes the
accounting result and the formulaic spine, and takes the rest as manual entry.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.5.5",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["account", "mail", "l10n_cssk_core",
        "l10n_cssk_submission_base"],
    "data": [
        "security/ir.model.access.csv",
        "security/record_rules.xml",
        "views/cssk_income_tax_views.xml",
    ],
    "installable": True,
}
