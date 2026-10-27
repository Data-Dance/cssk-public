---
title: Bank Statement Import — GPC
summary: Imports GPC electronic bank statements (the ABO statement format of Czech and Slovak banks), with balances, counterparty accounts and VS/KS/SS.
verified: 19.0.2.0.1
---

## What it is for {#purpose}

**GPC** is the fixed-width electronic statement that most Czech and Slovak
banks offer for download alongside their other formats — Fio banka, KB, ČS,
ČSOB and others. It carries what a Czech or Slovak accountant matches
payments on: the counterparty's account and bank code and the **variable,
constant and specific symbols**.

This module adds GPC to the OCA statement import wizard
(`account_statement_import_file`) on Community. On Enterprise,
[module:account_statement_import_gpc_ee](module:account_statement_import_gpc_ee)
adds it to Odoo's own statement import instead — see [below](#enterprise).

## What is read {#format}

A GPC file is a sequence of 130-character records:

| Record | Content | Becomes |
|---|---|---|
| `074` | statement header: account, old and new balance with their signs, statement number, date | one bank statement named `GPC <account>/<number>`, with its opening and closing balance |
| `075` | transaction: own account, counterparty account and bank code, document number, amount in hellers, accounting code, VS, KS, SS, counterparty name, currency, date | one statement line |
| `076`, `078`, `079` | additional message lines | appended to the label of the preceding line |

Any other record is ignored — banks add their own.

The sign of the amount comes from the accounting code: `1` debit, `2`
credit, `4` reversal of a debit (money comes back), `5` reversal of a credit
(money leaves).

On each statement line:

- **Label**: the counterparty name (or `GPC <document number>`), then
  `VS:…`, `KS:…`, `SS:…` and the counterparty account `number/bank code`.
- **Partner**: looked up from the counterparty's account number among the
  bank accounts in Odoo; the name is kept for the line.
- **Symbols**: with
  [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#bank-statements)
  installed, VS, KS and SS also land in the line's own symbol fields, where
  matching by variable symbol uses them.
- **Date**: the transaction date of the `075` record.

A file covering several days (one `074` per day) gives one statement per day.
A `074` block with no transactions is skipped.

The file is decoded as Windows-1250, or Latin-1 if that fails. The currency is
read from the transactions; CZK, EUR, USD, GBP, PLN, HUF, CHF, DKK, SEK and NOK
are recognised.

## Setting it up {#setup}

- The bank journal (*Accounting → Configuration → Accounting → Journals*) must
  have its bank account filled in. The GPC header carries the account
  **without the bank code**; the journal is found by comparing the prefix and
  the number with the journal's account, so a `CZ` / `SK` IBAN,
  `prefix-number/bank code` and the bare digits all work.
- The journal's currency must be the statement's currency.
- Download the statement from your bank in the GPC format (sometimes offered
  as *ABO* or `.gpc`).

## Importing a statement {#usage}

*Accounting → Accounting → Import Statement*, or **Import Statement (OCA)** on
the bank journal's card in the Accounting dashboard. Choose the file and press
**Import and View**.

Importing the same file again is safe: each line carries an import key made
from the account, the date, the document number and the signed amount, and
lines already imported are skipped. A file overlapping an earlier one brings
in only the new lines.

## Enterprise {#enterprise}

[module:account_statement_import_gpc_ee](module:account_statement_import_gpc_ee)
adds GPC to Enterprise's statement import, next to CAMT, OFX, QIF and CSV:
use **Import File** on the bank journal's card in the Accounting dashboard. The
file is recognised by its first record (`074` or `075`); everything described
above applies the same way.

Enterprise checks the account of the file against the journal it is imported
into; the module makes that check compare prefix and number too, so a journal
stored as an IBAN or as `prefix-number/bank code` accepts its GPC files. A
file covering **several accounts** is refused on Enterprise, which imports
into the journal it was started from: download one file per account.

## Limitations {#limitations}

- Only the ten currencies listed above. A file in another currency stops
  with *Missing currency code*.
- GPC carries no bank code, so two accounts with the same prefix and number
  at two banks cannot be told apart; the journal you import from is preferred.
  An account that only *contains* the file's digits is not taken for it — the
  import stops and names the look-alike journal.
- Switching an account from GPC files to a bank connection (for example the
  [Fio API](module:account_statement_fio)) does not recognise lines already
  imported from GPC, because the two use different import keys. Switch at a
  statement boundary.
