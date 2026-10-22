=========
Changelog
=========

All notable changes to **l10n_sk_asset_protocol_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-08-07
-------------------------

Added
~~~~~

- Split out of ``l10n_sk_asset_protocol``, which could only ever install on
  Community: it depended on OCA ``account_asset_management``, whose manifest
  carries ``excludes: ["account_asset"]``.
- ``l10n.sk.asset.protocol.mixin`` holding the Slovak data (inventárne číslo,
  miesto umiestnenia, zodpovedná osoba, dôvod a spôsob vyradenia) as an
  AbstractModel, so the base touches neither asset engine.
- One set of QWeb templates for both protocols, rendering from an engine-neutral
  values dict that each bridge fills from its own field names.
