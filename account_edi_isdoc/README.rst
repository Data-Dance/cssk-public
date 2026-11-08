========================================
Import/Export Czech e-invoices (ISDOC)
========================================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :alt: License: AGPL-3

**Import and export ISDOC 6.0.2 electronic invoices (Czech national e-invoicing standard)**

Adds the Czech national e-invoicing format **ISDOC 6.0.2** to Odoo's electronic
invoice import/export, alongside the standard UBL/CII formats.

The format can be selected per customer (Invoicing tab) and is offered for
companies established in the Czech Republic. Supported representations:

* plain ``.isdoc`` XML
* ``.isdocx`` archive (ISDOC + manifest + PDF)
* ISDOC embedded into a PDF/A-3 document

This module hooks into ``account_edi_ubl_cii`` so it reuses the existing
send/print and bill-import plumbing.

.. rubric:: Module facts

- **Technical name:** ``account_edi_isdoc``
- **Version:** 18.0.1.0.2
- **Licence:** AGPL-3
- **Requires:** ``account_edi_ubl_cii``, ``l10n_cz_base``

Authors: Data Dance s.r.o.
