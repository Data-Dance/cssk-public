{
    "name": "CZ/SK Supplier Reliability Check (guarantor liability)",
    "summary": "Before you pay a vendor, check the supplier's tax reliability "
               "and whether the bank account is the one registered with the "
               "tax authority — and snapshot the result onto the bill.",
    "description": """
CZ/SK Supplier Reliability Check
================================

Protects the *buyer* from liability for a supplier's unpaid VAT
(*ručenie za daň* §69 ods. 14 SK / *ručení* §109 CZ). On a vendor bill it checks:

1. **Tax reliability** of the supplier (the tax authority's rating).
2. Whether the **bank account** you are about to pay is one the supplier has
   **registered/published** with the tax authority.

The result is **snapshotted onto the bill** (status + the registered accounts +
a timestamp) as point-in-time proof, and a warning is posted to the chatter.
It **never blocks** the payment — paying an unregistered account or an
unreliable payer stays possible (you may instead remit the VAT directly to the
tax office under §69b / §109a), but you are warned and it is documented.

This is the **country-neutral base**: the actual register lookups live in the
country providers (``l10n_sk_payment_reliability`` etc.).
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.1.0",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["account", "l10n_cssk_core"],
    "data": [
        "data/ir_cron.xml",
        "views/res_config_settings_views.xml",
        "views/account_move_views.xml",
        "views/account_payment_views.xml",
        "views/res_partner_views.xml",
    ],
    "installable": True,
}
