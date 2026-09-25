=========
Changelog
=========

All notable changes to **l10n_sk_asset_protocol_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.4] — 2026-09-13
-------------------------

Fixed
~~~~~

- The module's own model name and the inventárne číslo help text had no
  Slovak. Both now do.

[19.0.1.0.3] — 2026-09-13
-------------------------

Fixed
~~~~~

- **The model's own name was never exported.** ``_description`` is what
  labels a record's type in breadcrumbs and the technical model list, and
  ``tools/i18n_export_offline.py`` emitted no ``model:ir.model,name:`` line
  at all — the entries already in the catalogues had come from an older
  DATABASE export. So every model added since had no entry and its name
  could not be translated. The exporter now emits it, and the missing
  entries are merged and filled.

[19.0.1.0.2] — 2026-09-13
-------------------------

Fixed
~~~~~

- **A field label was being INVENTED, not missing.** ``fields.Float("Night
  work %", ...)`` passes ``string`` positionally, and
  ``tools/i18n_export_offline.py`` read it from keyword arguments only — so it
  fell back to deriving a label from the field name and wrote "Noc Pct" into
  the catalogue where Odoo's own export writes "Night work %". Every
  translation keyed to the derived form was therefore keyed to a msgid the
  runtime never looks up: present, valid, and dead.
- The exporter now reads the positional slot, which differs per field type
  (``Many2one`` puts ``comodel_name`` first, ``One2many`` two arguments,
  ``Many2many`` four, ``Selection`` its selection). Positional ``selection``
  lists are extracted too, which is where the stupne-náročnosti and VRP2
  receipt-state labels had been going missing entirely.
- Catalogues regenerated against the corrected msgids and re-translated.

[19.0.1.0.1] — 2026-09-13
-------------------------

Added
~~~~~

- **Slovak catalogue — the module had none.** Generated with
  ``tools/i18n_export_offline.py`` (no database is available here) and verified
  back through Odoo's own ``PoFileReader``, so every entry resolves to the
  record it belongs to rather than importing as code strings only.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

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
