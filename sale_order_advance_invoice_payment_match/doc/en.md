---
title: Advance Invoices — Bank Statement Matching
summary: Matches incoming bank transactions to open advance invoices by the advance number or variable symbol, registers the payment and optionally creates the tax document.
verified: 19.0.1.1.0
---

## What it is for {#purpose}

An advance invoice from
[module:sale_order_advance_invoice](module:sale_order_advance_invoice) has no
journal entry until it is paid, so no bank reconciliation, Odoo's or OCA's,
can ever propose it for an incoming payment. This module closes that gap. It
finds the advance a bank transaction pays and registers the payment exactly
as the advance's own **Register Payment** button would. If you want, it also
creates the tax document for the payment.

It is the advance-invoice sibling of the invoice matching in
[module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#bank-matching):
that one matches payments to posted invoices, this one to advance invoices.
The two passes are independent.

## Setting it up {#setup}

*Accounting → Configuration → Settings*, block **Advance Invoices — Bank
Matching**:

| Setting | What it does |
|---|---|
| Auto-match bank statements | Turns on automatic matching for the company (off by default). The manual wizard works either way. |
| Tax document on matched payment | What happens once a transaction has paid an advance: **Leave for manual creation** (default), **Create as draft**, or **Create and post**. Posting also reconciles the clearing account. |

The advance settings of
[module:sale_order_advance_invoice](module:sale_order_advance_invoice#setup)
must be complete, the **Advance Clearing Account** above all. The bank
journal needs an incoming payment method with an outstanding receipts account.

## How a transaction is matched {#matching}

Only incoming transactions in the company currency are considered. They are
compared with the company's advance invoices that are not cancelled and still
have something unpaid. If the bank transaction already knows the customer
(for example from the account number), only that customer's advances are
considered.

The transaction is searched in three tiers, strongest first, and the first
tier that finds anything decides:

| Tier | What is compared | When it is applied automatically |
|---|---|---|
| Advance number | `ADV00042` written in the label, the reference or the bank's transaction details | the amount does not exceed what is unpaid |
| Variable symbol | the transaction's variable symbol, compared with the digits of the advance number, **ignoring leading zeros** (`42` = `00042`) | the amount does not exceed what is unpaid |
| Digits | any run of 3 to 10 digits in the label or reference, compared the same way | the amount **equals** what is unpaid |

The variable symbol tier needs a variable symbol on the bank transaction.
[module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#bank-statements)
reads it out of bank statements. Without that module the tier is skipped.

If a tier finds **more than one** advance, nothing is matched. An advance
number is unique only per issuer, so the pass never guesses. Partial payments
are accepted in the first two tiers. A payment larger than what is unpaid is
never applied automatically.

Ask your customers to quote the advance number, or its digits as the variable
symbol: for `ADV00042`, the variable symbol `42` or `00042`.

## What a match does {#applying}

1. A customer payment for the transaction's amount and date is created in the
   bank journal, posted to the **Advance Clearing Account**, and linked to the
   advance. A quotation is confirmed.
2. A bank transaction with no customer gets the advance's customer.
3. The transaction is reconciled with the payment, so it shows as reconciled.
4. With **Create as draft** or **Create and post**, the tax document for the
   payment is created as described in
   [module:sale_order_advance_invoice](module:sale_order_advance_invoice#tax-document),
   and posted with the second option.

## Automatic and manual matching {#triggers}

- **Scheduled action** *Advance Invoices: match bank statement lines* runs
  every 15 minutes. It goes through up to 200 unreconciled incoming
  transactions in bank journals of the companies with *Auto-match bank
  statements* on: first those it has never seen, then, with what is left of
  the 200, the older ones in turn. A transaction that cannot be matched
  safely is left alone and comes round again later, so every open
  transaction is retried, however many there are.
- **Match Advance Invoice** in the *Actions* menu of a bank transaction
  (list or form) opens a wizard. It proposes the advance the rules find, and
  you may pick any open advance of the same company (of the same customer, if
  the transaction has one). **Register Payment** then does the same as an
  automatic match. The wizard does not need the automatic setting, and it
  refuses an amount larger than what is unpaid.

### Inside the bank reconciliation {#bank-reconciliation}

Two add-ons run the same matching as part of a bank reconciliation's own
automatic matching, **before** it. A transaction quoting an advance number
cannot then be matched by words to an unrelated document first. Both install
themselves when their engine is present, and both honour *Auto-match bank
statements*:

- [module:sale_order_advance_invoice_payment_match_ee](module:sale_order_advance_invoice_payment_match_ee)
  — Odoo Enterprise bank reconciliation (`account_accountant`): runs before
  its automatic reconciliation;
- [module:sale_order_advance_invoice_payment_match_oca](module:sale_order_advance_invoice_payment_match_oca)
  — the OCA reconciliation widget (`account_reconcile_oca`) on Community:
  runs before its reconciliation models and invoice matching, and only when
  it actually reconciles, not when it merely computes a proposal.

Matched transactions show as reconciled in either widget.

## Limitations {#limitations}

- Incoming transactions only, in the company currency, paying an advance in
  the same currency.
- No tie-break by amount: two advances that both fit the same tier are left
  to you, even if only one of them has the right amount. This differs from
  the invoice matching of
  [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#bank-matching).
- An overpayment is never split. Register the payment and the surplus by
  hand.
- The digits tier can be fooled by numbers that are not symbols, such as a
  date or an account number. That is why it applies a match only on an exact
  amount.
