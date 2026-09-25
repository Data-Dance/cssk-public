# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Czech Republic - Payroll with Accounting",
    "version": "19.0.1.0.1",
    "category": "Human Resources/Payroll",
    "summary": "Post Czech payslips to the general ledger",
    "countries": ["cz"],
    "author": "Data Dance s.r.o., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/payroll",
    "license": "AGPL-3",
    "depends": [
        "payroll_account",
        "l10n_cz",
        "l10n_cz_hr_payroll_oca",
    ],
    "data": [],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
