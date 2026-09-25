{
    "name": "CZ/SK EC Sales List — Shared Framework (Súhrnný výkaz / Souhrnné hlášení)",
    "version": "19.0.1.6.5",
    "summary": "Country-neutral framework for the Slovak Súhrnný výkaz and Czech "
               "Souhrnné hlášení (EC sales list): single-line aggregation per "
               "(country, VAT, transaction code), mandatory VIES preflight, and "
               "an XSD-validated XML export pipeline.",
    "description": """
CZ/SK EC Sales List — Shared Framework
======================================

The country-neutral engine behind the Slovak **Súhrnný výkaz** and Czech
**Souhrnné hlášení** (EC sales list / recapitulative statement). The two have
the **same row shape** — one aggregated line per (member-state, customer VAT,
transaction code) — so a single line model serves both; country modules ship
only the codes, XML template and schema.

Depends on **Odoo core only** (``account``, ``mail``, ``l10n_cssk_core``) — no
``account_reports`` — so it is Community/Enterprise- and 18.0/19.0-clean.

Provides:

* ``cssk.ec.summary.statement.version`` — versioned template + schema + types.
* ``cssk.ec.summary.statement`` (mail.thread; draft → preview → exported →
  submitted) with ``action_compute_lines`` and ``action_export_xml``.
* ``cssk.ec.summary.statement.line`` — the aggregated line.
* ``account.tax.cssk_ec_summary_code`` — marks intra-EU supply taxes and their
  transaction code.
* **Mandatory VIES preflight** before export (hard block — diverges from
  Consystech's soft warning, since a submitted EC list with an invalid VAT is
  penalised in both jurisdictions).
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
        "views/cssk_ec_summary_version_views.xml",
        "views/cssk_ec_summary_statement_views.xml",
        "views/cssk_ec_summary_menus.xml",
    ],
    "installable": True,
}
