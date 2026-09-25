# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Account Move Report Signed",
    "version": "19.0.1.0.0",
    "author": "Data Dance s.r.o.",
    "category": "Accounting/Accounting",
    "summary": "Renders negative (signed) values in Account Move note PDF reports",
    "description": "This is useful in CZ/SK context where credit notes need to be displayed with negative amounts",
    "data": [
        "views/report_invoice.xml",
    ],
    "depends": ["account"],
    "installable": True,
    "license": "AGPL-3",
    "price": 0,
    "currency": "EUR",
}
