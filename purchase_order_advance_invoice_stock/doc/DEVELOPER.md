# purchase_order_advance_invoice_stock: developer notes

Not user documentation: this file is not rendered into a page.

## Implementation

A received advance invoice is a purchase order of its own and is confirmed
when it is paid. With Inventory, Odoo would open a receipt for its stockable
lines, so the same goods would be expected twice. This module stops an
advance from ever creating or updating a receipt (`_create_picking` and
`_create_or_update_picking` skip it); the goods are received on the parent
purchase order. The base module cannot do this itself because it does not
depend on `purchase_stock`.
