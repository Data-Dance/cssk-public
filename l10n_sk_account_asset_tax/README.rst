======================================
Tax Depreciation - Slovak Localization
======================================

Loads the seven Slovak tax-depreciation groups (odpisové skupiny 0–6) with the
straight-line regime (§27, monthly pro-rata in the first year) and the
accelerated coefficients (§28, groups 2 & 3 only), verified against the 2026
consolidated text of zákon č. 595/2003 Z. z. (§26–28).

This is the **Slovak data layer** for the ``account_asset_tax`` framework. It is
data-only; install a framework bridge (``account_asset_tax_ee`` for Enterprise or
``account_asset_tax_oca`` for OCA/Community) to attach the tax-depreciation board
to actual assets.

Features
========

* Seven Slovak depreciation groups (0–6) as ready-to-use data.
* §27 straight-line regime with monthly pro-rata in the first year.
* §28 accelerated coefficients for groups 2 & 3.
* Verified against the 2026 consolidated text of zákon č. 595/2003 Z. z.

Usage
=====

Install this module together with the core ``account_asset_tax`` and one bridge
(``account_asset_tax_ee`` / ``account_asset_tax_oca``). The Slovak groups then
become available when assigning the tax-depreciation group and method on an
asset's tax board.

Documentation
=============

* ``CHANGELOG.md`` — release history.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
