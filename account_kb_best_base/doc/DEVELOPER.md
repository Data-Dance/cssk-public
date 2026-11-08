# account_kb_best_base: developer notes

Not user documentation: this file is not rendered into a page.

## What the builders enforce

Each rule is the specification's, not a guess:

* The debited account must be a KB account (bank code `0100`).
* `Sekv_No` must be unique for the client **per creation day across every
  file** — it is taken from the payment line's database id (base 36), because a
  per-file counter would collide with the morning's batch.
* Due date not before today; amounts `9(13)V9(2)`; the trailer carries the
  count and the sum of the amounts.
* Domestic: a payment in another currency than the account's goes with the
  counter-currency and conversion flag `P`; a non-CZK counter-currency only
  to another KB account; a direct debit outside KB only in CZK; the constant
  symbols KB refuses in a batch (`???5`, `??51`, `0006`, `0007`) are
  refused before the bank does.
* Foreign: SWIFT character set only, no field starting with `-` or `:`;
  **SEPA** (flag `Y`, charges `SLV`) when EUR, an IBAN in a SEPA country and
  shared charges; into the EEA only with `SHA` (PSD2, since 13 Jan 2018); EUR
  into the EEA needs an IBAN; a non-SEPA payment needs the beneficiary's name,
  street, city and country and a BIC or the bank's name, city and country.
  `/VS/` and `/KS/` are written into the remittance, where KB reads them
  back into the transaction history.

## Statement parsing

Signs come from the accounting code — `0` debit, `1` credit, `2` debit
reversal, `3` credit reversal — which is the spec's own check
`NZ = SZ − OD + OK`. `53` records (non-accounting loan interest and fee
instalments) do not move the balance and are skipped. SS `9999999999` is an
instruction to suppress the partner's name, not a symbol, and is dropped.
