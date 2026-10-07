# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "ISDOC Import — Received Advance Invoices",
    "version": "19.0.1.0.0",
    "summary": "Route imported ISDOC advance documents (DocumentType 4/5/6) "
               "into the received-advances flow.",
    "description": """
ISDOC Import — Received Advance Invoices
========================================

Wires the ISDOC import into ``purchase_order_advance_invoice``:

* **DocumentType 4** (zálohová faktura — non-tax proforma): a received
  advance ``purchase.order`` is created from the document (supplier,
  gross amount, supplier's number) instead of leaving only a vendor
  bill — a proforma must not be posted as a bill. The draft bill the
  import framework creates is kept for reference, linked to the advance
  and flagged in the chatter.
* **DocumentType 5** (daňový doklad k přijaté platbě): the imported bill
  is registered as an advance tax document — moved to the advance
  journal, ``taxable_supply_date`` taken from ``TaxPointDate``, product
  lines rewritten to the paid-advances account, the payable leg to the
  advance clearing account, and linked to the matching open advance
  (by order reference, variable symbol, or unique paid amount — with an
  ambiguity bail-out).
* **DocumentType 6** (opravný doklad k zálohovému): same journal/date/
  account treatment as 5, as a vendor credit note.

Auto-installs when both ``account_edi_isdoc`` and
``purchase_order_advance_invoice`` are present.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["account_edi_isdoc", "purchase_order_advance_invoice"],
    "data": [
        "data/product_data.xml",
    ],
    "auto_install": True,
    "installable": True,
}
