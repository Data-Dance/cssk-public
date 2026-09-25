{
    'name': "CZ/SK Bank File Formats — shared builders",
    'summary': "Shared ABO and MultiCash payment-file builders. The CE "
               "(account_payment_order) and EE (account_batch_payment) variants "
               "of account_abo / account_multicash both build on this.",
    'description': """
Single source of truth for the Czech/Slovak bank payment-file formats:

* ``utils.abo.build_abo_file`` — ABO credit-transfer (úhrada) file
* ``utils.multicash.build_multicash_file`` — MultiCash CFD/CFU/CFA/MT101
* ``utils.common`` — Czech account parsing, the normalized ``BankPaymentItem``
  passed to the builders, and the VS/KS/SS symbol resolver.

The builders take a list of ``BankPaymentItem`` (plain values + bank records),
so the edition-specific shims feed them from either ``account.payment.line``
(OCA payment order, CE) or ``account.payment`` (Enterprise batch payment, EE)
without duplicating any format logic. No models — pure helpers imported via
``odoo.addons.account_cz_bankfile_base.utils.*``.
    """,
    'author': "Data Dance s.r.o.",
    'website': "https://www.datadance.eu",
    'category': 'Accounting/Accounting',
    'version': '19.0.1.3.1',
    'depends': ['base_iban'],
    'license': "AGPL-3",
}
