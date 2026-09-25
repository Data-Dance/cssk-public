{
    "name": "Czech Republic Base Localization",
    "summary": "Czech IBAN <-> legacy account number conversion and variable/constant/specific symbols",
    "description": """
Czech Republic base localization
================================

Provides the Czech-specific building blocks shared by other modules
(e.g. ISDOC e-invoicing), kept lightweight (depends only on ``account``):

* res.partner.bank: bidirectional Czech IBAN <-> legacy "prefix-number/bankcode"
  conversion, with the legacy account number, account prefix and bank code
  computed from the IBAN (IBAN stays the primary storage format).
* account.move: Variable / Constant / Specific symbol fields (VS / KS / SS).
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "category": "Accounting/Localizations",
    "version": "19.0.2.0.2",
    "depends": ["account", "l10n_cssk_payment_symbols"],
    "data": [
        "views/res_partner_bank_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "license": "AGPL-3",
}
