{
    "name": "SLOVAK FX Revaluation — default accounts (Community)",
    "summary": "Pre-fills the OCA multicurrency-revaluation accounts with the "
               "Slovak 563/663 (kurzové rozdiely) accounts.",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.0.1",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["l10n_sk", "account_multicurrency_revaluation"],
    "post_init_hook": "post_init_hook",
    "auto_install": True,
    "installable": True,
}
