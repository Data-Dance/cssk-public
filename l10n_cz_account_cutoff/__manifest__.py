{
    "name": "CZ Deferrals — default accounts (časové rozlišení)",
    "summary": "Pre-fills the OCA cut-off / deferral default accounts with the "
               "Czech 381/383/384/385 accounts so časové rozlišení works out of "
               "the box.",
    "description": """
CZ Deferrals — default accounts
===============================

Thin glue between the Czech chart (``l10n_cz``) and the OCA cut-off / deferral
engine (``account_cutoff_start_end_dates``). Maps the company's default cut-off
accounts to the Czech *časové rozlišení* accounts:

* prepaid expense  → **381** Náklady příštích období
* deferred revenue → **384** Výnosy příštích období
* accrued expense  → **383** Výdaje příštích období
* accrued revenue  → **385** Příjmy příštích období

Licensed **AGPL-3** because it depends on the AGPL OCA cut-off engine.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.0.1",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["l10n_cz", "account_cutoff_start_end_dates"],
    "post_init_hook": "post_init_hook",
    "auto_install": True,
    "installable": True,
}
