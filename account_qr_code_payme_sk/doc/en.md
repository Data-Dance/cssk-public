---
title: payme (Slovakia)
summary: Prints a Slovak payme payment link as a QR code on customer invoices; scanning it opens the customer's banking app with the payment filled in.
verified: 19.0.1.2.1
---

## What it is for {#purpose}

**payme** is the payment link standard of the Slovak Banking Association
(*Slovenská banková asociácia*): a `payme.sk` web address that carries the
account, amount and payment identification. This module prints that link as a
QR code on your invoices. The customer scans it with the phone camera or a
banking app, and their banking app opens with the payment filled in.

What the national formats have in common — switching QR codes on, the bank
account they need and how Odoo picks a format for each invoice — is described
in [module:account_qr_code_frame_provider](module:account_qr_code_frame_provider),
installed with this module.

## Setting it up {#setup}

1. Switch on *QR Codes* in *Accounting → Configuration → Settings* — see
   [the common setup](module:account_qr_code_frame_provider#setup).
2. Use a bank account in **IBAN** form from a SEPA country, with an *Account
   Holder Name*.
3. Invoice in **EUR**. payme is not offered for other currencies.

Odoo picks payme **automatically** for a euro invoice when both your company
and the customer are in Slovakia (or the customer's country is not filled in)
and PAY by square is not installed. Otherwise pick *payme (Slovensko)* in the
invoice's *Payment QR-code* field — see
[Which format an invoice gets](module:account_qr_code_frame_provider#method-choice).

## What the link contains {#content}

| Value | Taken from |
|---|---|
| IBAN | the invoice's *Recipient Bank* account |
| Amount, currency | the amount still open on the invoice, EUR |
| Payment identification | with [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#qr) installed and symbols on the invoice: `/VS…/SS…/KS…`; otherwise the *Payment Reference* or the invoice number. At most 35 characters. |
| Creditor's name | *Account Holder Name* of the account, or the name of its owner; at most 70 characters |
| Message | the *Payment Reference*, or the invoice number when there is none |

The code is drawn inside the payme frame.

## Limitations {#limitations}

- No due date is passed; the banking app proposes its own payment date.
- Euro only.
- With PAY by square also installed, PAY by square is the one Odoo picks
  automatically; see
  [the common limitations](module:account_qr_code_frame_provider#limitations).
