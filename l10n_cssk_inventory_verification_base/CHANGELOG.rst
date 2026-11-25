=========
Changelog
=========

All notable changes to **l10n_cssk_inventory_verification_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- **19.0.1.0.0 (2026-11-24), not yet on 18.0:** the whole module. Port it
  before the two country modules, which depend on it.

[19.0.1.0.0] — 2026-11-24
-------------------------

Added
~~~~~

- Initial release: the settlement lines of an inventory difference, the check
  that they explain the whole difference of a count sheet, the draft journal
  entry dated in the period verified, and its deletion or reversal when the
  record is reopened. Shared by ``l10n_sk_inventory_verification`` and
  ``l10n_cz_inventory_verification``.
- Journal entries of inventory differences refuse to be posted into a locked
  period instead of being moved past the lock date.
