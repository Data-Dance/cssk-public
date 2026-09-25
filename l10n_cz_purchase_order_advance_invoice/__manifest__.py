{
    "name": "Czech Republic — Received Advance Invoices",
    "version": "19.0.1.0.0",
    "summary": "Czech chart wiring for purchase_order_advance_invoice.",
    "description": """
Czech Republic — Received Advance Invoices
==========================================

Wires the statutory Czech accounts and journal for the received
advance-invoice flow: creates the reconcilable clearing account **314001**,
maps net paid advances to **314000** and creates the **PDADV** purchase
journal for the suppliers' tax documents on sent payments.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["purchase_order_advance_invoice", "l10n_cz"],
    "post_init_hook": "_l10n_cz_purchase_advance_post_init",
    "installable": True,
}
