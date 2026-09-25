# Copyright 2022 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Account Debit Note DD",
    "category": "Tools",
    "license": "AGPL-3",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.0.0",
    "depends": ["account_debit_note"],
    "data": [
        "report/report_invoice.xml",
        "views/account_move_views.xml",
    ],
    "installable": True,
}
