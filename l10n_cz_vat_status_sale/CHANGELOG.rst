=========
Changelog
=========

All notable changes to **l10n_cz_vat_status_sale** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[18.0.1.0.1] — 2026-10-19
-------------------------

Fixed
~~~~~

- **The module read a 19.0 field name and so did nothing on 18.0.**
  ``sale.order.line``'s taxes are ``tax_id`` on this series and ``tax_ids`` on
  19.0, and the compute is ``_compute_tax_id`` rather than
  ``_compute_tax_ids`` — so the override extended a method core never calls
  and an order's taxes never followed the company's VAT status. Both
  corrected, along with ``res.users.group_ids`` (``groups_id`` here) in the
  suite's setup.

[19.0.1.0.0] — 2026-09-28
-------------------------

Added
~~~~~

- Sale order lines propose the taxes the company's VAT status allows on the
  order date (``l10n_cz_vat_status``). The document the order produces is
  decided again by its own DUZP.
