{
    'name': "MultiCash Payment Export",
    'summary': "Export payments in MultiCash formats (CFD/CFU/CFA/MT101) for Czech banks",
    'description': """
Generates MultiCash payment files used by Czech banks (Česká spořitelna, KB, ČSOB, Raiffeisenbank, UniCredit and others).

Supported formats:
    * CFD - domestic Czech credit transfers and direct debits (inkasa)
    * CFU - urgent domestic Czech credit transfers
    * CFA - foreign (cross-border) payments
    * MT101 - SWIFT Request For Transfer

Hooks onto the OCA ``account.payment.order`` (CE-clean — no Enterprise
dependency).
    """,
    'author': "Data Dance s.r.o.",
    'website': "https://www.datadance.eu",
    'category': 'Accounting/Accounting',
    'version': '19.0.2.0.0',
    'depends': ['account_payment_order', 'account_cz_bankfile_base', 'base_iban'],
    'data': [
        'data/account_payment_method.xml',
        'views/account_payment_line_views.xml',
    ],
    'license': "AGPL-3",
}
