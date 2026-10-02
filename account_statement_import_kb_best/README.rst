===============================
Bank Statement Import — KB BEST
===============================

Imports Komerční banka **BEST** electronic statements — the ``*.OKM`` /
``*.KMO`` export of MojeBanka Business, Profibanka and Přímý kanál — through
the OCA ``account.statement.import`` wizard. The record layout and the
specification it follows are described in ``account_kb_best_base``.

Features
========

* One statement per account and booking day, with opening and closing balance
  from the turnover record; several days and accounts per file.
* Accounting transactions (``52``) become statement lines; non-accounting
  ones (``53``, loan interest and fee instalments) do not touch the balance
  and are skipped.
* VS/KS/SS land in ``variable_symbol`` / ``constant_symbol`` /
  ``specific_symbol`` when ``l10n_cssk_payment_symbols`` is installed, and
  always as ``VS:``-style tokens in the label; counterparty account and name
  are set, so the partner is found from a matching bank account.
* KB's own posting identifier (``KBI_ID``) is part of the import key, so a
  re-import is refused and an overlapping file brings in only what is new.
* The journal is found whether it holds the account as IBAN or as
  ``prefix-number/0100``.

Credits
=======

Author: Data Dance s.r.o. — https://www.datadance.eu
