# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "payme (Slovakia)",
    "summary": "Slovak payme payment QR code on invoices — a payme.sk link that opens the "
        "customer's banking app with IBAN, amount, currency and payment identification "
        "pre-filled.",
    "version": "19.0.1.2.0",
    "category": "Accounting/Payment",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "description": """
        This module adds Slovakia payme QR Code to reports.
    """,
    "depends": ["account", "base_iban", "account_qr_code_frame_provider"],
    "data": [],
    "auto_install": False,
    "license": "AGPL-3",
    "price": 50.00,
    "currency": "EUR",
}
