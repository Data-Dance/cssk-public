{
    "name": "Slovak VRP2 - Invoice Payments",
    "version": "19.0.2.3.0",
    "author": "Data Dance s.r.o.",
    "category": "Accounting/Localizations",
    "summary": "Fiscalize customer invoices through the Slovak Virtual Cash Register (VRP 2)",
    "description": """
Issue Slovak VRP 2 fiscal receipts ("pokladničný doklad — úhrada faktúry") for
customer invoices and retain them in Odoo. The Odoo payment/reconciliation is
handled by your normal flow; this module only fiscalizes.

- "Fiscalize in VRP2" on the invoice form (single invoice) and as a list mass
  action (many invoices → one merged PDF of the official VRP2 receipts).
- 0.05 € cash rounding driven by the register's "Zaokrúhľovať na 5 centov"
  setting.
- Storno: cancel the fiscal receipt of a fiscalized invoice.
- Hidden "VRP2 Fiscalized" column on the invoice list.
- Stores every receipt as a ``vrp2.receipt`` record (number, fiscal codes,
  QR, raw request/response) with a printable report.
- No POS dependency.
    """,
    "license": "AGPL-3",
    "depends": [
        "l10n_sk_vrp2_base",
        "account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "views/vrp2_receipt_views.xml",
        "views/account_move_views.xml",
        "views/account_payment_register_views.xml",
        "report/vrp2_receipt_report.xml",
    ],
    "installable": True,
    "application": False,
}
