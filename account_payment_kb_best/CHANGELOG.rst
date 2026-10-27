=========
Changelog
=========

All notable changes to **account_payment_kb_best** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.1.0] — 2026-10-27
-------------------------

Added
~~~~~

- Priority and Charge Bearer on the payment line, read by the domestic and
  foreign BEST records. They used to be read from fields no Community module
  defines, so every payment was normal priority with shared charges.

[19.0.1.0.0] — 2026-09-28
-------------------------

Added
~~~~~

- Komerční banka BEST payment files on the OCA payment order: domestic
  transfers and direct debits (``01``), foreign and SEPA transfers (``02`` +
  ``03``), with VS/KS/SS per payment line. ``Sekv_No`` comes from the payment
  line id, so it stays unique across every file sent in a day.
