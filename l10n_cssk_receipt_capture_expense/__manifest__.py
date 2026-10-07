# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Fiscal Receipt Capture — Employee Expenses",
    "version": "19.0.1.0.0",
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

One expense per VAT rate
------------------------

Not a stylistic choice. ``hr.expense`` carries a single ``tax_ids`` and a single
amount, so a receipt with food at 5 %, water at 19 % and alcohol at 23 % cannot
be one expense without throwing away the VAT split — and the VAT split is the
deductible part. The receipt's own per-rate recap therefore becomes one expense
each, all pointing back at the receipt.

Tax-included taxes are required
-------------------------------

``hr.expense`` derives its unit price from the total, so the receipt's gross
only lands on the right base when the mapped purchase tax is **price-included**.
Rather than post a plausible-looking wrong number, this module checks the created
expense against the receipt and refuses with the reason named.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["l10n_cssk_receipt_capture", "hr_expense"],
    "data": [
        "views/cssk_receipt_views.xml",
        "views/hr_expense_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
}
