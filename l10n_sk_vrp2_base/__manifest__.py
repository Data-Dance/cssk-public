{
    "name": "Slovak VRP2 - Base / Connection",
    "version": "19.0.2.4.0",
    "author": "Data Dance s.r.o.",
    "category": "Accounting/Localizations",
    "summary": "Connection layer for the Slovak Virtual Cash Register (VRP 2)",
    "description": """
Base module for integrating Odoo with the Slovak Financial Administration's
Virtuálna registračná pokladnica 2 (VRP 2) REST API.

Provides the shared communication layer:
- ``vrp2.client`` API client with crpChecksum request signing
- VRP2 credentials, session and dashboard cache on the company
- VRP2 VAT-rate ↔ Odoo sales-tax mapping
- Login / Logout actions in the Accounting settings

Functional modules (invoice payments, POS receipts, ...) depend on this
module and reuse ``vrp2.client``.
    """,
    "license": "AGPL-3",
    "depends": [
        "account",
    ],
    "external_dependencies": {
        "python": ["requests"],
    },
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "application": False,
}
