{
    "name": "POS VRP2 Integration",
    "version": "18.0.4.6.0",
    "author": "Data Dance s.r.o.",
    "category": "Point of Sale",
    "summary": "Integrate Odoo POS with Slovak Virtual Cash Register (VRP 2)",
    "description": """
Integrates Odoo Point of Sale with the Slovak Financial Administration's
Virtual Cash Register 2 (Virtuálna registračná pokladnica 2).

Calls the VRP2 REST API at vcrp.financnasprava.sk to:
- Authenticate and manage sessions
- Synchronise products and categories
- Create fiscal receipts (pokladničné doklady)
- Handle deposits, withdrawals, invoice payments
- Manage closures and reports
    """,
    "license": "AGPL-3",
    "depends": [
        "point_of_sale",
        "l10n_sk_vrp2_base",
    ],
    "external_dependencies": {
        "python": ["requests"],
    },
    "data": [
        "views/res_config_settings_views.xml",
        "views/pos_config_views.xml",
        "views/pos_category_views.xml",
        "views/product_views.xml",
        "views/pos_order_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "pos_vrp2/static/src/js/vrp2_load_credentials.js",
            "pos_vrp2/static/src/xml/vrp2_load_credentials.xml",
        ],
    },
    "installable": True,
    "application": False,
}
