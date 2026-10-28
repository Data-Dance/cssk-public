---
title: ABO Payment Files
summary: Domestic CZK credit transfers exported as an ABO file for upload to the bank, from an OCA payment order or an Enterprise batch payment.
verified: 19.0.2.1.0
---

## What it is for {#purpose}

**ABO** is the fixed-layout text file that Czech banks accept for a batch of
domestic credit transfers (*hromadný příkaz k úhradě*). Instead of keying
payments into internet banking one by one, you collect the vendor bills you
want to pay in Odoo, generate one ABO file and upload it to the bank.

This module writes that file from an OCA **payment order**
(`account_payment_order`), so it works on Community without any Enterprise
module. On Enterprise, [module:account_abo_batch](module:account_abo_batch)
writes the same file from a **batch payment** instead — see
[below](#batch).

What it writes:

| | |
|---|---|
| Record type | credit transfers (*úhrady*), ABO data type `1501` |
| Arrangement | batch: the payer's account is stated once, in the group header |
| Currency | CZK only |
| Accounts | Czech accounts only — a `CZ` IBAN or `[prefix-]number/bank code` |
| Encoding | Windows-1250, CR LF line ends; characters it cannot hold are reduced to plain ASCII |
| File name | `ABO-<journal code>-<date and time>.abo` |

The file is not sent anywhere: you download it and upload it in your bank's
internet or direct banking yourself. With Fio banka you can also send it from
Odoo — see [module:account_payment_fio](module:account_payment_fio#send).

## Setting it up {#setup}

1. **The bank journal** (*Accounting → Configuration → Accounting → Journals*)
   must have its bank account filled in, as a Czech IBAN or as
   `prefix-number/bank code`. This is the account the money leaves.
2. **A payment mode** (*Accounting → Configuration → Accounting → Payment
   Modes*): choose the payment method **ABO (Czech credit transfer)**
   and the bank journal from step 1.
3. **Every vendor** you pay needs a bank account in Odoo, again as a Czech IBAN
   or `prefix-number/bank code`.
4. Recommended: install
   [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols). Its
   add-on [module:l10n_cssk_payment_symbols_payment_order](module:l10n_cssk_payment_symbols_payment_order)
   then installs itself and copies each bill's variable, constant and specific
   symbol onto the payment order lines, so you do not have to type them.

## Paying bills with a payment order {#usage}

1. *Accounting → Vendors → Payment Orders*, **New**, choose the ABO payment
   mode.
2. **Create Payment Lines from Journal Items** and pick the bills to pay.
3. Check the lines. Each has **Variable Symbol**, **Constant Symbol** and
   **Specific Symbol** next to *Communication*.
4. **Confirm Payments**, then **Generate Payment File**. The `.abo` file is
   attached to the order.
5. Upload the file in your bank, authorise it there, and mark the order with
   **File Successfully Uploaded**.

### Where the symbols come from {#symbols}

For every line, each symbol is taken from, in this order:

1. the symbol field on the payment line;
2. a token in the line's *Communication*: `VS:12345`, `VS 12345`, `VS=12345`
   (likewise `KS:` and `SS:`);
3. nothing — the file then carries `0`.

A symbol field accepts digits only, up to 10 for VS and SS and 4 for KS.
How the symbols get onto the bills in the first place is described in
[module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#invoices).

The *Communication* also becomes the message for the beneficiary: whitespace
collapsed, characters that banks reject in ABO messages (such as `@ # ; § ! & _ * = + ? [ ]`)
removed, and cut to 35 characters.

## What is checked {#checks}

Generating the file stops with a message when:

- a line has no beneficiary bank account;
- a line is not in CZK;
- the journal's or a beneficiary's account is not a Czech account (a Slovak
  IBAN is refused);
- the journal has no bank account.

The payment order stops at the **first** problem; fix it and generate again.
The Enterprise variant lists every problem at once — see [below](#batch).

## Enterprise batch payments {#batch}

[module:account_abo_batch](module:account_abo_batch) produces the identical
file from an Enterprise **batch payment** (`account_batch_payment`).

- When it is installed, the bank journals of companies whose fiscal country is
  the Czech Republic get the outgoing payment method **ABO (Czech credit
  transfer)** (on the journal's *Outgoing Payments* tab). Bank journals created
  later for such a company get it too; another country's journals can add it
  by hand.
- Register vendor payments on that journal with that payment method, put them
  into a batch (*Accounting → Vendors → Batch Payments*) and press
  **Validate**. The file is generated and attached to the batch's chatter.
- The symbols come from the payment's own VS/KS/SS fields
  ([module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#payments)
  fills them from the paid bill), else from a `VS:` token in the *Memo*.
- Before writing the file, the batch lists **every** payment that would make
  it unusable: no recipient bank account, not in CZK, recipient account not
  Czech, zero amount.
- It warns, without blocking, about payments with no variable symbol (they go
  out as `VS 0`, which the bank accepts but the payee cannot match) and about
  payments dated differently from the batch.
- **All payments are executed on the batch date**, because an ABO file has
  one due date for all its items.

Both modules can be installed side by side.

## The shared builder {#format}

The ABO and MultiCash writers live in
[module:account_cz_bankfile_base](module:account_cz_bankfile_base), so the
Community and Enterprise variants produce byte-identical files. The same
module reads Czech account numbers in both spellings (IBAN and
`prefix-number/bank code`) for the KB BEST and Fio modules and for the MT940
and KB statement imports. It has no screen of its own.

## Limitations {#limitations}

- A credit note grouped with its invoice on the payment order (the payment
  mode's *Group Transactions in Payment Orders*) becomes **one item of the net
  amount** — the amount of the payment the order books. It carries the
  invoice's variable symbol; when one credit note is netted against several
  invoices their symbols differ and none is sent. Groups without a credit note
  keep one item per invoice. Without grouping, a credit-note line is refused.
- **CZK and Czech accounts only.** The file refuses any currency other
  than CZK and any non-Czech account, Slovak IBANs included. Pay in EUR through SEPA (ISO 20022) or
  [module:account_multicash](module:account_multicash) (CFA).
- **One due date per file.** A payment order whose lines carry different
  dates is refused with a message listing them, rather than executing every
  line on the first one's date. The default *Payment Execution Date Type*,
  *Due Date*, gives every line its own bill's due date — so set it to *Fixed
  Date* or *Immediately* when paying by ABO, or split the order.
- Only credit transfers. ABO direct debits (*inkaso*) are not written; use
  MultiCash CFD or KB BEST for those.
- A line with a zero or negative amount stops the export with a message
  naming it (banks reject such a file).
- The file is not uploaded to the bank automatically (except through Fio, as
  above).
