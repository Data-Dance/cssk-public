=========
Changelog
=========

All notable changes to **l10n_sk_asset_protocol** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- **19.0.2.0.3 (2026-10-27), not yet on 18.0:** amounts that foot (salvage
  value, removal line) and the regenerated Slovak catalogue.

[19.0.2.0.2] — 2026-10-27
-------------------------

Fixed
~~~~~

- Printing *Protokol o zaradení majetku* and *Protokol o vyradení majetku*
  failed: the print actions still named the templates of the removed module
  ``l10n_sk_asset_protocol``. They now print the shared templates of
  ``l10n_sk_asset_protocol_base``.

[19.0.2.0.3] — 2026-10-27
-------------------------

Fixed
~~~~~

- **Zostatková cena ignored the salvage value**, so purchase value − oprávky
  did not give the printed residual; it is now the net book value.
- **After removal the disposal protocol printed oprávky of the whole
  depreciation base and a zostatková cena of nil**, because OCA counts the
  removal line as depreciated. The oprávky are now the posted depreciation
  lines only, and the zostatková cena is what was written off.
- The protocol fields and the tab are translated into Slovak (the catalogue
  was keyed to the module's old name and never loaded).

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
