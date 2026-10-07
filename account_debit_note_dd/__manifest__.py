# Copyright 2022 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Account Debit Note DD",
    "summary": "Names Odoo's core debit note as the Czech vrubopis (opravný daňový doklad zvyšující "
        "základ) on screen and on the printed document — a UI and report layer that leaves "
        "posting unchanged.",
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
