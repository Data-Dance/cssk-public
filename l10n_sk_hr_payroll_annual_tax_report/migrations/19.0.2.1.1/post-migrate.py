from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    old = env.ref('l10n_sk_hr_payroll_annual_tax_report.hlasenie_version_2023', raise_if_not_found=False)
    if old:
        old.write({'valid_to': '2025-12-31'})
