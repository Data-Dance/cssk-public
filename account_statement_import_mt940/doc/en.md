---
title: Bank Statement Import — MT940 / MultiCash
summary: Imports SWIFT MT940 bank statements — the *.STA files of MultiCash, X-business and Business 24 — with VS/KS/SS, counterparty accounts and balances.
verified: 19.0.1.0.0
---

## What it is for {#purpose}

Czech banks hand statements to accounting software as **SWIFT MT940**:
MultiCash writes them as `*.STA` files (into `MCCWIN` in version 3.x, `DATA`
in 4.x), and X-business and Business 24 use the same layout. The SWIFT part is
the same everywhere; field `:86:` ("information to account owner") is not, and
it is where the variable, constant and specific symbols, the counterparty's
account and name and the payment message live.

This module imports such files through the OCA statement import wizard
(`account_statement_import_file`), on Community and Enterprise alike. It is
the statement half of MultiCash; the payment half is
[module:account_multicash](module:account_multicash).

## What is read {#format}

| Field | Becomes |
|---|---|
| `:25:` account | the journal the statement belongs to |
| `:28C:` statement number | the statement name `MT940 <account>/<number>` |
| `:60F:` / `:60M:` opening balance | the statement's opening balance and its currency |
| `:61:` transaction | a statement line: amount, sign (`C` credit, `D` debit, `RC`/`RD` reversals), booking date (else the value date), SWIFT transaction type, customer reference |
| `:86:` details | label, VS/KS/SS, counterparty account and name |
| `:62F:` / `:62M:` closing balance | the statement's closing balance |

**The `:86:` field.** Banks write it as `?NN` subfields and do not agree on the
numbering — Česká spořitelna puts `KS:` in `?20` and `VS:` in `?21`,
Raiffeisenbank puts `KS` in `?21` and `VS` in `?22`. The module therefore
recognises a symbol by its prefix (`VS`, `KS`, `SS`, with or without a colon,
zero-padded or not), never by its position. The counterparty comes from `?30`
(bank code or BIC), `?31` (account), `?38` (IBAN) and `?32`/`?33` (name); the
message from `?00`, `?20`–`?29` and `?60`–`?63`. Recurring noise such as
Raiffeisenbank's statement number and zero fee lines is dropped. A `:86:`
without subfields is kept as free text, and `VS:`-style tokens are still
picked out of it.

On each statement line:

- **Label**: counterparty name, message, `VS:…`, `KS:…`, `SS:…`, counterparty
  account.
- **Partner**: looked up from the counterparty account among the bank accounts
  in Odoo.
- **Symbols**: with
  [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#bank-statements)
  installed, also in the line's own symbol fields.
- The raw `:61:`/`:86:` text is kept on the line, the customer reference goes
  to *Reference*, the SWIFT type to *Transaction Type*.

One file may hold several days and several accounts; each statement lands on
its own journal. A statement split over several messages (`:60M:` opening, same
statement number, opening equal to the previous closing) is joined into one.

The file is read as UTF-8 if it is valid UTF-8, otherwise as code page 852 or
Windows-1250, whichever yields more Czech letters.

## Setting it up {#setup}

- Every account in the file needs a bank journal with that bank account
  (*Accounting → Configuration → Accounting → Journals*), in the statement's
  currency.
- **The account can be written either way.** Česká spořitelna writes `:25:` as
  `0800/192000145399` (bank code first), others as an IBAN. The module
  compares bank code, prefix and number, so a journal whose account is stored
  as a `CZ` IBAN or as `19-2000145399/0800` is found in both cases.

## Importing a statement {#usage}

*Accounting → Accounting → Import Statement*, or **Import Statement (OCA)** on
the bank journal's card in the Accounting dashboard. Choose the `.STA` file and
press **Import and View**.

Importing the same statement again is refused line by line: each line's import
key is made from the account, the statement number, the value date, the
line's position on the statement, the amount and the bank reference. A file
overlapping an earlier import brings in only the new lines.

## Limitations {#limitations}

- The `:86:` layout was checked against the published descriptions of Česká
  spořitelna (*MultiCash 3.2*, also valid for Business 24) and Raiffeisenbank
  (MT940 versions 2–4 for MultiCash and X-business). Other banks' MT940 is read
  through the same SWIFT fields, but their `:86:` has not been compared with a
  published layout; with free-text `:86:` the label is the text as given.
- Matching the journal by bank code, prefix and number works for Czech and
  Slovak accounts. A foreign account must match the journal's account as
  written.
- The import key includes the line's position on the statement. If a bank
  re-issues a statement with the lines in a different order, lines may be
  imported twice.
- MT940 has two-digit years; dates are read as 1980–2079.
