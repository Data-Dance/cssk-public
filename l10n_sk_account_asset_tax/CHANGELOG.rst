=========
Changelog
=========

All notable changes to **l10n_sk_account_asset_tax** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[18.0.1.1.0] — 2026-11-11
-------------------------

Changed
~~~~~~~

- **§ 52zzzk ZDP** (port of 19.0.1.1.0): the proposed tax entry price leaves
  out the VAT § 85n left undeducted on the asset's bill lines, read when
  ``l10n_sk_vehicle_expense`` is installed.

[19.0.1.0.3] — 2026-07-04
-------------------------

Changed
~~~~~~~

- The Slovak depreciation-group data now supplies the *Tax Depreciation Group*
  axis of the combined book-vs-tax depreciation report added in the
  ``account_asset_tax`` family (Wave 4, 2026-07-04); data-only, no chart change.

[19.0.1.0.2]
------------

Added
~~~~~

- Module icon and README.

[19.0.1.0.1]
------------

Changed
~~~~~~~

- Doc reference updated for the OCA bridge rename (``account_asset_tax_oca``).

[19.0.1.0.0]
------------

Added
~~~~~

- Seven Slovak depreciation groups (0–6); accelerated coefficients for groups 2 & 3,
  verified against zákon 595/2003 Z.z. (2026 consolidated text).
