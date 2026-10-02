# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Payment Mode: Pay on Validation",
    "summary": "A payment mode can register the payment when the invoice is "
               "posted — cash and card sales paid on the spot.",
    "version": "19.0.1.0.0",
    "category": "Accounting/Payment",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "depends": ["account_payment_mode"],
    "data": ["views/account_payment_mode_views.xml"],
    "installable": True,
}
