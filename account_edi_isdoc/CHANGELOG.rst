=========
Changelog
=========

All notable changes to **account_edi_isdoc** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Carry-over to 19.0
~~~~~~~~~~~~~~~~~~

- **Mark 19.0's "Carry-over to 18.0 — TaxPointDate export/import" DISCHARGED**
  (ported below). Its question is answered: ``taxable_supply_date`` is core on
  19.0 but comes from ``l10n_cssk_core`` on 18.0, and this module's
  dependencies (``account_edi_ubl_cii``, ``l10n_cz_base``) do not reach it, so
  both the export and the import read it only where it exists — the guard
  ``account_edi_isdoc_purchase_advance`` already used.

[18.0.1.0.2] — 2026-10-24
-------------------------

Fixed
~~~~~

- **TaxPointDate carried the issue date, not the DUZP.** The export wrote
  ``invoice_date``, so a supply delivered on the 30th and invoiced on the 3rd
  told the recipient to book it in the wrong VAT period. It now writes
  ``taxable_supply_date``, falling back to the invoice date — and, on this
  series, where ``l10n_cssk_core`` is not installed the issue date is the only
  tax point there is.
- **An imported vendor bill ignored TaxPointDate.** Only the advance tax
  document (``account_edi_isdoc_purchase_advance``) read it; every ordinary
  bill now takes its DUZP from it. The deduction period
  (``cssk_vat_deduction_date``) is deliberately not set: it is when *we*
  claim, which the supplier's document cannot know.
- **The VAT summary could be a cent off the invoice under round_globally**
  (cssk-public#11), the Czech default. Each rate's ``TaxAmount`` was the
  lines' own totals summed, and a line's total is rounded on its own: three
  lines of 1.03 at 21 % gave 0.66 of VAT on an invoice that booked 0.65, so
  the summary and ``PayableAmount`` disagreed. The summary and the document
  totals now come from the invoice's rounded base lines (the booked tax
  lines spread over its lines, as core's UBL builders aggregate), rounded
  over the regular lines and the deducted advances together; the sale-order
  proforma rounds as the order's own totals do.
  ``_get_rounded_base_and_tax_lines``, ``_add_tax_details_in_base_lines`` and
  ``_round_base_lines_tax_details`` all exist on 18.0 at the same signatures,
  so the rework needed no adaptation.

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
