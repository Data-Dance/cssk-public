{
    'name': "ABO Payment Export",
    'summary': "Export Czech/Slovak domestic credit transfers in the ABO file format",
    'description': """
Generates ABO payment-order files used by Czech (and Slovak) banks
(Česká spořitelna, ČSOB, KB, MONETA, Raiffeisenbank, UniCredit, …).

Scope:
    * Export of credit transfers (úhrady, data type 1501) as a payment file on
      an OCA ``account.payment.order`` (CE-clean — no Enterprise dependency)
    * Batch (hromadný) record arrangement — orderer account in the group header
    * VS / KS / SS on each payment line (with memo/communication fallback)
    * Encoding: WIN1250 with ASCII fallback
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
