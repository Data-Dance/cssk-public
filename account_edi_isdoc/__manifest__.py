{
    'name': "Import/Export Czech e-invoices (ISDOC)",
    'version': '19.0.1.2.0',
    'category': 'Accounting/Accounting',
    'summary': "Import and export ISDOC 6.0.2 electronic invoices (Czech national e-invoicing standard)",
    'description': """
ISDOC electronic invoicing
==========================

Adds the Czech national e-invoicing format **ISDOC 6.0.2** to Odoo's electronic
invoice import/export, alongside the standard UBL/CII formats.

The format can be selected per customer (Invoicing tab) and is offered for
companies established in the Czech Republic. Supported representations:

* plain ``.isdoc`` XML
* ``.isdocx`` archive (ISDOC + manifest + PDF)
* ISDOC embedded into a PDF/A-3 document

This module hooks into ``account_edi_ubl_cii`` so it reuses the existing
send/print and bill-import plumbing.
    """,
    'depends': ['account_edi_ubl_cii', 'l10n_cz_base'],
    'data': [],
    'installable': True,
    'auto_install': False,
    'author': "Data Dance s.r.o.",
    "license": "AGPL-3",
}
