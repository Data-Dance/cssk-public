---
title: Received Advance Invoices — Inventory
summary: A received advance invoice never creates a receipt; the goods are received on the purchase order they were ordered on.
verified: 19.0.1.0.0
family: purchase_order_advance_invoice#register
---

A received advance invoice of
[module:purchase_order_advance_invoice](module:purchase_order_advance_invoice)
is a purchase order of its own, and paying it confirms it. With Inventory
installed, Odoo would then create a receipt for its stockable products, and
the same goods would be expected twice: on the advance and on the purchase
order they were ordered on.

With this add-on an advance never creates a receipt — not when it is paid,
not when it is confirmed by hand, and not when a line is added or a quantity
raised afterwards. Receive the goods on the **parent purchase order**, as
usual. Ordinary purchase orders are not affected.

It installs itself when
[module:purchase_order_advance_invoice](module:purchase_order_advance_invoice)
and Inventory (`purchase_stock`) are both installed. There is nothing to set
up.
