=========
Changelog
=========

All notable changes to **account_edi_isdoc** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[18.0.1.0.1] — 2026-07-18
-------------------------

Added
~~~~~

- Import now also writes ``VariableSymbol`` / ``ConstantSymbol`` /
  ``SpecificSymbol`` onto the invoice symbol fields (digits-sanitised);
  previously the VS went into ``payment_reference`` only and KS/SS were
  dropped.

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Adds the Czech national e-invoicing format **ISDOC 6.0.2** to Odoo's electronic
  invoice import/export, alongside the standard UBL/CII formats, by hooking into
  ``account_edi_ubl_cii`` (reuses existing send/print and bill-import plumbing).
- Export of customer invoices and credit notes as ISDOC; the format is selectable
  per customer (Invoicing tab) and offered for companies established in the CZ.
- Import (decode) of incoming ISDOC documents into draft vendor bills.
- Supported representations: plain ``.isdoc`` XML, ``.isdocx`` archive
  (ISDOC + manifest + PDF), and ISDOC embedded into a PDF/A-3 document.
