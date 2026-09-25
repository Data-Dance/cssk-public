# -*- coding: utf-8 -*-
{
    "name": "Czech EET 2.0 (Electronic Registration of Sales)",
    "summary": "Send registered-sale data messages to the Czech EET 2.0 system "
            "(data interface v4.1, SOAP + WS-Security).",
    "author": "Data Dance s.r.o.",
    "website": "https://eet.gov.cz",
    "category": "Accounting/Localizations",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        "base",
        "account",
    ],
    "external_dependencies": {
        "python": ["cryptography", "lxml", "requests"],
    },
    "data": [
        "security/eet2_security.xml",
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "views/eet2_certificate_views.xml",
        "views/eet2_transaction_views.xml",
        "views/account_journal_views.xml",
        "views/account_payment_views.xml",
        "views/res_config_settings_views.xml",
        "views/menus.xml",
    ],
    "installable": True,
    "application": True,
}
