# Copyright 2022 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "QR Code Frame Provider",
    "summary": "Shared QR-code frame parameters for the payment-QR providers (PAY by square, payme, "
        "QR Platba) that build on it.",
    "version": "19.0.1.1.0",
    "category": "Accounting/Payment",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "description": """
        This module provides QR Code frame generations parameters.
    """,
    "depends": ["account", "base"],
    "data": [
        "views/report_invoice.xml",
    ],
    "auto_install": False,
    "license": "AGPL-3",
}
