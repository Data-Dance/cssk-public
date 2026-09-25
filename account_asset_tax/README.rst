================================================
Tax Depreciation (CZ/SK dual depreciation core)
================================================

Country-neutral core for **dual depreciation** — the parallel *tax* depreciation
plan (daňové odpisy) that Czech and Slovak income-tax law requires alongside the
posted *accounting* depreciation plan (účetní / účtovné odpisy).

The tax plan is **never posted to the general ledger**; it only adjusts the
income-tax base (DPPO line 150 add-back / line 250 deduction). This module keeps
it as a non-posted board computed by a pure-Python engine.

Architecture
============

::

    account_asset_tax            core: models + engine + mixin + cheat sheet
      ├── account_asset_tax_ee           bridge → Odoo EE account_asset
      └── account_asset_tax_oca     bridge → OCA account_asset_management (CE)
    l10n_cz_account_asset_tax    Czech groups & coefficients (§31/§32/§30a)
    l10n_sk_account_asset_tax    Slovak groups & coefficients (§27/§28)

Install **core + one bridge + the country data layer(s)**. The two bridges are
mutually exclusive (only one ``account.asset`` implementation can be installed).

Why a separate engine
=====================

All statutory maths lives in ``engine/depreciation.py`` with **no Odoo import**,
so it is unit-tested in isolation (``tests/test_engine.py``, runnable with plain
``python3``) and reused unchanged by both bridges, which differ only in *where*
they read the entry value and in-service date.

See ``docs/tax_depreciation_cheat_sheet.rst`` (rendered in
``static/description``) for worked examples of every group and method.

Wizards
=======

* **Compute Tax Depreciation Boards** — batch (re)computation of the tax board
  for a selection of assets.
* **Backfill Tax Depreciation** — set up the tax board on an asset already part
  way through its life (opening accumulated tax depreciation).
* **Tax Depreciation Event Wizard** — record a lifecycle event (technical
  improvement / suspension / disposal) and re-plan the board from that point.
* **Close Tax Depreciation Year** — freeze the board up to a filed fiscal year so
  later edits cannot change an already-submitted DPPO.
* **Tax Depreciation Reconciliation (DPPO)** — accounting-vs-tax reconciliation
  for a fiscal period: computes the §23 add-back/deduction, optionally posts the
  deferred-tax entry, and exports XLSX / PDF.

Documentation
=============

* ``docs/tax_depreciation_cheat_sheet.rst`` — worked examples of every CZ/SK
  group and method (also rendered as an interactive page in ``static/description``).
* ``CHANGELOG.md`` — release history.

Status
======

Engine + golden tests: done and green. The Odoo layer (models, mixin, views) is
static-validated; run ``-i account_asset_tax_ee l10n_sk_account_asset_tax`` (or
the OCA bridge) in a dev database to confirm registry/view loading.
