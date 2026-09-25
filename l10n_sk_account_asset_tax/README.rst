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

Intangible assets have no depreciation group
============================================

Seven groups is the whole set, and the absence is deliberate rather than
unfinished: **nehmotný majetok is not assigned to an odpisová skupina at all.**

§ 22 ods. 8 zákona 595/2003 has intangible assets tax-depreciated *in accordance
with the accounting rules* — daňové odpisy equal účtovné odpisy, up to the
vstupná cena — because the groups in Príloha č. 1 classify **tangible** assets
by their KP/CPA code. There is nothing to classify an intangible into.

So for an asset on 012 Aktivované náklady na vývoj, 013 Softvér, 014 Oceniteľné
práva, 015 Goodwill or 019 Ostatný DNM, an empty ``tax_class_id`` is the
**correct final state**, not a gap waiting to be filled, and its tax
depreciation comes from the accounting schedule rather than from a group. An
importer that expects every asset to resolve a group will report the right
answer as a problem, once per intangible asset.

Written down because the absence is silent: the data ships seven groups and
says nothing about the case it excludes, and it has been inferred backwards
more than once — from an asset's accounting life (a 48-month write-off looking
like group 1's four years) rather than from what the asset is.

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
