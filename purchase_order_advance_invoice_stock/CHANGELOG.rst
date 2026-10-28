=========
Changelog
=========

All notable changes to **purchase_order_advance_invoice_stock** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[19.0.1.0.0] — 2026-10-27
-------------------------

Added
~~~~~

- Initial release. With Inventory installed, a received advance invoice no
  longer creates a receipt when it is paid or confirmed, or when a line is
  added or a quantity raised afterwards. The goods are received once, on the
  parent purchase order.
