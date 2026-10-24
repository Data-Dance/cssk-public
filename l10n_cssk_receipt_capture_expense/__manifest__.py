# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Fiscal Receipt Capture — Employee Expenses",
    "version": "19.0.1.1.0",
    "summary": "Turn a captured fiscal receipt into employee expenses, and "
               "capture receipts from the expense attachment upload.",
    "description": """
Fiscal Receipt Capture — Employee Expenses
==========================================

The expense sink for ``l10n_cssk_receipt_capture``, and the reason the framework
is worth having on Community: Odoo's **Expenses** app is Community (LGPL-3), but
the only thing that reads a receipt for you — ``hr_expense_extract`` — is
Enterprise and bills IAP credits per page. A Slovak receipt does not need
reading: the figures are already in the eKasa system, exact.

Two directions
--------------

* **From a receipt** — *Create Expenses* on a captured receipt.
* **From the Expenses app** — uploading receipt images creates one captured
  receipt per attachment and tries the providers, so the familiar "drop your
  receipts here" flow gains the QR lookup without the Enterprise module.

One receipt, one expense — whatever its VAT rates
-------------------------------------------------

``hr.expense`` holds one amount and applies all its taxes to it as one base,
which for food at 5 % and alcohol at 23 % would be a 28 % tax on everything.
So a receipt with several rates is still one expense, carrying every rate's
tax, but its VAT figure and its journal entry — employee-paid or company-paid —
are built from the receipt's own recap: a base and a VAT line per rate. An
expense whose amount or taxes were edited away from its receipt refuses to post.

Any purchase tax works
----------------------

``hr.expense`` computes its taxes from the amount as a tax-included total,
whether or not the tax itself is price-included, so the receipt's gross lands
on the receipt's own base with the chart's ordinary taxes — the same ones the
vendor-bill path uses. The created expenses are still checked against the
receipt's total and VAT before they are kept.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["l10n_cssk_receipt_capture", "hr_expense"],
    "data": [
        "security/ir_rule.xml",
        "views/cssk_receipt_views.xml",
        "views/hr_expense_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
}
