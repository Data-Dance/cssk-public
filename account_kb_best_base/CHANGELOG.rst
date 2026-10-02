=========
Changelog
=========

All notable changes to **account_kb_best_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-09-28
-------------------------

Added
~~~~~

- Komerční banka **BEST** client format, written against KB's published
  specification (valid from 20 June 2026) and checked against its sample
  files:

  - ``utils.best.build_best_domestic`` — domestic úhrady and inkasa (``01``)
  - ``utils.best.build_best_foreign`` — foreign and SEPA payments (``02``)
    with the ``03`` structured address introduced on 20 June 2026
  - ``utils.best.parse_best_statement`` / ``is_best_statement`` — the
    electronic statement (``51``/``52``; ``53`` skipped)
  - ``tests.best_fixtures`` — statement-record builders
