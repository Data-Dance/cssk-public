=========
Changelog
=========

All notable changes to **l10n_cz_sale_order_advance_invoice** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[19.0.1.0.0]
------------

- Initial Czech localization of ``sale_order_advance_invoice``: post_init hook
  wiring the advance-invoice journal and accounts to the Czech chart
  (324001 clearing [created], 324000 short-term, 475000 long-term).
