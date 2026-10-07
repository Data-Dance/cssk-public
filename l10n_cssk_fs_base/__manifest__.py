{
    "name": "CZ/SK Financial Statements — Shared Framework (Súvaha / VZS / Rozvaha / VZZ)",
    "version": "19.0.1.9.0",
    "summary": "Country-neutral framework for the Slovak and Czech financial "
               "statements (balance sheet + P&L): line trees computed from "
               "account-code balances + aggregates, with a comparison period, "
               "manual overrides and XSD-validated XML export. CE-clean.",
    "description": """
CZ/SK Financial Statements — Shared Framework
=============================================

The country-neutral engine behind the Slovak **Súvaha** (balance sheet) /
**Výkaz ziskov a strát** (P&L) and Czech **Rozvaha** / **VZZ**. A hierarchical
line tree where leaf lines are computed from **account-code balances** and
parent lines aggregate.

**CE-clean:** the evaluator reads ``account.move.line`` balances directly (by
``account.account.code``), so it does **not** depend on the EE
``account_reports`` engine. Works on Community and Enterprise, 18.0 and 19.0.

Provides:

* ``cssk.fs.statement.version`` — line definitions + statement kind
  (balance_sheet / profit_loss) + template + schema.
* ``cssk.fs.statement.line.def`` — ``accounts`` (account-code formula, balance-
  sheet = as-of / P&L = period), ``aggregate`` (formula over line codes), or
  ``manual``.
* ``cssk.fs.statement`` (mail.thread) — computes the **current and a comparison
  (prior) period**, supports per-line manual overrides preserved across
  recompute, and XSD-validated XML export.

Country modules ship the line definitions (the account mapping), the XML
template and the schema.

Scope note: this core computes a single (net) value per line. The SK Súvaha's
3-column **Brutto / Korekcia / Netto** split and Poznámky / mikro variants are
extensions on top.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["account", "mail", "l10n_cssk_core",
        "l10n_cssk_submission_base"],
    "data": [
        "security/ir.model.access.csv",
        "security/record_rules.xml",
        "views/cssk_fs_version_views.xml",
        "views/cssk_fs_statement_views.xml",
        "views/cssk_fs_menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "l10n_cssk_fs_base/static/src/fs_tree_field/fs_tree_field.js",
            "l10n_cssk_fs_base/static/src/fs_tree_field/fs_tree_field.xml",
            "l10n_cssk_fs_base/static/src/fs_tree_field/fs_tree_field.scss",
        ],
    },
    "installable": True,
}
