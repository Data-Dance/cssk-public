# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Slovakia - Payroll",
    "version": "19.0.1.18.3",
    "category": "Human Resources/Payroll",
    "summary": "Slovak payroll rules for the payroll engine",
    "countries": ["sk"],
    "author": "Data Dance s.r.o., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/payroll",
    "license": "AGPL-3",
    "depends": [
        "payroll",
        "l10n_sk_hr_payroll_base",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/hr_payroll_country_security.xml",
        "data/hr_salary_rule_category_data.xml",
        "data/hr_rule_parameter_data.xml",
        "data/hr_leave_type_data.xml",
        "data/hr_leave_accrual_plan_data.xml",
        "data/hr_leave_options_data.xml",
        "data/hr_salary_rule_data.xml",
        "data/hr_payroll_structure_data.xml",
        "views/hr_contract_views.xml",
        "views/l10n_sk_tax_reconciliation_views.xml",
    ],
    "demo": [
        "demo/hr_leave_type_demo.xml",
    ],
    "installable": True,
}
