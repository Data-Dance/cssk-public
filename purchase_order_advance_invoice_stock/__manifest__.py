# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Received Advance Invoices — Inventory",
    "version": "19.0.1.0.0",
    "summary": "A received advance invoice never creates a receipt; the goods "
               "are received on the purchase order they belong to.",
    "description": """
Received Advance Invoices — Inventory
=====================================

Bridge between ``purchase_order_advance_invoice`` and ``purchase_stock``.

A received advance invoice is registered as a purchase order of its own and
is confirmed when it is paid. With Inventory installed, Odoo would create a
receipt for its stockable lines, so the same goods would be expected twice:
once on the advance and once on the purchase order they were ordered on. The
advance never procures; the goods are received on the parent purchase order,
the mirror of what ``sale_order_advance_invoice`` does for deliveries.

Installs itself when both modules are present.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Inventory/Purchase",
    "depends": ["purchase_order_advance_invoice", "purchase_stock"],
    "auto_install": True,
    "installable": True,
}
