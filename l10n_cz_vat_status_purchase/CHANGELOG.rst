=========
Changelog
=========

All notable changes to **l10n_cz_vat_status_purchase** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[18.0.1.0.1] — 2026-10-19
-------------------------

Fixed
~~~~~

- **The module read a 19.0 field name and so did nothing on 18.0.**
  ``purchase.order.line``'s taxes are ``taxes_id`` on this series and
  ``tax_ids`` on 19.0, and ``_prepare_purchase_order_line``'s fifth parameter
  is ``supplier`` (a ``product.supplierinfo``) rather than ``partner_id``.
  Both corrected. The compute hook ``_compute_tax_id`` happens to carry the
  same name on both series, which is why nothing failed at install.

Carry-over to 19.0
~~~~~~~~~~~~~~~~~~

- ``_prepare_purchase_order_line``'s command-tuple loop reads only ``6`` and
  ``4``, so a ``5`` (clear), ``3`` or ``2`` is ignored and a bare list of ids
  would raise on ``command[0]``. Core only ever hands it ``[(6, 0, ids)]``
  here, so nothing is broken today. **The loop is 19.0's, unchanged** — this
  port only renamed the key to ``taxes_id`` — so the same gap is on that
  branch and a fix belongs there first, not as a divergence here. Raised by a
  GPT-5.3-Codex review of the port, 2026-10-19.

[19.0.1.0.0] — 2026-09-28
-------------------------

Added
~~~~~

- Purchase order lines propose the taxes the company's VAT status allows on the
  order date (``l10n_cz_vat_status``). The document the order produces is
  decided again by its own DUZP.
