==================================
ISDOC for Czech Advance Invoices
==================================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :alt: License: AGPL-3

**Map the Czech advance-payment documents to ISDOC DocumentType 4/5/6**

Integrates `sale_order_advance_invoice` (zálohová faktura) with ISDOC:

* zálohová faktura — an ``is_advance_invoice`` sale order — exports as ISDOC
  **DocumentType 4** (non-VAT proforma), via account_edi_isdoc_sale.
* daňový doklad k přijaté platbě — the tax document created in the advance journal
  (``is_advance_invoice_tax_document``) — exports as **DocumentType 5** (with VAT),
  its credit note as **6**.
* the final invoice deducts the advances: the ``is_advance_tracking`` deduction
  lines are reported as ``TaxedDeposits`` / already-claimed amounts on a normal
  **DocumentType 1** invoice, each referencing its tax document.

.. rubric:: Module facts

- **Technical name:** ``account_edi_isdoc_sale_advance``
- **Version:** 18.0.1.0.0
- **Licence:** AGPL-3
- **Requires:** ``account_edi_isdoc_sale``, ``sale_order_advance_invoice``

Authors: Data Dance s.r.o.
