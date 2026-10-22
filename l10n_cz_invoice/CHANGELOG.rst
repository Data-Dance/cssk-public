=========
Changelog
=========

All notable changes to **l10n_cz_invoice** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[18.0.1.0.1] — 2026-09-17
-------------------------

Fixed
~~~~~

- **``l10n_cssk_payment_symbols`` is now a declared dependency.** The module
  reads and writes the VS/KS/SS fields (``l10n_cssk_variable_symbol`` and
  siblings) but only received them transitively, through
  ``l10n_cssk_core``, which depended on the symbols module solely because
  the fields used to live there. Declaring it directly lets that legacy
  dependency be dropped from core without breaking this module.

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Czech statutory invoice content on top of core + ``l10n_cz``: customer DIČ (from
  ``l10n_cssk_core``), payment symbols (variabilní / konstantní / specifický symbol).
- Auto-detected statutory phrases: domestic reverse charge (§92a), intra-Community supply (§64),
  export (§66), plus a free-text manual note.
- cs_CZ jsonb translations (i18n sweep, 2026-06-30).
