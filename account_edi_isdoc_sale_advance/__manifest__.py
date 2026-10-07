{
    'name': "ISDOC for Czech Advance Invoices",
    'version': '19.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': "Map the Czech advance-payment documents to ISDOC DocumentType 4/5/6",
    'description': """
ISDOC mapping for Czech advance invoices
=======================================

Integrates `sale_order_advance_invoice` (zálohová faktura) with ISDOC:

* zálohová faktura — an ``is_advance_invoice`` sale order — exports as ISDOC
  **DocumentType 4** (non-VAT proforma), via account_edi_isdoc_sale.
* daňový doklad k přijaté platbě — the tax document created in the advance journal
  (``is_advance_invoice_tax_document``) — exports as **DocumentType 5** (with VAT),
  its credit note as **6**.
* the final invoice deducts the advances: the ``is_advance_tracking`` deduction
  lines are reported as ``TaxedDeposits`` / already-claimed amounts on a normal
  **DocumentType 1** invoice, each referencing its tax document.
""",
    'depends': ['account_edi_isdoc_sale', 'sale_order_advance_invoice'],
    'data': [],
    'installable': True,
    'auto_install': True,
    'author': "Data Dance s.r.o.",
    "license": "AGPL-3",
}
