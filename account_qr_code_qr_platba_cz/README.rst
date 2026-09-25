============================
QR Platba (Czech Republic)
============================

Adds the Czech **QR Platba** payment QR code to Odoo invoices. QR Platba is the
Czech Banking Association short-payment-descriptor (SPD) standard supported by
every Czech banking app: the customer scans the code on the invoice and the
payment form is pre-filled (IBAN, amount, currency, message and the variable
symbol).

The code is generated **offline** — it builds the SPD string
(``SPD*1.0*ACC:...*AM:...*CC:...``) directly from the invoice data and renders
it as a QR code, with **no external service**. It registers as an extra
payment-QR method on ``res.partner.bank`` and reuses Odoo's standard
QR-code-on-invoice plumbing, so it works on both Community and Enterprise.

Features
========

* New **QR Platba (Czech Republic)** payment-QR method on every bank account.
* Pure-offline SPD generator per the CBA *QR Platba* standard 1.2 — no network
  dependency.
* Encodes IBAN, amount, currency, message and the variable-symbol reference
  (digits-only ``RF`` field) from the invoice.
* Branded QR frame on the printed invoice.
* Eligibility checks: CZK currency or a Czech debtor, IBAN account in a SEPA
  country, and a beneficiary name present.

Usage
=====

#. Go to *Settings ▸ Invoicing ▸ Customer Payments* and enable **QR Codes**.
#. On a customer invoice, open *Other Info ▸ Payment QR-code* and pick
   **QR Platba (Czech Republic)**.
#. The QR code is rendered on the invoice PDF; the customer scans it in their
   banking app to pay.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
