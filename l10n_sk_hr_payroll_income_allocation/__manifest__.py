# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Slovakia - Historical social assessment and premiums',
    'version': '19.0.1.2.0', 'license': 'AGPL-3', 'author': 'Data Dance s.r.o., votrelec',
    'category': 'Human Resources/Payroll', 'countries': ['sk'],
    'summary': 'Reviewed historical social bases and dated premiums for additional income',
    'website': 'https://github.com/Data-Dance/l10n_cssk',
    'depends': ['l10n_sk_hr_payroll_oca', 'l10n_cssk_payroll_declaration_base'],
    'data': ['security/ir.model.access.csv', 'security/rules.xml', 'views/allocation.xml'],
    'installable': True,
}
