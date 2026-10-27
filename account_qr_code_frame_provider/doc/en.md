---
title: Czech and Slovak Payment QR Codes — Common Base
summary: What the Czech and Slovak payment QR codes on invoices have in common — switching them on, how the format is chosen for each invoice, and the branded frame.
verified: 19.0.1.1.1
---

## What it is for {#purpose}

Odoo can print a payment QR code on a customer invoice. The customer scans it
in their banking app and gets a payment order with the account, amount and
payment details already filled in. Each country has its own format:

| Format | Country | Module |
|---|---|---|
| QR Platba (*Short Payment Descriptor*) | Czech Republic | [module:account_qr_code_qr_platba_cz](module:account_qr_code_qr_platba_cz) |
| PAY by square | Slovakia | [module:account_qr_code_pay_by_square_sk](module:account_qr_code_pay_by_square_sk) |
| payme | Slovakia | [module:account_qr_code_payme_sk](module:account_qr_code_payme_sk) |
| SEPA Credit Transfer QR (EPC) | euro area | Odoo's own, installed with Accounting |

This module is what the three national formats share. It is installed with any
of them and has no settings. It:

- **chooses the right format** for each invoice when you leave the choice to
  Odoo (see [below](#method-choice));
- draws the national code **inside its scheme's frame** — the logo the
  customer recognises from their banking app;
- removes the Odoo logo that the standard invoice layout places over the
  middle of the payment QR code.

## Switching QR codes on {#setup}

1. *Accounting → Configuration → Settings*, block *Customer Payments*: tick
   **QR Codes**.
2. Install the format module(s) you need.
3. Make sure the bank account the customer should pay to is entered in **IBAN
   form** and has an *Account Holder Name* (or belongs to a contact with a
   name). A Czech domestic account number such as `123-4567890/0100` is not
   enough; enter its IBAN. This is the account shown as *Recipient Bank* on
   the invoice.

The code is printed on the PDF invoice as long as the invoice has an open
amount, and it is for **the amount still open**, so a partly paid invoice asks
only for the rest. A fully paid invoice prints no code.

With [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#qr)
installed, the invoice's variable, constant and specific symbols are passed to
the code as separate values; each format module describes where they end up.

## Which format an invoice gets {#method-choice}

The *Payment QR-code* field on the invoice's *Other Info* tab decides.

- **If you pick a format there**, it is used — or, when it cannot be used for
  that invoice (wrong currency, the account is not an IBAN), printing stops
  with a message saying so.
- **If you leave it empty**, Odoo takes the first format that suits the
  invoice, in this order, and stores it in the field:

| Order | Format | Used automatically when |
|---|---|---|
| 1 | QR Platba | the invoice is in CZK **or** the customer is in the Czech Republic |
| 2 | PAY by square | the invoice is in EUR **and** both your company (the account holder) and the customer are in Slovakia |
| 3 | payme | as PAY by square |
| 4 | SEPA Credit Transfer QR | the invoice is in EUR |

All formats also need an IBAN from a SEPA country. A party whose country is
not filled in does not count against a format: a Slovak company invoicing a
customer with no country still gets PAY by square.

So a Czech company's euro invoice to a German customer gets the SEPA code, a
Slovak company's invoice to a Czech customer gets QR Platba, and an invoice
between two Slovak companies gets the Slovak format.

Once a format has been stored on the invoice, it stays. Clear the field to
let Odoo choose again.

## Limitations {#limitations}

- **PAY by square comes before payme**, by a fixed rank rather than module
  load order: with both installed, PAY by square is the automatic choice
  between Slovak parties. To use payme on an invoice, pick it in *Payment
  QR-code*.
- QR Platba is chosen for any invoice to a Czech customer, also in euro and
  also when your company is not Czech.
- Only the payment QR code loses the Odoo logo. The separate payment-link QR
  code (*Add QR-code link on PDF*) is unchanged.
- The national formats are chosen automatically only on invoices. Elsewhere
  (for example a payment request generated from a bank account directly) the
  standard Odoo order applies.
