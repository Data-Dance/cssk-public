# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Slovakia - Payroll with Accounting (OCA)",
    "summary": "Post Slovak payslips to the general ledger",
    "version": "19.0.1.0.1",
    "category": "Human Resources/Payroll",
    "author": "Data Dance s.r.o., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/payroll",
    "license": "AGPL-3",
    "countries": ["sk"],
    "depends": [
        "payroll_account",
        "l10n_sk",
        "l10n_sk_hr_payroll_oca",
    ],
    "data": [],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "auto_install": False,
}
