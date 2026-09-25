=========
Changelog
=========

All notable changes to **l10n_cssk_payment_symbols_payment_order** are
documented here. Versioning follows the Odoo manifest (``19.0.x.y.z``);
format follows Keep a Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- Relicensed from ``Other proprietary`` to **AGPL-3**. The module depends on
  the OCA ``account_payment_order``, which is AGPL-3 and third-party
  copyright, so a proprietary licence on a module deriving from it was not
  sustainable.

[19.0.1.0.0] — 2026-07-18
-------------------------

Added
~~~~~

- Initial release. Payment lines created from journal items carry the
  document's VS/KS/SS in the structured ``variable_symbol`` /
  ``constant_symbol`` / ``specific_symbol`` fields consumed by the ABO and
  Multicash exporters (explicit value wins over ``VS:``-token parsing).
