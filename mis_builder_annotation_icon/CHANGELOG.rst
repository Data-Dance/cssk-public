=========
Changelog
=========

All notable changes to **mis_builder_annotation_icon** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Upstream
~~~~~~~~

- The same change is proposed to mis_builder itself as OCA/mis-builder#856.
  **When it is merged, uninstall and delete this module**: its template
  extension replaces ``div[@id='dropdown_menu']``, which #856 removes, so on
  a merged mis_builder the xpath finds nothing and the web client's assets
  fail to load.

[19.0.1.0.0] — 2026-11-03
-------------------------

Added
~~~~~

- A note icon replaces the dropdown caret in each MIS Builder report cell. It
  opens the annotation directly, appears on the row under the pointer, stays
  visible and filled when the cell has a note, and is absent on cells that
  cannot be annotated (where mis_builder drew a greyed caret).
