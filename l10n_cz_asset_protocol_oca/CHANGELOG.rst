=========
Changelog
=========

All notable changes to **l10n_cz_asset_protocol_oca** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-11-15
-------------------------

Added
~~~~~

- Community bridge of the Czech asset protocols: the tab *Protokoly (CZ)* on
  the OCA ``account_asset_management`` asset form and the print entries
  *Protokol o zařazení majetku* and *Protokol o vyřazení majetku*, filled from
  the OCA register. Oprávky are the posted depreciation lines only and the
  zůstatková cena is the purchase value less oprávky, so the amounts foot
  with a salvage value and after removal. The inventární číslo falls back to
  the register's reference.
