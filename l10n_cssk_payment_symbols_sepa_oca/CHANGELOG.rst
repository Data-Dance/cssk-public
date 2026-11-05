=========
Changelog
=========

All notable changes to **l10n_cssk_payment_symbols_sepa_oca** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-11-04
-------------------------

Added
~~~~~

- **VS, KS and ŠS in the SEPA credit transfer file of OCA payment orders.**
  On Odoo Community the file carried no structured symbols: the end-to-end
  identifier was the line's id and the message only the bill reference. A
  bank journal option chooses where they go: the end-to-end identifier as
  ``/VS…/SS…/KS…`` (the Slovak banks' structure, default for Slovak
  companies), the remittance information as ``/VS/…/KS/…/SS/…`` (default for
  Czech companies) or nowhere (default elsewhere).
- With symbols exported, bills with different symbols are paid by separate
  transfers; other orders group as OCA does.
