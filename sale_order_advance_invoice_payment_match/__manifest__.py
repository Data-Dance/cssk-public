{
    "name": "Advance Invoices — Bank Statement Matching",
    "version": "19.0.1.0.0",
    "summary": "Match incoming bank statement lines to advance invoices by "
               "variable symbol and register the payment automatically.",
    "description": """
Advance Invoices — Bank Statement Matching
==========================================

An issued advance invoice (``sale_order_advance_invoice``) has no posted
journal entry until it is paid, so no stock reconciliation engine can ever
match an incoming bank transaction to it. This module closes that gap:

* **Matching** — statement lines are matched against open advances by the
  advance number (``ADV00042``) or its digits/variable symbol; leading-zero
  tolerant; prefers a ``variable_symbol`` field on the statement line when
  one exists (``l10n_cssk_payment_symbols`` or upstream odoo/odoo#275611 —
  duck-typed, no hard dependency). Ambiguity bails out; a digits-only match
  is only auto-applied when the amount equals the open remainder.
* **Applying** — reuses the module's proven manual-payment path: a real
  ``account.payment`` to the advance clearing account is created and
  posted, its outstanding leg is reconciled against the statement line's
  suspense leg, and the payment is wrapped in the offline transaction that
  drives the advance's payment/accounting statuses.
* **Tax document** — company setting: on payment, leave the advance
  "waiting" (default), create the tax document as draft, or create and
  post it (the clearing account then nets to zero automatically).
* **Triggers** — a cron (opt-in per company) processes unreconciled
  statement lines; a "Match Advance Invoice" wizard is available on
  statement lines for manual use in any edition. An Enterprise shim
  (``..._payment_match_ee``) plugs the same matching into the bank
  reconciliation widget's auto-flow.

Limitations (v1): inbound single-currency transactions only (statement,
advance and company currency must agree); the payment journal needs an
inbound payment method with an outstanding receipts account.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["sale_order_advance_invoice"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron_data.xml",
        "wizard/advance_statement_match_wizard_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
}
