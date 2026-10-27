---
title: PAY by square (Slovakia)
summary: Prints the Slovak PAY by square payment QR code on customer invoices, with the variable, constant and specific symbols as separate values.
verified: 19.0.1.2.2
---

## What it is for {#purpose}

**PAY by square** is the payment QR code standard of the Slovak Banking
Association (*Slovenská banková asociácia*). Every Slovak banking app reads it:
the customer scans the code on your invoice and gets a payment order with your
account, the amount and the payment symbols filled in.

This module adds PAY by square as a QR format for Odoo invoices. What the
national formats have in common — switching QR codes on, the bank account they
need and how Odoo picks a format for each invoice — is described in
[module:account_qr_code_frame_provider](module:account_qr_code_frame_provider),
installed with this module.

## Setting it up {#setup}

1. Switch on *QR Codes* in *Accounting → Configuration → Settings* — see
   [the common setup](module:account_qr_code_frame_provider#setup).
2. Use a bank account in **IBAN** form from a SEPA country, with an *Account
   Holder Name*. Fill in its bank's BIC (*Bank Identifier Code*) if you want it
   in the code; it is optional.
3. Invoice in **EUR**. PAY by square is not offered for other currencies.

Odoo picks PAY by square **automatically** for a euro invoice when both your
company and the customer are in Slovakia (or the customer's country is not
filled in). For any other invoice you can still pick *PAY by square
(Slovensko)* in the invoice's *Payment QR-code* field — see
[Which format an invoice gets](module:account_qr_code_frame_provider#method-choice).

## What the code contains {#content}

| Value in the code | Taken from |
|---|---|
| IBAN, BIC | the invoice's *Recipient Bank* account |
| Beneficiary name | *Account Holder Name* of that account, or the name of its owner |
| Amount, currency | the amount still open on the invoice, EUR |
| Variable, constant, specific symbol | the invoice's symbols, with [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#qr) installed |
| Originator's reference | the *Payment Reference* (or the invoice number) — only when the invoice has no symbols, as the standard prescribes |
| Payment note | the *Payment Reference*, or the invoice number when there is none |
| Due date | the invoice's due date; today, if that date has already passed |

The code is a one-off payment: no standing order, no direct debit. It is drawn
inside the PAY by square frame so that the customer recognises it.

## Limitations {#limitations}

- The beneficiary's address is not included.
- Euro only, and only one bank account per code.
- With payme also installed, PAY by square is the one Odoo picks
  automatically; see
  [the common limitations](module:account_qr_code_frame_provider#limitations).
