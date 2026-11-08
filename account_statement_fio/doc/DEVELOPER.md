# account_statement_fio: developer notes

Not user documentation: this file is not rendered into a page.

## Design

`bank_statements_source` is a Community field — core declares it with one
entry, `undefined`, and Enterprise's `account_online_synchronization` merely
appends `online_sync` to it — so registering `fio` there costs nothing on
either edition and keeps this module's one-code-path premise.

- **Switching from GPC files to the API does not deduplicate across the two.**
  `account_statement_import_gpc` derives its import key from the GPC record,
  this module from Fio's movement id, and the two cannot be compared. Switch at a
  date boundary: import the last GPC statement, then start the pull the next day.
* A Fio account is single-currency, and each currency is a separate account with
  its own token: set up **one journal per currency account**, in that currency.
  A movement in another currency than the journal's stops the pull with an error
  rather than being booked in the wrong currency.
* A movement made in another currency (a card payment abroad) carries its
  original amount in `column_18` as `20.00 EUR`; that exact shape fills the
  line's `foreign_currency_id` / `amount_currency`. Anything else stays in
  `raw_data`. This needs confirming against a live multi-currency account.
* On Enterprise this brings in two OCA LGPL base modules
  (`account_statement_base`, `account_statement_import_base`) for the import
  key and the partner-matching hooks.
