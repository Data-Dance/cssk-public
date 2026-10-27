---
title: Fio banka — Payment Orders
summary: Builds Fio XML payment orders from an OCA payment order or an Enterprise batch payment and sends them to Fio banka over the API, for authorisation in internet banking.
verified: 19.0.1.3.0
---

## What it is for {#purpose}

Instead of downloading a payment file and uploading it in internet banking,
you send the payment batch from Odoo to Fio banka with one button. Fio stores
it as an **unauthorised batch**; someone with signing rights then confirms it
in Fio internet banking (by SMS or Fio signature). **Nothing in Odoo moves
money on its own.**

The file is Fio's own XML (`importIB.xsd`), the only Fio upload format that
carries the variable, constant and specific symbols as real fields — pain.001
is EUR only and ABO is CZK domestic only. The module works from an OCA
**payment order** (`account_payment_order`); on Enterprise,
[module:account_payment_fio_batch](module:account_payment_fio_batch) does the
same from a **batch payment** — see [below](#batch).

It needs the connection from [module:account_fio](module:account_fio#setup)
with a **submit token** on the journal.

## Three kinds of order {#kinds}

Each payment line becomes one of three Fio orders, chosen automatically:

| Beneficiary's account | Fio order | Notes |
|---|---|---|
| Czech: a `CZ` IBAN or `[prefix-]number/bank code` | domestic payment | any currency Fio allows between its own accounts; VS, KS, SS, message for the beneficiary |
| EUR to an IBAN in a SEPA country (including Slovakia) | Europlatba (SEPA) | VS, KS, SS; beneficiary's name required |
| anything else | foreign payment | BIC, the beneficiary's name, street, city and country, a payment reference and a *platební titul* all required |

On a payment order, **Priority** (*Urgent* sends a priority payment) and
**Charge Bearer** (for foreign payments) are set on each line; they default to
standard and shared.

The orders are written domestic first, then Europlatba, then foreign, as Fio
requires. The file is named `FIO-<journal code>-<date and time>.xml`.

## Setting it up {#setup}

1. The bank journal: its bank account is the Fio account the money leaves —
   a `CZ` or `SK` IBAN, or `number/2010` (Fio CZ) or `number/8330` (Fio SK).
   It needs a **Fio Submit Token** (see [module:account_fio](module:account_fio#tokens)).
2. A payment mode (*Accounting → Configuration → Accounting → Payment
   Modes*) with the payment method **Fio XML (Fio banka API)** and that
   journal.
3. Partners: a bank account for everyone you pay; for foreign payments also
   the address, the BIC of their bank, and the **Platební titul** on the
   partner (tab *Sales & Purchase*) so it fills in by itself.
4. Recommended: [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols),
   so each bill's VS/KS/SS reaches the payment lines on its own (see
   [module:account_abo](module:account_abo#setup)).

## Paying {#usage}

1. *Accounting → Vendors → Payment Orders*, **New**, choose the Fio payment
   mode, **Create Payment Lines from Journal Items**.
2. Check the lines: **Variable Symbol**, **Constant Symbol**, **Specific
   Symbol** and **Platební titul** sit next to *Communication*. An empty symbol
   is taken from a `VS:` / `KS:` / `SS:` token in the *Communication*.
3. **Confirm Payments**. This is where everything is checked (below).
4. **Generate Payment File**, then **Send to Fio**.
5. Authorise the batch in Fio internet banking.

When Fio accepts the batch, the order shows *Sent to Fio as batch …* with
Fio's batch number and moves on to the uploaded state by itself — there is no
need to press *File Successfully Uploaded*. Fio's answer, including any
warnings per order, is posted in the order's chatter.

### What is checked {#checks}

At **Confirm Payments** the whole order is checked and **every** problem is
listed in one message (*This payment order cannot be sent to Fio yet*):

- the amount is not positive, or the currency, date or recipient account is
  missing;
- a domestic payment has no bank code;
- a Europlatba or foreign payment has no beneficiary name;
- a foreign payment lacks the BIC, the beneficiary's street, city or country,
  a payment reference (the *Communication*), or a valid *platební titul*;
- a Europlatba over EUR 50 000 from an account at Fio's **Slovak** branch has
  no valid *platební titul*;
- an account is neither an IBAN nor a domestic `number/bank code`.

The *platební titul* is the three-digit payment reason from the Czech National
Bank's code list. On a payment line it defaults from the partner.

## Send to Fio {#send}

**Send to Fio** appears on any payment order whose file has been generated and
not yet sent. It recognises the file type from the file itself, so it also
sends:

- the ABO file from [module:account_abo](module:account_abo),
- a SEPA pain.001 (and pain.008) file from the OCA SEPA modules,

as long as the journal is a Fio account with a submit token. Fio rejects files
over 2 MB; split the order then.

**If the answer is lost.** When the file left Odoo but no answer came back,
nobody knows whether Fio holds the batch. The order then goes to **Unknown —
check the bank** and shows a red warning; sending again is blocked, because a
second batch, if both were authorised, would pay everything twice. Look in Fio
internet banking for an unauthorised batch and record what you found:

- **It IS in the bank** — the order is marked as sent and cannot be sent
  again;
- **It is NOT in the bank** — sending is enabled again.

A batch that Fio **rejects** stays *Not sent*; the reasons appear on screen and
in the chatter, and you can correct and send again.

## Enterprise batch payments {#batch}

[module:account_payment_fio_batch](module:account_payment_fio_batch) builds
the same Fio XML from an Enterprise **batch payment** and sends it with the
same button and the same *Unknown* safeguard.

- On installation the outgoing payment method **Fio XML (Fio banka API)** is
  added to the bank journals whose own account is at Fio (bank code 2010 or
  8330, or a Fio BIC), and to such journals created later or given a Fio
  account later. Journals at other banks do not get it.
- The vendor payment form gets a **Platební titul** field, defaulting from the
  partner.
- Register the payments with that method, group them in a batch
  (*Accounting → Vendors → Batch Payments*) and press **Validate**: the batch
  lists every payment that cannot be sent, grouped by problem, before the file
  is written. Then press **Send to Fio**. The bank's answer is on the batch's
  *Fio* tab.
- Every payment in the batch is executed on the **batch date**, because the
  batch is authorised as one in internet banking.
- With Odoo's ISO 20022 module, a payment marked urgent is sent as a priority
  payment.

Both modules can be installed side by side.

## Limitations {#limitations}

- **"Sent" is not "paid"**: the batch waits in internet banking for
  authorisation.
- Fio's batch number is not the instruction ID that later appears on the
  statement lines, so a payment cannot be traced to its statement line through
  it — match on VS, amount and date.
- The paying account cannot have a **prefix**: Fio's `accountFrom` is a plain
  number. Configure the journal with the account number Fio itself shows.
- **Enter Slovak beneficiaries as IBAN.** A `number/bank code` account is
  read as Czech. When Odoo knows it is Slovak — its bank's country, or else the
  holder's country, is Slovakia — the payment is refused with a request for the
  SK IBAN rather than sent to a Czech bank of that code; with neither country
  recorded it still goes out as a Czech domestic payment.
- Fio operates no test environment; check the first batch carefully in
  internet banking before authorising it.
