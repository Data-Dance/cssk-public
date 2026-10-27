---
title: QR Platba (Czech Republic)
summary: Prints the Czech QR Platba payment code on customer invoices, with the variable, constant and specific symbols as separate values.
verified: 19.0.1.1.3
---

## What it is for {#purpose}

**QR Platba** is the payment QR code standard of the Czech Banking Association
(*Česká bankovní asociace*), built on the Short Payment Descriptor (SPD)
format. Every Czech banking app reads it: the customer scans the code on your
invoice and gets a payment order with your account, the amount and the
variable symbol filled in.

This module adds QR Platba as a QR format for Odoo invoices. What the national
formats have in common — switching QR codes on, the bank account they need and
how Odoo picks a format for each invoice — is described in
[module:account_qr_code_frame_provider](module:account_qr_code_frame_provider),
installed with this module.

## Setting it up {#setup}

1. Switch on *QR Codes* in *Accounting → Configuration → Settings* — see
   [the common setup](module:account_qr_code_frame_provider#setup).
2. Enter the bank account in **IBAN** form (for example `CZ65 0800 …`), not
   as a domestic number with a bank code, and fill in the *Account Holder
   Name*. The IBAN must be from a SEPA country.

QR Platba comes **first** in Odoo's automatic choice and is used for every
invoice that is **in CZK, or addressed to a customer in the Czech Republic**
in any currency. Other invoices fall through to the next format. You can
always pick *QR Platba (Czech Republic)* — the label is shown in English — in
the invoice's *Payment QR-code* field yourself; see
[Which format an invoice gets](module:account_qr_code_frame_provider#method-choice).

## What the code contains {#content}

| SPD field | Taken from |
|---|---|
| `ACC` account | the IBAN of the invoice's *Recipient Bank* account |
| `AM` amount, `CC` currency | the amount still open on the invoice, in the invoice currency |
| `MSG` message for the payee | the *Payment Reference*, or the invoice number when there is none; first 60 characters, with `*` written as `%2A` and `%` as `%25` as the standard prescribes |
| `RF` payee's reference | the variable symbol, or else the digits of the message; at most 16 digits |
| `RN` payee's name | *Account Holder Name*, or the name of the account's owner; escaped like `MSG` |
| `X-VS`, `X-SS`, `X-KS` | the invoice's variable, specific and constant symbols, with [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#qr) installed |

The code is drawn inside the QR Platba frame.

## Limitations {#limitations}

- No due date (`DT`) is passed; the banking app proposes its own payment date.
- QR Platba is chosen for any invoice to a Czech customer, also in euro and
  also when your company is Slovak. Pick another format on the invoice if you
  do not want that.
- Without the payment symbols module there are no `X-VS`/`X-SS`/`X-KS`
  fields; the variable symbol then reaches the customer only through `RF` and
  the message, if the reference contains it.
