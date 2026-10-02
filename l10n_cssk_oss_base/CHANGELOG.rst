=========
Changelog
=========

All notable changes to **l10n_cssk_oss_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Added
~~~~~

- ``cssk.oss.return``: the quarterly OSS VAT return (Union scheme) on core
  ``l10n_eu_oss``. Rows per member state of consumption × rate × goods /
  services, corrections of earlier quarters per member state, per-state
  balances and the total due (positive balances only), export through the
  shared statutory pipeline (kontroly, XSD validation, filed-copy retention,
  delivery tracking).
- EUR conversion at the ECB rate for the quarter's last day or the next day of
  publication (Directive 2006/112/EC Art. 369h(2); CZ § 110ze; SK § 68b ods.
  17), corrections at the corrected quarter's rate. Proposed rates must be
  confirmed as ECB rates before export.
- The Slovak 5 % rate in core's OSS tax mapping, both directions, through a
  scoped overlay of core's map lookup (no core edit); domestic taxes sharing a
  foreign rate are all linked, as in 18.0.
