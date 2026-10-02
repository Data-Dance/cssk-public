=========
Changelog
=========

All notable changes to **account_payment_kb_sepa** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-09-28
-------------------------

Added
~~~~~

- Komerční banka's profile of the OCA pain.001.001.03 SEPA credit transfer,
  for orders paid from a KB account: structured postal address (``StrtNm``,
  ``BldgNb``, ``PstCd``, ``TwnNm``, ``Ctry``; omitted without town and
  country) in place of ``AdrLine``, and the SWIFT character set enforced.
