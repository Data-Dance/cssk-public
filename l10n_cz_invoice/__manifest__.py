{
    "name": "CZ Invoice (statutory PDF)",
    "summary": "Czech invoice layout: customer DIČ, payment symbols and the "
               "mandatory statutory phrases (reverse charge §92a, exemptions "
               "§64/§66).",
    "description": """
CZ Invoice — statutory PDF
==========================

The Czech country layer that adds the statutory invoice content to Odoo's
invoice, on top of core + ``l10n_cz`` (which prints IČO / trade registry).

* Customer **DIČ** (from ``l10n_cssk_core``).
* **Payment symbols** — variabilní / konstantní / specifický symbol.
* **Statutory phrases** (auto-detected): domestic reverse charge (§92a),
  intra-Community supply (§64), export (§66); plus a free-text manual note.

The phrase auto-detection (zero-rate + partner country + the per-tax §92a flag)
is a best-effort heuristic — have an accountant confirm the mapping.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.0.2",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["l10n_cz", "l10n_cssk_core", "l10n_cssk_payment_symbols"],
    "data": [
        "views/account_views.xml",
        "report/report_invoice.xml",
    ],
    "installable": True,
}
