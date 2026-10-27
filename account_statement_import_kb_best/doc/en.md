---
title: Bank Statement Import — KB BEST
summary: Imports Komerční banka's BEST electronic statements (*.OKM / *.KMO) with balances, counterparty accounts and VS/KS/SS.
verified: 19.0.1.0.0
---

## What it is for {#purpose}

Komerční banka's direct banking channels — MojeBanka Business, Profibanka and
Přímý kanál — export electronic statements in KB's **BEST** format, as
`*.OKM` or `*.KMO` files. This module imports them through the OCA statement
import wizard (`account_statement_import_file`), on Community and Enterprise
alike. Payments in the same format are written by
[module:account_payment_kb_best](module:account_payment_kb_best).

## What is read {#format}

| Record | Content | Becomes |
|---|---|---|
| `HO` | file header naming BEST | how the file is recognised |
| `51` | turnover per account and day: account and IBAN, opening and closing balance, statement number, date | one bank statement `BEST <account>/<number>` with its balances |
| `52` | accounting transaction | one statement line |
| `53` | non-accounting item (loan interest and fee instalments) | skipped — it does not move the balance |

On each line:

- **Amount and sign** from the accounting code: `0` debit, `1` credit, `2`
  reversal of a debit, `3` reversal of a credit.
- **Label**: counterparty name, the message for the beneficiary, `VS:…`,
  `KS:…`, `SS:…`, the counterparty account; KB's own transaction description
  when there is no message.
- **Reference**: your own description (*popis pro mě*) of the side you are on.
- **Counterparty account**: the domestic account and bank code; for a foreign
  or SEPA payment, the IBAN KB puts in the first description field.
- **Partner**: looked up from the counterparty account among the bank accounts
  in Odoo.
- **Symbols**: with
  [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#bank-statements)
  installed, also in the line's own symbol fields. A specific symbol
  `9999999999` is KB's instruction to hide the partner's name, not a symbol,
  and is dropped.

A file may hold several days and several accounts; each account and day is
one statement.

## Setting it up {#setup}

- A bank journal with the KB account (*Accounting → Configuration → Accounting
  → Journals*), in the statement's currency. The account may be stored as an
  IBAN or as `prefix-number/0100`: the module compares bank code, prefix and
  number, not the written form.
- In KB's channel, export statements in the BEST format.

## Importing a statement {#usage}

*Accounting → Accounting → Import Statement*, or **Import Statement (OCA)** on
the bank journal's card in the Accounting dashboard; choose the file and press
**Import and View**.

KB's own posting identifier is part of each line's import key, so importing the
same file twice adds nothing, and a file overlapping an earlier one brings in
only the new lines.

## Limitations {#limitations}

- A day that has only non-accounting (`53`) items produces no statement.
- Written against KB's specification valid from 20 June 2026 and KB's sample
  files; older variants of the format have not been tested.
