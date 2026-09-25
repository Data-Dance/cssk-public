{
    "name": "Advance Invoices — Bank Statement Matching (OCA Reconcile)",
    "version": "19.0.1.0.0",
    "summary": "Runs the advance-invoice matching inside the OCA "
               "reconciliation widget's auto-reconcile.",
    "description": """
Advance Invoices — Bank Statement Matching (OCA Reconcile)
==========================================================

Plugs ``sale_order_advance_invoice_payment_match`` into OCA
``account_reconcile_oca``: the advance matching pass runs before the OCA
auto-reconcile (reconcile models + invoice matching), so statement lines
paying an advance invoice are matched, paid and reconciled first; they then
show as reconciled in the OCA widget.

Auto-installs when both dependencies are present. The matching itself
remains governed by the company's "Auto-match bank statements" setting.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["sale_order_advance_invoice_payment_match", "account_reconcile_oca"],
    "auto_install": True,
    "installable": True,
}
