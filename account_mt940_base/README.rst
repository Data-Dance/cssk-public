===================================================
MT940 / MultiCash Statement Format — shared parser
===================================================

The single source of truth for **SWIFT MT940** bank statements as Czech banks
deliver them to accounting — through MultiCash (``*.STA`` files), X-business and
Business 24, all of which write the same MT940 layout.

There are **no Odoo models** here — only pure helpers, imported via
``odoo.addons.account_mt940_base.utils.mt940``. The Community import shim is
``account_statement_import_mt940``.

Why a Czech parser at all
=========================

The SWIFT part of MT940 is the same everywhere. Field :86: ("information to
account owner") is not, and it is the field that carries everything a Czech
accountant matches on: the **VS/KS/SS** payment symbols, the counterparty
account and name, the remittance text. Czech banks write it as ``?NN``
subfields, and they do not agree on the numbering:

============  ================================  ================================
subfield      Česká spořitelna (MultiCash 3.2)  Raiffeisenbank (MT940 v2–v4)
============  ================================  ================================
``?20``       ``KS:308``                        posting text
``?21``       ``VS:23568``                      ``KS0000000308``
``?22``       ``SS:4523``                       ``VS0045135784``
``?23``       counterparty ``bank/account``     ``SS0001234578``
empty value   ``.``                             ``-`` (or omitted)
============  ================================  ================================

So the parser recognises a symbol by its **prefix**, never by the subfield it
sits in. What both banks do share — ``?30`` counterparty bank code or BIC,
``?31`` account, ``?38`` IBAN, ``?32``/``?33`` name, ``?00`` posting text,
``?20``–``?29`` and ``?60``–``?63`` remittance — is the German structured-:86:
convention both inherited, and that is what the mapping relies on. An :86:
without ``?NN`` subfields is kept as free text, with ``VS:``-style tokens still
picked out of it.

Features
========

* ``parse_mt940(data_file, with_symbols=False)`` — the file into
  ``(currency_code, account_number, stmts_vals)`` triplets, one per currency
  and account. ``with_symbols`` adds ``variable_symbol`` / ``constant_symbol``
  / ``specific_symbol`` to each transaction.
* Several statements per file (several days, several accounts); a statement
  continued over several messages (``:60M:`` opening, same ``:28C:`` number) is
  folded back into one.
* ``:61:`` with the optional MMDD booking date (its year taken from the value
  date, across a year boundary if need be) and the ``RC``/``RD`` reversal marks.
* Encoding: UTF-8 when it decodes, else CP852 (what both MultiCash specs
  prescribe) or CP1250, whichever yields more Czech letters.
* ``statement_account`` — the :25: account as ``prefix-number/bank`` or IBAN.
* ``tests.mt940_fixtures`` — sample-file builders for both dialects.

Specifications
==============

Written against the banks' published documents only (fetched 2026-09-28):

* Česká spořitelna — *MultiCash 3.2: Popis formátu výpisu MT940*,
  https://www.csas.cz/content/dam/cz/csas/www_csas_cz/dokumenty/produkty/podnikatele-a-firmy/ucty-a-platby/internetove-bankovnictvi/produktova-stranka/multicash/MCC_popis_formatu_vypisu_MT940.pdf
* Česká spořitelna — *Technický popis struktury formátu výpisu MT940 pro službu
  Business 24* (states it is identical to the MultiCash one),
  https://www.csas.cz/banka/content/inet/internet/cs/MT940_B24.pdf
* Raiffeisenbank — *Formát MT940, výpisy verze 4 pro aplikaci MultiCash a
  X-business* (v1.5, 2019-05-28),
  https://www.rb.cz/attachments/elektronicke-bankovnictvi/27804-RFB-Format-MT940.pdf
* Raiffeisenbank — *MultiCash / X-business: napojení na účetní systémy*
  (MT940 v2 and v3),
  https://www.rb.cz/attachments/elektronicke-bankovnictvi/multicash-struktura-dat.pdf

Other banks' MT940 (KB, ČSOB, UniCredit, Citibank …) parse through the same
SWIFT fields, but their :86: has not been checked against a published layout;
with a free-text :86: the label is the text as given.

Not the OCA parser
==================

OCA's generic ``account_bank_statement_import_mt940_base``
(``OCA/bank-statement-import``) was last released for **11.0** and never
ported; its 19.0 successors are country modules — the Romanian
``l10n_ro_account_bank_statement_import_mt940_base`` depends on
``l10n_ro_config`` — so nothing on 19.0 was reusable without dragging a foreign
localization in. This is a fresh implementation against the specifications
above, not a port.

Credits
=======

Author: Data Dance s.r.o. — https://www.datadance.eu
