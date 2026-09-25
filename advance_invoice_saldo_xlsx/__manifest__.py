# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
{
    "name": "Advance Invoices — Open Advances Saldo (XLSX)",
    "version": "19.0.1.0.1",
    "summary": "XLSX saldo of issued and received advance invoices: paid, "
               "tax-documented, deducted and open amounts.",
    "description": """
Advance Invoices — Open Advances Saldo (XLSX)
=============================================

One workbook, two sheets:

* **Issued advances** (``sale_order_advance_invoice``): per advance —
  total, paid, paid date, tax-documented amount, amount already deducted
  on the final invoice, open saldo (paid − deducted), payment and
  accounting statuses.
* **Received advances** (``purchase_order_advance_invoice``): the mirror
  columns from the supplier side.

By default only advances with an open saldo (or still waiting for a tax
document / payment) are listed; a checkbox includes the settled ones.
Launched from Accounting → Reporting.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": [
        "report_xlsx",
        "sale_order_advance_invoice",
        "purchase_order_advance_invoice",
    ],
    "data": [
        "security/ir.model.access.csv",
        "report/report_data.xml",
        "views/wizard_views.xml",
    ],
    "installable": True,
}
