# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged


@tagged('post_install_l10n', 'post_install', '-at_install')
class TestWhitelistFromTemplate(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company_cz = self.env['res.company'].create({
            'name': 'CZ Co',
            'country_id': self.env.ref('base.cz').id,
        })
        self.employee_cz = self.env['hr.employee'].create({
            'name': 'CZ Employee',
            'company_id': self.company_cz.id,
        })

    def test_cz_contract_template_loading(self):
        Version = self.env['hr.version'].with_company(self.company_cz)

        template = Version.create({
            'name': 'CZ Template',
            'l10n_cz_tax_declaration': True,
            'l10n_cz_children_t1': 2,
            'l10n_cz_meal_allowance': 120.0,
        })

        contract = self.employee_cz.version_id

        self.assertFalse(contract.l10n_cz_tax_declaration)
        self.assertEqual(contract.l10n_cz_children_t1, 0)

        wizard = self.env['hr.version.wizard']\
            .with_company(self.company_cz)\
            .with_context(active_model='hr.employee', active_id=self.employee_cz.id)\
            .create({'contract_template_id': template.id})
        wizard.action_load_template()

        for field in Version._get_whitelist_fields_from_template():
            self.assertEqual(contract[field], template[field])

    def test_non_cz_company_does_not_whitelist(self):
        company_sk = self.env['res.company'].create({
            'name': 'SK Co',
            'country_id': self.env.ref('base.sk').id,
        })
        whitelist = self.env['hr.version'].with_company(
            company_sk)._get_whitelist_fields_from_template()
        self.assertFalse([f for f in whitelist if f.startswith('l10n_cz_')])
