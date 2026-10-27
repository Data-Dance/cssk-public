# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestReverseChargeCategory(TransactionCase):
    """A domestic reverse-charge sale (§ 69 ods. 12) is 'AE', not exempt."""

    def setUp(self):
        super().setUp()
        if 'cssk_control_is_reverse_charge' not in self.env['account.tax']._fields:
            self.skipTest("needs l10n_cssk_kv_kh_base for the reverse-charge flag")
        sk = self.env.ref('base.sk')
        self.company = self.env['res.company'].create({
            'name': "SK RC Co", 'country_id': sk.id})
        self.seller = self.company.partner_id
        self.buyer = self.env['res.partner'].create({
            'name': "SK buyer", 'country_id': sk.id, 'is_company': True})

        group = self.env['account.tax.group'].create({
            'name': "VAT 0%", 'company_id': self.company.id, 'country_id': sk.id})

        def tax(name, **extra):
            return self.env['account.tax'].create({
                'name': name, 'amount': 0.0, 'amount_type': 'percent',
                'type_tax_use': 'sale', 'company_id': self.company.id,
                'country_id': sk.id, 'tax_group_id': group.id, **extra})

        self.rc = tax("0% RC", cssk_control_is_reverse_charge=True)
        self.exempt = tax("0% exempt")

    def test_reverse_charge_sale_is_ae_with_its_reason(self):
        common = self.env['account.edi.common']
        self.assertEqual(
            common._get_tax_category_code(self.buyer, self.seller, self.rc), 'AE')
        reason = common._get_tax_exemption_reason(self.buyer, self.seller, self.rc)
        self.assertEqual(reason['tax_exemption_reason_code'], 'VATEX-EU-AE')
        self.assertEqual(
            common._get_tax_category_code(self.buyer, self.seller, self.exempt), 'E')

    def test_a_category_set_on_the_tax_wins(self):
        self.rc.ubl_cii_tax_category_code = 'S'
        self.assertEqual(
            self.env['account.edi.common']._get_tax_category_code(
                self.buyer, self.seller, self.rc), 'S')
