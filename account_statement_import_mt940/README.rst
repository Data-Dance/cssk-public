==============================================
Bank Statement Import — MT940 / MultiCash (CZ)
==============================================

Imports **SWIFT MT940** bank statements — the ``*.STA`` files MultiCash writes,
and the same layout from X-business and Business 24 — through the OCA
``account.statement.import`` wizard (*Accounting ▸ Bank ▸ Import*). CE-clean:
no Enterprise dependency. The parser, and the notes on which bank layout it
follows, live in ``account_mt940_base``.

This is the statement half of MultiCash; the payment half (CFD/CFU/CFA/MT101
export) is ``account_multicash``.

Features
========

* One file, several statements, several accounts — each lands on its journal.
* The journal is found from the ``:25:`` account **whichever way it is
  written**: Česká spořitelna writes ``0800/192000145399``, the journal may
  hold ``CZ65 0800 0000 1920 0014 5399`` or ``19-2000145399/0800``. The OCA
  framework compares sanitized strings and would pair none of these; this
  module compares bank code, prefix and number instead.
* VS/KS/SS land in the statement line's ``variable_symbol`` /
  ``constant_symbol`` / ``specific_symbol`` when ``l10n_cssk_payment_symbols``
  is installed, and always as ``VS:``-style tokens in the label.
* Counterparty account and name are set on the line, so the partner is found
  from a matching ``res.partner.bank``.
* The raw ``:61:``/``:86:`` text is kept in the line's *Raw data*, the SWIFT
  transaction type in *Transaction type*, the customer reference in *Reference*.
* Re-importing the same statement is refused; a file overlapping an earlier
  import brings in only the new lines.

Usage
=====

In MultiCash, statements are written to ``MCCWIN`` (v3.x) or ``DATA`` (v4.x)
as ``*.STA``. Upload the file from the bank journal's *Import* button, or from
*Accounting ▸ Bank ▸ Import* to let the file's account pick the journal.

Credits
=======

Author: Data Dance s.r.o. — https://www.datadance.eu
