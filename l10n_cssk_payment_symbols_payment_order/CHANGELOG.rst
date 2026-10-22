=========
Changelog
=========

All notable changes to **l10n_cssk_payment_symbols_payment_order** are
documented here. Versioning follows the Odoo manifest (``18.0.x.y.z``);
format follows Keep a Changelog.

[Unreleased]
------------

[18.0.1.0.0] — 2026-07-18
-------------------------

Added
~~~~~

- Initial release. Payment lines created from journal items carry the
  document's VS/KS/SS in the structured ``variable_symbol`` /
  ``constant_symbol`` / ``specific_symbol`` fields consumed by the ABO and
  Multicash exporters (explicit value wins over ``VS:``-token parsing).
