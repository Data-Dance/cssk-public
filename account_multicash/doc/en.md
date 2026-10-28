---
title: MultiCash Payment Files
summary: Domestic, urgent, direct-debit and foreign payments exported as MultiCash files (CFD, CFU, CFA, MT101), from an OCA payment order or an Enterprise batch payment.
verified: 19.0.2.2.0
---

## What it is for {#purpose}

**MultiCash** is the client application several Czech banks give their
corporate customers for sending payment batches and fetching statements. It
imports payment files in fixed formats. This module writes those files from an
OCA **payment order** (`account_payment_order`), so it works on Community
without any Enterprise module. On Enterprise,
[module:account_multicash_batch](module:account_multicash_batch) writes the
same files from a **batch payment** — see [below](#batch).

The layouts follow Česká spořitelna's *MultiCash 3.2* format description. The
statement side of MultiCash (`*.STA` files in MT940) is imported by
[module:account_statement_import_mt940](module:account_statement_import_mt940).

## The formats {#formats}

You choose the format by choosing the payment method. Each method writes one
file type:

| Payment method | What it is | File | Currency and accounts |
|---|---|---|---|
| MultiCash CFD (Czech domestic transfer) | domestic credit transfers | `.cfd` | CZK, Czech accounts only |
| MultiCash CFD (Czech direct debit / inkaso) | domestic direct debits — you collect from your customers | `.cfd` | CZK, Czech accounts only |
| MultiCash CFU (Czech urgent transfer) | urgent domestic transfers | `.cfu` | CZK, Czech accounts only |
| MultiCash CFA (foreign transfer) | cross-border payments | `.cfa` | any currency; the beneficiary's account as entered (normally an IBAN) |
| MultiCash MT101 (SWIFT Request For Transfer) | SWIFT MT101 transfer request | `.mt101` | any currency; accounts as entered |

"Czech account" means a `CZ` IBAN or `[prefix-]number/bank code`.

What goes into the file:

- **CFD / CFU**: one block per payment with its own date, amount in hellers,
  both accounts, the names and addresses of payer and payee (from the company
  and the partner, up to four lines of 35 characters), VS, KS and SS, and up
  to four lines of message from the *Communication*. Text is upper-cased and
  encoded in code page 852.
- **CFA**: a file header with the total and the count, then one SWIFT-like
  block per payment: payer, ordering account, beneficiary's account, name and
  address, the beneficiary's bank by BIC (or by name and address when the
  bank has no BIC), the payment details and the charge bearer. Code page 852.
- **MT101**: one message for the whole file with a single execution date, then
  a transaction per payment. Plain ASCII.

## Setting it up {#setup}

1. **The bank journal** (*Accounting → Configuration → Accounting → Journals*)
   needs its bank account. For CFD and CFU, and for the ordering account of
   CFA, it must be a Czech account. For **CFA and MT101 the journal's bank
   must also have a BIC** — the export refuses to run without one.
2. **A payment mode** per format you use (*Accounting → Configuration →
   Accounting → Payment Modes*), with the matching MultiCash payment method
   and the journal. Use the *direct debit / inkaso* method on an inbound
   payment mode.
3. **Partners**: a bank account on every partner you pay or collect from. For
   CFA and MT101 also the partner's address and country, and preferably the
   BIC of their bank.
4. Recommended: [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols),
   so the symbols of each bill reach the payment lines on their own (see
   [module:account_abo](module:account_abo#setup) for how).

Check with your bank which of the formats your contract covers — CFU, CFA and
MT101 are often arranged separately.

## Making a payment file {#usage}

1. Paying vendors: *Accounting → Vendors → Payment Orders*. Collecting by
   direct debit: *Accounting → Customers → Debit Orders*.
2. **New**, choose the MultiCash payment mode, **Create Payment Lines from
   Journal Items**.
3. Check **Variable Symbol**, **Constant Symbol** and **Specific Symbol** on
   the lines. An empty one is taken from a `VS:` / `KS:` / `SS:` token in the
   *Communication*; if there is none, the file carries `0`. For a CFA payment
   set **Priority** (*Urgent* for express processing) and **Charge Bearer**
   (*Shared*, *Payer*, *Beneficiary*) on the line; they default to normal and
   shared.
4. **Confirm Payments**, **Generate Payment File**. The file is attached to
   the order as `<format>-<journal code>-<date and time>.<extension>`.
5. Import the file into MultiCash, send it to the bank from there, and mark
   the order with **File Successfully Uploaded**.

The order stops at the **first** problem it finds — a line without a bank
account, a line with a zero or negative amount, a non-CZK line in CFD/CFU, an
account that is not Czech where one is required, a missing BIC, and for MT101
lines dated differently.

## Enterprise batch payments {#batch}

[module:account_multicash_batch](module:account_multicash_batch) writes the
same files from an Enterprise **batch payment**, with one payment method per
format under the same names.

- When it is installed, the bank journals of companies whose fiscal country is
  the Czech Republic get the two **CFD** methods (outgoing transfer, incoming
  direct debit); so do new bank journals of such companies. Journals of other
  countries do not get them, but can add them by hand. **CFU, CFA and MT101 you add
  to the journal yourself** (*Outgoing Payments* tab), once your bank has set
  them up for you.
- Register the payments with the method of the format you want, group them in
  a batch (*Accounting → Vendors → Batch Payments*, or *Customers* for direct
  debits) and press **Validate**. The file is attached to the batch's chatter.
- Before writing the file the batch lists **every** unusable payment: no
  recipient bank account, zero amount, for CFD/CFU a payment not in CZK or a
  recipient account that is not Czech, for CFA/MT101 a payment without a
  partner (the beneficiary's name and address would be empty).
- MT101 has one execution date for the whole message, so every payment is
  executed on the **batch date**, with a warning for payments dated
  otherwise. CFD, CFU and CFA keep each payment's own date.
- The urgency (*priority*) and the charge bearer of a CFA payment come from
  the payment's ISO 20022 fields when Odoo's ISO 20022 module is installed.

Both modules can be installed side by side.

## Limitations {#limitations}

- A credit note grouped with its invoice on the payment order (the payment
  mode's *Group Transactions in Payment Orders*) becomes **one item of the net
  amount** — the amount of the payment the order books. It carries the
  invoice's variable symbol; when one credit note is netted against several
  invoices their symbols differ and none is sent. Groups without a credit note
  keep one item per invoice. Without grouping, a credit-note line is refused.
- **Czech domestic formats.** CFD and CFU take only CZK and Czech accounts; a
  Slovak IBAN is refused. CFA also needs the ordering account to be Czech.
- **MT101 from a payment order** has one execution date for the whole
  message, so an order whose lines carry different dates is refused — set the
  order's *Payment Execution Date Type* to *Fixed Date* or *Immediately*, or
  split it.
- Characters outside code page 852 (CFD, CFU, CFA) or ASCII (MT101) are
  reduced to their plain letters; MT101 also drops characters outside the
  SWIFT set.
- The file is not uploaded to the bank automatically; MultiCash does that.
- Only the Česká spořitelna layout was used as the specification. Other banks'
  MultiCash imports usually accept it, but test one file with your bank first.
