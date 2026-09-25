============================
PAY by square (Slovakia)
============================

Adds the Slovak **PAY by square** payment QR code to Odoo invoices. PAY by
square is the Slovak Banking Association standard used by every Slovak banking
app: the customer scans the code on the invoice and the payment form is
pre-filled (IBAN, amount, currency, beneficiary, message).

The code is generated **offline** — it builds the PAY by square sequence
(CRC32 checksum, LZMA1/XZ compression, base32 encoding) entirely in Python and
does **not** call any external service. It registers as an extra payment-QR
method on ``res.partner.bank`` and reuses Odoo's standard QR-code-on-invoice
plumbing, so it works on both Community and Enterprise.

Features
========

* New **PAY by square (Slovakia)** payment-QR method on every bank account.
* Pure-offline generator per the SBA *PAY by square* specification 1.1.0 — no
  network dependency.
* Encodes IBAN, amount, currency, beneficiary name and the payment message
  (variable symbol / structured reference) from the invoice.
* Branded QR frame for the printed invoice.
* Eligibility checks: EUR currency, IBAN account in a SEPA country, and a
  beneficiary name present.

Usage
=====

#. Go to *Settings ▸ Invoicing ▸ Customer Payments* and enable **QR Codes**.
#. On a customer invoice, open *Other Info ▸ Payment QR-code* and pick
   **PAY by square (Slovakia)**.
#. The QR code is rendered on the invoice PDF; the customer scans it in their
   banking app to pay.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
