{
    "name": "Purchase Order Advance Invoice",
    "version": "19.0.1.1.0",
    "summary": "Received advance invoices (vendor proformas) with tax "
               "documents on sent payments",
    "description": """
Received Advance Invoices
=========================

Country-neutral engine for the RECEIVED advance-invoice / proforma flow used
in Czech and Slovak accounting (přijatá zálohová faktura / prijatá
preddavková faktúra) — the purchase-side mirror of
``sale_order_advance_invoice``:

* The received proforma is registered as its own **purchase order** (own
  ``PADV`` sequence) — never posted, as the law requires; optionally linked
  to a parent purchase order.
* **Paying it** books Dr 314-clearing / Cr bank via a real outbound payment
  (wizard, or link an existing payment).
* The supplier's **tax document on the received payment** (daňový doklad k
  přijaté platbě / faktúra k prijatej platbe) is registered by wizard as a
  draft vendor bill in a dedicated purchase journal: net amount on the
  advances account (314000 / long-term variant), the payable leg rewritten
  to the reconcilable clearing account, the supplier's document number
  mandatory in ``ref`` (it must go to KH B.2 / KV B.2 verbatim), taxable
  supply date = payment date, accounting date freely editable (deduction
  period ≠ tax point). Posting reconciles the clearing legs automatically.
* **Settlement**: bills created from the parent purchase order deduct its
  paid advances automatically; standalone advances are deducted on any
  draft vendor bill via the "Link Advance Invoices" wizard. With a posted
  tax document the deduction is net + taxes (input-VAT reversal); without,
  it is gross without taxes.
* An activity chases the supplier when the tax document is overdue
  (15 days / end of month after payment).

Install a localization layer to wire the statutory accounts automatically:
``l10n_cz_purchase_order_advance_invoice`` / ``l10n_sk_purchase_order_advance_invoice``.

Reverse-charge / intra-EU advances are out of scope: an advance payment
creates no tax point there — register no tax document for them.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Inventory/Purchase",
    "depends": ["purchase", "account"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "data/ir_cron_data.xml",
        "wizard/purchase_advance_payment_wizard_views.xml",
        "wizard/purchase_advance_payment_link_wizard_views.xml",
        "wizard/purchase_advance_tax_doc_wizard_views.xml",
        "wizard/account_move_link_purchase_advance_wizard_views.xml",
        "views/purchase_order_views.xml",
        "views/account_move_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
}
