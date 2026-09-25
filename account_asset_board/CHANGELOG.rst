=========
Changelog
=========

All notable changes to **account_asset_board** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Initial release (AGPL-3): gives Odoo Community an interactive asset
  depreciation board comparable to Enterprise's *Depreciation Schedule*, on top
  of OCA ``account_asset_management`` (which only ships a static XLSX report).
- **Depreciation Schedule** — OWL client action rendering an EE-style dynamic
  schedule for a chosen date range (default: current fiscal year). One row per
  asset grouped by asset profile with subtotals and a grand total; columns
  acquisition value, opening depreciated value, depreciation in period,
  disposals in period, closing depreciated value and closing residual. Asset
  rows are clickable and open the asset form; profile groups fold/unfold.
- **Depreciation Analysis** — pivot/graph views over the depreciation lines
  (``account.asset.line``, type *depreciate*): rows per asset, columns per year,
  measures *Amount* and *Remaining Value*, with Posted/Planned filters and
  asset / profile / year group-bys.
- Disposal semantics: the *Disposals* column reads the residual written off by
  the OCA removal wizard (the ``remove``-type line); if a removed asset has no
  such line, the undepreciated remainder (base − closing) is used instead.
- Both screens under *Accounting → Assets*.
