---
title: CAMT Import — Statements That Pass the Balance Check
summary: Corrects two ways a valid CAMT.053 statement fails the balance check in the OCA CAMT import — daily closing balances and transactions split over several detail blocks.
verified: 19.0.1.0.0
---

## What it is for {#purpose}

The OCA module `account_statement_import_camt` imports ISO 20022 **CAMT.053**
bank statements. Some banks write statements that are perfectly correct but
that this import reads in a way that leaves the statement out of balance —
found on real Tatra banka statements. This module corrects the two cases. It
adds no screen and no settings; install it next to the OCA CAMT import and
import as before.

## What it changes {#changes}

**A closing balance for every day.** A monthly statement may carry one
opening balance for the month and a closing balance (`CLBD`) for every day
with movements. The OCA import takes the first `CLBD`, so the statement
"closes" on the first day's balance and never balances. This module takes the
**latest** closing balance and the **earliest** opening balance (`OPBD` or
`PRCD`) — by their dates, or in the order they appear in the file where they
carry no date. A statement with a single closing balance is not touched.

**One transaction split over several detail blocks.** The OCA import makes one
statement line for every `TxDtls` block of an entry, and a block without an
amount of its own inherits the whole entry amount. A bank that describes one
fee in two blocks — one with the references, one with the amount — therefore
gets the fee booked twice. When the lines of an entry **do not add up** to the
entry's amount, this module merges its blocks into **one line** for the entry
amount, taking each detail from the first block that has it and joining the
notes. A genuine batch, whose blocks carry their own amounts and add up to the
entry, keeps one line per payment.

## Usage {#usage}

Nothing changes in how you import: *Accounting → Accounting → Import
Statement* (or **Import Statement (OCA)** on the bank journal's card), choose
the CAMT file, **Import and View**. The statement's opening and closing
balance now match its lines.

## Limitations {#limitations}

- A stopgap: both corrections are candidates for the OCA module itself, and
  this module becomes unnecessary once they are merged there.
- The merge decision rests only on the amounts. An entry whose blocks do not
  add up for another reason is also merged into one line; the merged line
  carries the first block's partner and references.
- It changes only the OCA CAMT import, not Odoo Enterprise's own CAMT import.
