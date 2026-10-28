=======================================
Received Advance Invoices — Inventory
=======================================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :alt: License: AGPL-3

|badge1|

Bridge between ``purchase_order_advance_invoice`` and ``purchase_stock``,
installed automatically when both are present.

A received advance invoice is a purchase order of its own and is confirmed
when it is paid. With Inventory, Odoo would open a receipt for its stockable
lines, so the same goods would be expected twice. This module stops an
advance from ever creating or updating a receipt (``_create_picking`` and
``_create_or_update_picking`` skip it); the goods are received on the parent
purchase order. The base module cannot do this itself because it does not
depend on ``purchase_stock``.

User documentation: ``static/description/index.html`` (also in Slovak and
Czech).

Credits
=======

* Data Dance s.r.o. — https://www.datadance.eu
