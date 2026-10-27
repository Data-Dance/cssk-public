=========
Changelog
=========

All notable changes to **account_asset_board** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- **19.0.1.0.2 (2026-10-27), not yet on 18.0:** *Remaining Value* is no longer
  a pivot measure (field ``aggregator=None``). 18.0 spells the attribute
  ``group_operator``.

[19.0.1.0.1] — 2026-10-27
-------------------------

Fixed
~~~~~

- **Residual at End** was understated by the salvage value: it is now the net
  book value (acquisition value − closing depreciated value − disposals). For
  an asset removed in the period the disposal is the whole net book value
  that left the register, salvage value included, so its residual is zero.
- **Depreciation Analysis** no longer includes the planned lines of draft
  assets.

[19.0.1.0.2] — 2026-10-27
-------------------------

Fixed
~~~~~

- **Depreciation Analysis** no longer offers *Remaining Value* (OCA's *Next
  Period Depreciation*) as a measure. It is the balance left after each line,
  so the pivot's yearly sum of it was meaningless — with monthly depreciation,
  twelve balances added together.

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
