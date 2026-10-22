=========
Changelog
=========

All notable changes to **currency_rate_update_cz** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Česká národní banka (ČNB) daily fixing registered as a
  ``res.currency.rate.provider`` for the OCA ``currency_rate_update`` framework.
- CE-compatible: no Enterprise ``currency_rate_live`` dependency.
- Parses the ČNB ``Amount|Currency|Code|Rate`` feed; for a CZK-base company the
  stored rate is ``Amount / Rate`` (foreign per CZK), e.g. ``1|EUR|24.170`` → 1/24.170
  and ``100|JPY|13.043`` → 100/13.043.
- Licensed AGPL-3, matching the ``currency_rate_update`` framework it derives from.
