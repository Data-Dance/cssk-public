# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Slovakia — additional-income tax and health calculation',
    'version': '19.0.1.0.2', 'license': 'AGPL-3', 'author': 'Data Dance s.r.o., votrelec',
    'category': 'Human Resources/Payroll', 'countries': ['sk'],
    'summary': 'Reviewed monthly additional-income tax and health calculation',
    'depends': ['l10n_sk_hr_payroll_income_allocation', 'l10n_sk_hr_payroll_oca'],
    'data': ['security/ir.model.access.csv', 'security/rules.xml', 'views/settlement.xml'],
    'installable': True,
}
