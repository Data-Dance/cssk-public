{
    "name": "CZ/SK EC Sales List — VIES proof",
    "summary": "Validate EC sales list partners against VIES at export and "
               "snapshot the consultation number onto each line.",
    "description": """
Link module: EC Sales List × direct VIES
========================================

When both ``l10n_cssk_ec_summary_base`` and ``l10n_cssk_vies`` are installed,
this glue makes the EC sales list export do a **real VIES check** (not just a
format gate) for companies using direct EU VIES, and **snapshots** the official
consultation number, the check timestamp, and the validity onto each reported
line — so re-opening a filed statement shows exactly what was confirmed.

* A line whose VAT VIES reports as **invalid** is a hard block on export.
* A transient VIES outage does **not** block the statutory filing; it is logged
  in the statement chatter so the check can be repeated.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.0.4",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["l10n_cssk_ec_summary_base", "l10n_cssk_vies"],
    "data": [
        "views/cssk_ec_summary_statement_views.xml",
    ],
    "auto_install": True,
    "installable": True,
}
