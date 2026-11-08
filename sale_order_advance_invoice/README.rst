============================
Sale Order Advance Invoice
============================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :alt: License: AGPL-3

**Advance invoices (proforma) with tax documents on received payments**

Country-neutral engine for the advance-invoice / proforma flow used in Czech and
Slovak accounting (zálohová / preddavková faktura): an advance is its own sale
order, payable by QR or manual payment, that produces a tax document on the
received payment and is settled (deducted) on the final invoice.

Install a localization layer to wire the statutory accounts automatically:

* ``l10n_cz_sale_order_advance_invoice`` — Czech chart
* ``l10n_sk_sale_order_advance_invoice`` — Slovak chart

See the documentation in ``static/description``.

.. rubric:: Module facts

- **Technical name:** ``sale_order_advance_invoice``
- **Version:** 18.0.1.0.4
- **Licence:** AGPL-3
- **Requires:** ``sale``, ``sale_management``, ``account_payment``

Authors: Data Dance s.r.o.
