=========
Changelog
=========

All notable changes to **account_mt940_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-09-28
-------------------------

Added
~~~~~

- SWIFT MT940 statement parser for the files Czech banks deliver through
  MultiCash (``*.STA``), written against the Česká spořitelna and
  Raiffeisenbank published layouts:

  - ``utils.mt940.parse_mt940`` — file → ``(currency, account, statements)``
    triplets; several statements and accounts per file; continued statements
    (``:60M:``) folded into one; ``:61:`` booking date and ``RC``/``RD``
    reversals; CP852/CP1250/UTF-8 decoding
  - structured :86: (``?NN`` subfields): VS/KS/SS recognised by prefix, so the
    ČS and RB numberings both work; counterparty account (``?30``/``?31``,
    ``?38`` IBAN) and name (``?32``/``?33``); free-text :86: kept as the label
  - ``utils.mt940.is_mt940`` / ``statement_account``
  - ``tests.mt940_fixtures`` — sample-file builders for both dialects
