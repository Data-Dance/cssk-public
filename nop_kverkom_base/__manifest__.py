{
    "name": "NOP KVERKOM Base",
    "summary": "Transport layer for Slovak QR Platby (NOP KVERKOM): mTLS REST + transaction ledger",
    "description": """
Implements the base integration with the Slovak National Operator of Payments
(NOP, operated by KVERKOM) for instant bank-to-bank QR payments:

* ``nop.pokladnica`` — cash register configuration (mTLS cert, VATSK, POKLADNICA id,
  environment: integration vs production).
* ``nop.transaction`` — authoritative ledger of payment notifications received
  from the bank through NOP.
* ``NopClient`` service — mTLS-authenticated REST client wrapping
  ``generateNewTransactionId``, ``getAllTransactions`` and ``getTransactionHistory``.
* Data-integrity hash verification (SHA-256 of IBAN|AMOUNT|EUR|endToEndId).
* Rate-limited polling with a safety cron.

No POS dependency — POS/invoice integrations are provided by separate modules
that depend on this one.
    """,
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.0.1",
    "category": "Accounting/Payment",
    "depends": [
        "base",
        "base_iban",
        "account",
        "mail",
        "point_of_sale",
    ],
    "external_dependencies": {
        "python": ["requests", "cryptography"],
    },
    "data": [
        "security/ir.model.access.csv",
        "data/cron.xml",
        "report/non_confirmation_receipt.xml",
        "views/pos_config_views.xml",
        "views/nop_transaction_views.xml",
        "views/menus.xml",
    ],
    "installable": True,
    "application": False,
    "license": "AGPL-3",
}
