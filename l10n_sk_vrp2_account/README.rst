================================
Slovak VRP2 - Invoice Payments
================================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :alt: License: AGPL-3

**Fiscalize customer invoices through the Slovak Virtual Cash Register (VRP 2)**

Issue Slovak VRP 2 fiscal receipts ("pokladničný doklad — úhrada faktúry") for
customer invoices and retain them in Odoo. The Odoo payment/reconciliation is
handled by your normal flow; this module only fiscalizes.

- "Fiscalize in VRP2" on the invoice form (single invoice) and as a list mass
  action (many invoices → one merged PDF of the official VRP2 receipts).
- 0.05 € cash rounding driven by the register's "Zaokrúhľovať na 5 centov"
  setting.
- Storno: cancel the fiscal receipt of a fiscalized invoice.
- Hidden "VRP2 Fiscalized" column on the invoice list.
- Stores every receipt as a ``vrp2.receipt`` record (number, fiscal codes,
  QR, raw request/response) with a printable report.
- No POS dependency.

.. rubric:: Module facts

- **Technical name:** ``l10n_sk_vrp2_account``
- **Version:** 18.0.2.2.0
- **Licence:** AGPL-3
- **Requires:** ``l10n_sk_vrp2_base``, ``account``

Authors: Data Dance s.r.o.
