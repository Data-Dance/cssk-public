============================
ISDOC for Sales (proforma)
============================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :alt: License: AGPL-3

**Export a sale order as an ISDOC proforma (zálohová faktura, DocumentType 4)**

In Odoo a pro-forma is not a separate record but a sale order rendered as a
pro-forma document. This bridge lets such a sale order be exported as an ISDOC
6.0.2 proforma (DocumentType 4 — zálohová faktura, a request for advance payment).

Incoming proformas are decoded by the base module (account_edi_isdoc) into a
draft vendor bill, since a proforma is not a bookable tax document.

.. rubric:: Module facts

- **Technical name:** ``account_edi_isdoc_sale``
- **Version:** 18.0.1.0.0
- **Licence:** AGPL-3
- **Requires:** ``account_edi_isdoc``, ``sale``

Authors: Data Dance s.r.o.
