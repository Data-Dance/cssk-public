{
    "name": "Slovakia — VAT Return (Daňové priznanie k DPH)",
    "version": "18.0.1.1.0",
    "summary": "Slovak VAT return (DPHv25) — output/input lines wired to the "
               "l10n_sk tax tags, with FS SR DPH XML export. Built on the "
               "shared l10n_cssk_vat_return_base framework.",
    "description": """
Slovakia — VAT Return (Daňové priznanie k DPH)
==============================================

Concrete Slovak VAT return on top of ``l10n_cssk_vat_return_base``. Line
definitions mirror the **l10n_sk** DPH report tag formulas, so the per-line
values match what Odoo's own report would compute — but with a CE-clean
evaluator (no ``account_reports``).

Shipped lines (validate the full form + the net-payable computation with a SK
accountant):

* Output base/tax per category: ``sk01``, ``sk03`` (standard), ``sk05`` (reduced).
* Deductible tax: ``sk19``, ``sk20``.
* Aggregates: total output base/tax, total deductions, net VAT.

The net-payable lines that Odoo computes with ``sum`` / custom engines (sk_30+)
are out of scope of the simple tags+aggregate evaluator and need extended-engine
support or manual entry.

FS SR ``DPH`` XML export (template + stand-in XSD — replace with the official
schema before live filing).
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": [
        "l10n_cssk_vat_return_base",
        "l10n_sk",
        "l10n_sk_statutory",
        "l10n_sk_tax_report_backport",
    ],
    "data": [
        "security/ir.model.access.csv",
        "report/l10n_sk_vat_return_templates.xml",
        "data/cssk_vat_return_version_data.xml",
        "data/cssk_vat_return_2024_version_data.xml",
        "views/l10n_sk_par53b_views.xml",
    ],
    "installable": True,
}
