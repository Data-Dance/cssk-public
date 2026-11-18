from psycopg2 import IntegrityError

from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestTaxDepreciationGroup(TransactionCase):

    @mute_logger('odoo.sql_db')
    def test_group_code_is_unique_across_countries(self):
        groups = self.env['account.asset.tax.class']
        values = {
            'name': 'Test depreciation group',
            'code': 'TEST-TAX-GROUP-CODE',
            'country_code': 'CZ',
            'group_number': 1,
            'useful_life_years': 3,
        }
        original = groups.create(values)
        groups.create(dict(values, code='TEST-OTHER-TAX-GROUP-CODE'))
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            groups.create(dict(values, country_code='SK'))
        self.assertEqual(groups.search_count([('code', '=', original.code)]), 1)
