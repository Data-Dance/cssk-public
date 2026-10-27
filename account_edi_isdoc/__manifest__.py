{
    'name': "Import/Export Czech e-invoices (ISDOC)",
    'version': '19.0.1.4.0',
    'category': 'Accounting/Accounting',
    'summary': "Import and export ISDOC 6.0.2 electronic invoices (Czech national e-invoicing standard)",
    'description': """
ISDOC electronic invoicing
==========================

Adds the Czech national e-invoicing format **ISDOC 6.0.2** to Odoo's electronic
invoice import/export, alongside the standard UBL/CII formats.

A Czech customer without an *eInvoice format* of its own gets ISDOC, unless
it is known to be on Peppol (then Peppol BIS 3). Any customer can be set to
ISDOC by hand (Invoicing tab, *eInvoice format*).
Supported representations:

* plain ``.isdoc`` XML (sent and imported)
* ``.isdocx`` archive (ISDOC + manifest + PDF): imported, and downloadable
  from a posted customer invoice (*Action → Download ISDOCX*)
* ISDOC embedded into a PDF/A-3 document (sent and imported)

This module hooks into ``account_edi_ubl_cii`` so it reuses the existing
send/print and bill-import plumbing.
    """,
    'depends': ['account_edi_ubl_cii', 'l10n_cz_base'],
    'data': [
        'data/ir_actions_server.xml',
    ],
    'installable': True,
    'auto_install': False,
    'author': "Data Dance s.r.o.",
    "license": "AGPL-3",
}
