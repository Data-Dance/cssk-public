{
    "name": "Sale Order Advance Invoice",
    "version": "19.0.2.5.3",
    "summary": "Advance invoices (proforma) with tax documents on received payments",
    "description": """
Advance Invoices
================

Country-neutral engine for the advance-invoice / proforma flow used in Czech and
Slovak accounting (zálohová / preddavková faktura): an advance is its own sale
order, payable by QR or manual payment, that produces a tax document on the
received payment and is settled (deducted) on the final invoice.

Install a localization layer to wire the statutory accounts automatically:

* ``l10n_cz_sale_order_advance_invoice`` — Czech chart
* ``l10n_sk_sale_order_advance_invoice`` — Slovak chart

See the documentation in ``static/description``.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "depends": ["sale", "sale_management", "account_payment"],
    "category": "Sales/Sales",
    "post_init_hook": "post_init_hook",
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "data/account_journal_data.xml",
        "data/mail_template_data.xml",
        "wizard/sale_make_invoice_advance_views.xml",
        "wizard/sale_advance_invoice_wizard_views.xml",
        "wizard/account_move_link_advance_invoice_wizard_views.xml",
        "wizard/sale_order_manual_payment_wizard_views.xml",
        "wizard/sale_order_manual_transfer_link_wizard_views.xml",
        "report/ir_actions_report.xml",
        "report/report_saleorder_templates.xml",
        "report/report_invoice_templates.xml",
        "views/account_move_views.xml",
        "views/sale_order_views.xml",
        "views/sale_advance_invoice_views.xml",
        "views/sale_portal_templates.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
}
