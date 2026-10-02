=========
Changelog
=========

All notable changes to **l10n_cz_invoice_payment_mode** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-09-28
-------------------------

Added
~~~~~

- *Forma úhrady* in the header of the Czech invoice, from the invoice's
  payment mode (OCA ``account_payment_mode``). Installs itself where both
  ``l10n_cz_invoice`` and ``account_payment_mode`` are installed.
