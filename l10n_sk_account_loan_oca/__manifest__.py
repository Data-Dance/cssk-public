# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "SK Lízing — Community engine (OCA)",
    "summary": "Applies the Slovak leasing account defaults to the OCA "
               "account_loan / account_leasing engine.",
    "description": """
SK Lízing — Community engine (OCA)
==================================

Bridge between ``l10n_sk_account_loan_base`` (the Slovak account roles) and the
**Community** leasing engine, OCA ``account_loan`` + ``account_leasing``. A new
loan or leasing contract opens with the Slovak accounts already filled in:

* long-term liability → ``long_term_loan_account_id``      (474000)
* current portion     → ``short_term_loan_account_id``     (474100)
* interest expense    → ``interest_expenses_account_id``   (562000)
* leased asset        → ``leased_asset_account_id``        (022000, ``account_leasing``)

The Enterprise counterpart is ``l10n_sk_account_loan_ee``. Exactly one of the two
may be installed, because the underlying engines declare the same models — see
the base module's description and ``PORTED-OCA.md``.

Licensed **AGPL-3** because it depends on the AGPL OCA engine.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.1.2",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["l10n_sk_account_loan_base", "account_leasing"],
    # Belt and braces: `account_loan` already excludes `account_loans`, but state
    # it here too so the exclusivity is visible on the module a user installs.
    "excludes": ["account_loans"],
    "auto_install": True,
    "installable": True,
}
