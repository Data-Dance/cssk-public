{
    "name": "SK Deferrals — default accounts (časové rozlíšenie)",
    "summary": "Pre-fills the OCA cut-off / deferral default accounts with the "
               "Slovak 381/383/384/385 accounts so časové rozlíšenie works out "
               "of the box.",
    "description": """
SK Deferrals — default accounts
===============================

Thin glue between the Slovak chart (``l10n_sk``) and the OCA cut-off /
deferral engine (``account_cutoff_start_end_dates``). It maps the company's
default cut-off accounts to the Slovak *časové rozlíšenie* accounts so the
deferral feature is turnkey:

* prepaid expense  → **381** Náklady budúcich období
* deferred revenue → **384** Výnosy budúcich období
* accrued expense  → **383** Výdaje budúcich období
* accrued revenue  → **385** Príjmy budúcich období

New companies get the mapping when the SK chart loads (via the chart template);
existing SK companies get it on install (post-init hook). The cut-off journal is
set to a general journal if one exists.

Licensed **AGPL-3** because it depends on the AGPL OCA cut-off engine.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.0.2",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["l10n_sk", "account_cutoff_start_end_dates"],
    "post_init_hook": "post_init_hook",
    "auto_install": True,
    "installable": True,
}
