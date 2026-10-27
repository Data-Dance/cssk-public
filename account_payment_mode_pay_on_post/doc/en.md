---
title: Payment Mode — Pay on Validation
summary: A payment mode can register the payment the moment the invoice is posted, for sales paid in cash or by card on the spot.
verified: 19.0.1.0.0
---

## What it is for {#purpose}

When a customer pays in cash or by card at the counter, the invoice is paid
the moment it is issued. Registering the payment as a separate step is only
a chance to forget it, and the open invoice then shows up in the receivables
and in payment reminders.

This module adds one option to OCA's payment modes (`account_payment_mode`):
an invoice whose payment mode has it is **paid in full automatically when it
is posted**, in the journal the payment mode names.

## Setting it up {#setup}

*Accounting → Configuration → Payment Modes* (the module has no Slovak or
Czech translation, so its labels are in English). Create or open a payment
mode, for example *Cash* or *Card*:

| Field | Value |
|---|---|
| Payment Type | Inbound for customer invoices |
| Link to Bank Account | **Fixed** |
| Fixed Bank Journal | the journal the money arrives in — a cash journal for cash, the card clearing journal for cards |
| **Register payment on validation** | ticked |

The checkbox appears only when *Link to Bank Account* is *Fixed*, and a mode
with it ticked cannot be saved without a fixed journal.

Set the mode on the invoice (field *Payment Mode*), or as the customer's
default payment mode on the contact so that new invoices get it
automatically.

## What happens when you post {#usage}

When an invoice is posted and its payment mode has **Register payment on
validation**:

- a payment for the **whole amount still due** is created and reconciled
  with the invoice, through Odoo's standard *Register Payment* wizard — the
  same payment as if you had registered it by hand;
- in the payment mode's fixed journal;
- dated the **invoice date** (the accounting date if there is none).

The invoice then shows as *Paid*, or *In Payment* if the journal uses an
outstanding receipts account and waits for the bank statement.

It works the same for customer credit notes, vendor bills and receipts that
carry such a payment mode. An invoice that is already paid, or has nothing
left to pay, is left alone. Several invoices posted together each get their
own payment.

## Limitations {#limitations}

- The payment is always for the full amount. For a partly paid sale, use a
  payment mode without the option and register the payment yourself.
- The payment is dated the invoice date, not the moment of posting. If you
  post an invoice dated in the past, the payment is dated in the past too.
- If the payment cannot be created — for example the journal has no
  suitable payment method — the invoice is not posted either.
- The module only records the payment. It does not issue a cash register
  receipt or talk to a card terminal.
