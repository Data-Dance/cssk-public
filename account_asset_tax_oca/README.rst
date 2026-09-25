=============================
Tax Depreciation — OCA bridge
=============================

Wires the country-neutral ``account_asset_tax`` core onto OCA
``account_asset_management`` (Community): the non-posted tax-depreciation board,
the asset ↔ tax-line/event relations, the *Tax Depreciation* page, the
removal-wizard disposal hook (``state='removed'``), the deferred-tax
accounting-residual reader, and tax-default inheritance from the asset profile.

Install with the core, a country data layer and — mutually exclusive — NOT the
Enterprise bridge.

Validated on Odoo 19 Community (19CE-TEST): 11 integration tests green.

Documentation
=============

* ``CHANGELOG.md`` — release history.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3 (see the LICENSE file).
