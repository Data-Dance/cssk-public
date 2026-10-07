# Copyright 2022 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "QR Platba (Czech Republic)",
    "summary": "Czech QR Platba payment QR code on invoices — the Czech Banking Association short "
        "payment descriptor (SPD) every Czech banking app reads, pre-filling IBAN, amount, "
        "currency, message and the variable symbol.",
    "version": "19.0.1.1.1",
    "category": "Accounting/Payment",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "description": """
         This module adds Czech Republic Credit Transfer QR-code to reports.
    """,
    "depends": ["account", "base_iban", "account_qr_code_frame_provider"],
    "data": [],
    "auto_install": False,
    "license": "AGPL-3",
    "price": 50.00,
    "currency": "EUR",
}
