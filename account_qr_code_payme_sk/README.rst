==================
payme (Slovakia)
==================

Adds the Slovak **payme** payment QR code to Odoo invoices. payme is the Slovak
Banking Association payment-link standard: the QR code carries a
``https://payme.sk/...`` link that opens the customer's banking app with the
payment pre-filled (IBAN, amount, currency, payment identification, creditor
name and an optional message).

The link is assembled locally from the invoice data — the module builds the
payme URL per the SBA *Payment Link* standard 2.0 and renders it as a QR code.
It registers as an extra payment-QR method on ``res.partner.bank`` and reuses
Odoo's standard QR-code-on-invoice plumbing, so it works on both Community and
Enterprise.

Features
========

* New **payme (Slovakia)** payment-QR method on every bank account.
* Builds the payme payment link per the SBA *Payment Link* standard 2.0.
* Encodes IBAN, amount, currency (EUR), payment identification, creditor name
  and an optional message from the invoice.
* Branded payme QR frame on the printed invoice.
* Eligibility checks: EUR currency, IBAN account in a SEPA country, and a
  beneficiary name present.

Usage
=====

#. Go to *Settings ▸ Invoicing ▸ Customer Payments* and enable **QR Codes**.
#. On a customer invoice, open *Other Info ▸ Payment QR-code* and pick
   **payme (Slovakia)**.
#. The QR code is rendered on the invoice PDF; the customer scans it in their
   banking app to pay.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
