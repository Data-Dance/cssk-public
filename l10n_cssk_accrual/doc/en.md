---
title: CZ/SK Estimated Accruals
summary: Book an estimate for a cost or revenue whose invoice has not arrived by the period end, then settle it against the real invoice so only the difference stays in the new period.
verified: 19.0.1.1.0
---

## What it is for {#purpose}

At the period end some costs have been incurred but not yet invoiced:
electricity consumed in December, a service delivered but billed in January,
an audit fee for the year being closed. Czech accounting books such items on
**estimated-item accounts** (*dohadné účty*, 388 active and 389 passive);
Slovak accounting uses **326** *Nevyfaktúrované dodávky* for unbilled
supplies, or a provision when the amount is uncertain (see
[Legal background](#legal)).

Odoo has no such document. This module adds one: the **estimated accrual**
(*dohadná položka*). You enter the estimate at the period end, post it, and
when the invoice arrives you link it and settle the estimate. Settling
reverses the estimate as of the invoice date, so the accrual account clears
and only the difference between estimate and invoice falls into the new
period.

Accrual (*dohadná položka*) is not the same as a deferral (*časové
rozlíšenie / časové rozlišení*), which spreads a **known** amount over
periods. Deferrals are handled by
[module:l10n_cz_account_cutoff](module:l10n_cz_account_cutoff) and
[module:l10n_sk_account_cutoff](module:l10n_sk_account_cutoff).

The module works with any chart: you choose the accounts and journal on each
estimate. It needs only Odoo's `account` module and
[module:l10n_cssk_core](module:l10n_cssk_core), so it runs on Community and
Enterprise alike.

## Legal background {#legal}

Both accounting acts require items to be booked in the period they relate to
in time and substance — [§ 3 odst. 1 of the Czech Accounting
Act](law:cz/1991/563) and
[§ 3 ods. 1 of the Slovak Accounting Act](law:sk/2002/431#paragraf-3.odsek-1).
How an unbilled item is shown differs:

- **Czech Republic.** [Vyhláška 500/2002 Sb.](law:cz/2002/500) (§ 10
  odst. 7, § 17 odst. 6 and Annex 1) defines *dohadné účty aktivní* and
  *dohadné účty pasivní* as amounts determined, for example, from contracts,
  that are not supported by all the necessary documents, so their exact
  amount is not known. These are accounts 388 and 389.
- **Slovakia.** [Opatrenie 740/2002 Z. z.](law:sk/2002/740) has no
  *dohadné účty*. Account **326** *Nevyfaktúrované dodávky* takes unbilled
  supplies whose amount the entity **knows** from a contract, delivery note or
  other document ([§ 50 ods. 6](law:sk/2002/740#paragraf-50.odsek-6)); where
  the timing or amount is uncertain, a short-term provision on 323 is created
  instead ([§ 50 ods. 3](law:sk/2002/740#paragraf-50.odsek-3)). An unbilled
  receivable is booked on the receivable account it belongs to, on a separate
  analytical account ([§ 48 ods. 3](law:sk/2002/740#paragraf-48.odsek-3)).

The module records whatever accounts you give it. Which account applies to a
given item — and, in Slovakia, whether it is an unbilled supply or a
provision — is your accountant's decision.

## Setting it up {#setup}

There are no settings. Before the first estimate:

- **Allow reconciliation on the accrual account.** Settling clears the
  estimate against its reversal on that account, so posting is refused unless
  the account has *Allow Reconciliation* ticked (*Povoliť párovanie* /
  *Povolit párování plateb*). Odoo's Czech chart ships 388000 and 389000, and
  the Slovak chart 326000, **without** it: open the account under
  *Accounting → Configuration → Accounting → Chart of Accounts* and tick it.
- **A miscellaneous journal.** Estimates post in a journal of type
  *Miscellaneous*.

The menu sits under *Accounting → Accounting*, which Community shows only
when full accounting features are enabled; there the app itself is called
*Invoicing*.

## Entering an estimate {#usage}

*Accounting → Accounting → Transactions → Estimated Accruals*, then *New*.

| Field | Fill in |
|---|---|
| Partner | The supplier (or customer) the invoice is expected from (or to). Required. |
| Accrual Type | **Estimated payable** — a cost not yet invoiced; or **Estimated receivable** — revenue not yet invoiced. |
| Date | The date the estimate is booked, normally the last day of the period. |
| Amount | The estimated amount in the company currency, without VAT. Must be positive. |
| Description | Printed on both journal items. |
| Journal | A miscellaneous journal of the company. |
| Accrual Account | 389 / 388 (CZ). In Slovakia: 326 for an unbilled supply, or a separate analytic account of the receivable for an unbilled receivable — whichever your accountant chooses. |
| Counterpart Account | The expense account (estimated payable) or income account (estimated receivable). |

Click **Post Estimate**. The module creates and posts one entry, numbered
`DOHAD/<year>/0001` onwards:

| Accrual Type | Debit | Credit |
|---|---|---|
| Estimated payable | Counterpart (expense) | Accrual account |
| Estimated receivable | Accrual account | Counterpart (income) |

Both lines carry the partner. The entry has no VAT: an estimate is not a tax
document.

## Settling against the invoice {#settle}

Book the real invoice the usual way, to the expense or income account, and
post it. Then open the estimate:

1. In **Actual Invoice**, pick the invoice. The list offers posted invoices
   and credit notes of the same partner and company.
2. Click **Settle (link invoice)**.

The module reverses the estimate entry as of the **invoice date** (or the
estimate date, if the invoice is dated earlier) and reconciles the estimate
with its reversal on the accrual account. The accrual account for this
estimate returns to zero, the reversal cancels the estimated expense in the
new period, and the invoice books the actual one. What remains in the new
period is exactly the difference.

Example: an estimate of 1 000 for December electricity; the January invoice
says 1 050 without VAT. In January the reversal credits the expense with
1 000 and the invoice debits it with 1 050 — 50 stays in January, 1 000 stays
in December.

The estimate moves to *Settled*; *Estimate Entry* and *True-up / Reversal
Entry* link to the two entries.

## Cancelling an estimate {#cancel}

**Cancel** on a posted estimate reverses its entry as of **today** and
reconciles it, then sets the estimate to *Cancelled*. A draft estimate is
simply cancelled.

**Reset to Draft** brings a cancelled estimate back to draft, to correct it
and post it again. The cancelled entry and its reversal stay in the books
(they net to zero) and the chatter names them; posting again books a new
entry.

Two checks run before any reversal (settling or cancelling):

- If the accrual line has already been reconciled with something else, the
  module refuses and names the entries it is matched with. Unreconcile first.
- If the reversal date falls in a locked period, the module refuses and names
  the lock. Adjust the lock date, or settle against a later-dated invoice.

## Limitations {#limitations}

- The module does not compare the estimate with the invoice, and does not
  reconcile the invoice with anything. The invoice is not checked against
  the accrual type either: any posted invoice or credit note of the partner
  can be linked.
- One estimate settles against one invoice. An estimate covering several
  invoices has to be split into several estimates, or settled against one of
  them and the rest booked normally.
- Amounts are in the company currency only; there is no foreign-currency
  estimate and no analytic distribution on the entry.
- Cancelling reverses as of today, not as of a date you choose.
- Nothing is estimated automatically, and there is no reminder of estimates
  still open at the next period end; filter the list by *Posted*.
