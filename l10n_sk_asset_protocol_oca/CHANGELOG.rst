=========
Changelog
=========

All notable changes to **l10n_sk_asset_protocol** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.2.0.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- Slovak catalogue completed. Terms already stated in Slovak in the source are
  deliberately left untranslated — the source IS the translation, per the
  hybrid convention for these modules — so an empty ``msgstr`` there is correct
  rather than missing.

[19.0.1.0.0] — 2026-08-05
-------------------------

Added
~~~~~

- Zaraďovací and vyraďovací protokol as QWeb reports on the OCA
  ``account_asset_management`` register.
- Protocol fields on ``account.asset``: inventárne číslo, miesto umiestnenia,
  zodpovedná osoba, poznámka k zaradeniu, dôvod and spôsob vyradenia.
- Inventárne číslo falls back to the register's own code when unset.
- 4 tests, incl. both reports rendering.

[19.0.2.0.0] — 2026-08-07
-------------------------

Changed
~~~~~~~

- Renamed from ``l10n_sk_asset_protocol`` and reduced to a **Community bridge**.
  The Slovak data and the protocol templates moved to
  ``l10n_sk_asset_protocol_base``; what remains here is the mapping of the OCA
  register's field names onto the neutral keys, plus the report bindings.
- The module previously could not install on Enterprise at all. See
  ``l10n_sk_asset_protocol_ee`` for that side.
