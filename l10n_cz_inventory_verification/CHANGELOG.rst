=========
Changelog
=========

All notable changes to **l10n_cz_inventory_verification** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-11-15
-------------------------

Added
~~~~~

- Czech inventarizace under § 29 and § 30 zákona č. 563/1991 Sb.:
  ``l10n.cz.inventarizace`` (periodická or průběžná, with the rozvahový den),
  its inventurní soupisy carrying the particulars of § 30 odst. 7 (both
  responsible persons, způsob zjišťování, rozhodný den, okamžik zahájení a
  ukončení inventury, ocenění) and their items. A dokladová inventura reads
  the account's ledger balance as at the day of valuation. Closing is refused
  while a soupis lacks a prescribed particular, and an inventura outside the
  § 30 odst. 6 window raises a warning. Prints the inventurní soupis and an
  internal inventarizační zápis.
