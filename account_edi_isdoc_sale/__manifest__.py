{
    'name': "ISDOC for Sales (proforma)",
    'version': '19.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': "Export a sale order as an ISDOC proforma (zálohová faktura, DocumentType 4)",
    'description': """
ISDOC proforma from sale orders
==============================

In Odoo a pro-forma is not a separate record but a sale order rendered as a
pro-forma document. This bridge lets such a sale order be exported as an ISDOC
6.0.2 proforma (DocumentType 4 — zálohová faktura, a request for advance payment).

Incoming proformas are decoded by the base module (account_edi_isdoc) into a
draft vendor bill, since a proforma is not a bookable tax document.
""",
    'depends': ['account_edi_isdoc', 'sale'],
    'data': [],
    'installable': True,
    'auto_install': True,
    'author': "Data Dance s.r.o.",
    "license": "AGPL-3",
}
