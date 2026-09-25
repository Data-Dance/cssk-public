=========
Changelog
=========

All notable changes to **l10n_cssk_intrastat_footprint** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.1.0] — 2026-09-13
-------------------------

Added
~~~~~

- The statutory footprint now names the FILING each row belongs to. This
  contributor is the one that needs no resolution: it reaches the row THROUGH
  the declaration, so it passes ``res_model`` **and** ``res_id`` and
  ``l10n_cssk_core`` uses the record as given rather than looking for it again.
