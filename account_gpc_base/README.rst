====================================
GPC Statement Format — shared parser
====================================

The single source of truth for the Czech/Slovak **GPC** bank-statement format
(the ABO electronic statement used by Fio, KB, ČS, ČSOB and the rest).

Both import shims build on it, so the record layout is implemented once:

* ``account_statement_import_gpc`` — Community, OCA ``account.statement.import``
* ``account_statement_import_gpc_ee`` — Enterprise, ``account_bank_statement_import``

There are **no Odoo models** here — only pure helpers, imported via
``odoo.addons.account_gpc_base.utils.gpc``.

Features
========

* ``parse_gpc(data_file, with_symbols=False)`` — parses the file into the
  ``(currency_code, account_number, stmts_vals)`` triplets both frameworks
  consume. ``with_symbols`` adds ``variable_symbol`` / ``constant_symbol`` /
  ``specific_symbol`` to each transaction; pass it only when a module providing
  those fields on ``account.bank.statement.line`` is installed.
* ``is_gpc(data_file)`` — cheap format sniff, for the Enterprise framework's
  chain-of-responsibility parser lookup.
* ``tests.gpc_fixtures`` — ``rec074`` / ``rec075`` / ``gpc_bytes`` / ``gpc_file``
  record builders, so both shims assert against byte-identical sample files.

Records handled
===============

Fixed 130-character records, values zero-padded from the left: ``074`` header,
``075`` transaction, ``076``/``078``/``079`` message (AV) extensions. Anything
else is ignored — banks append proprietary records.

Credits
=======

Author: Data Dance s.r.o. — https://www.datadance.eu
