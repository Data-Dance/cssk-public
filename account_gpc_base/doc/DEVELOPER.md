# account_gpc_base: developer notes

Not user documentation: this file is not rendered into a page.

## API

- `parse_gpc(data_file, with_symbols=False)` — parses the file into the
  `(currency_code, account_number, stmts_vals)` triplets both frameworks
  consume. `with_symbols` adds `variable_symbol` / `constant_symbol` /
  `specific_symbol` to each transaction; pass it only when a module providing
  those fields on `account.bank.statement.line` is installed.
* `is_gpc(data_file)` — cheap format sniff, for the Enterprise framework's
  chain-of-responsibility parser lookup.
* `tests.gpc_fixtures` — `rec074` / `rec075` / `gpc_bytes` / `gpc_file`
  record builders, so both shims assert against byte-identical sample files.

Fixed 130-character records, values zero-padded from the left: `074` header,
`075` transaction, `076`/`078`/`079` message (AV) extensions. Anything
else is ignored — banks append proprietary records.
