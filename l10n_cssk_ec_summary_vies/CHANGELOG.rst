=========
Changelog
=========

All notable changes to **l10n_cssk_ec_summary_vies** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.2] — 2026-07-04
-------------------------

Changed
~~~~~~~

- Export-time VIES check hardened alongside the direct-VIES base: a transient
  VIES outage no longer blocks the statutory filing (it is logged in the
  statement chatter for a repeat), while a VAT that VIES reports **invalid** stays
  a hard block on export.
- Snapshot re-apply: the consultation number, check timestamp and validity are
  frozen onto each reported line, so re-opening a filed statement shows exactly
  what was confirmed.

[2026-06-30] — i18n sweep & baseline
------------------------------------

Added
~~~~~

- Glue module (auto-install) linking ``l10n_cssk_ec_summary_base`` ×
  ``l10n_cssk_vies``: makes the EC sales list export perform a **real** direct-VIES
  check (not just a format gate) for companies in direct-VIES mode and snapshot
  the official consultation number onto each line.
- Full cs_CZ + sk_SK translations.
