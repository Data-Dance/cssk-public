# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "CZ/SK Wage Garnishment — Accounting",
    "version": "19.0.1.1.1",
    "category": "Human Resources/Payroll",
    "summary": "Turn each wage-garnishment deduction into a payable to the "
    "bailiff, stamped with the case number as variable symbol, ready for the "
    "payment order and the bank file.",
    "author": "Data Dance s.r.o.",
    "website": "https://github.com/Data-Dance/l10n_cssk",
    "license": "AGPL-3",
    "depends": [
        "account",
        "l10n_cssk_hr_payroll_garnishment_base",
        "l10n_cssk_payment_symbols",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_wage_garnishment_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "auto_install": True,
}
