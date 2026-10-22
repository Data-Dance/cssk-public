=========
Changelog
=========

All notable changes to **l10n_sk_jcd** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-08-05
-------------------------

Added
~~~~~

- Baseline: ``l10n.sk.jcd``, the Slovak import customs declaration as an accounting
  document — colná hodnota, clo, iné colné poplatky, VAT base and rate, regime,
  links to the supplier invoices and the goods receipts.
- Duty capitalised into stock value via ``stock.landed.cost``.
- Import VAT posted through the ``l10n_sk`` core taxes, so the existing tag-driven
  VAT return reports it with no new engine: ``vs_cust_*`` → r22/r22a/r23,
  ``vs_imp_post_*`` → r11c–e / r12c–e / r23a–c.
- **Deduction gate**: posting is refused without an MRN and an attached customs
  document (DPHv25 poučenie bod 38, § 49 ods. 2 písm. d)).
- Notional base posted +/- on a clearing account so only VAT and duty are real.
- Clearing account (379000) and duty product wired from the chart template for new
  SK companies, and by a post-init hook for existing ones.
- 12 tests, incl. exact DPH tag assertions for both regimes and duty reaching the
  stock valuation.

Notes
~~~~~

- Two Odoo 19 differences hit while building: ``mail.thread`` no longer has
  ``message_main_attachment_id`` (so the customs-document check is evaluated on
  read, not via ``@depends``), and ``stock.move`` has no ``name`` field
  (``_rec_name = 'reference'``).
- Landed costs are only permitted on FIFO/AVCO categories; duty capitalisation does
  not apply to standard-cost products.
