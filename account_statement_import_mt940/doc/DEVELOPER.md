# account_statement_import_mt940: developer notes

Not user documentation: this file is not rendered into a page.

## Account matching

- One file, several statements, several accounts — each lands on its journal.
* The journal is found from the `:25:` account **whichever way it is
  written**: Česká spořitelna writes `0800/192000145399`, the journal may
  hold `CZ65 0800 0000 1920 0014 5399` or `19-2000145399/0800`. The OCA
  framework compares sanitized strings and would pair none of these; this
  module compares bank code, prefix and number instead.
* VS/KS/SS land in the statement line's `variable_symbol` /
  `constant_symbol` / `specific_symbol` when `l10n_cssk_payment_symbols`
  is installed, and always as `VS:`-style tokens in the label.
* Counterparty account and name are set on the line, so the partner is found
  from a matching `res.partner.bank`.
* The raw `:61:`/`:86:` text is kept in the line's *Raw data*, the SWIFT
  transaction type in *Transaction type*, the customer reference in *Reference*.
* Re-importing the same statement is refused; a file overlapping an earlier
  import brings in only the new lines.
