from lxml import etree

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged
from odoo.tools import file_open

ISDOC_NS = "http://isdoc.cz/namespace/2013"


@tagged('post_install', '-at_install')
class TestISDOCAdvanceCZ(AccountTestInvoicingCommon):

    @classmethod
    def _create_company(cls, **create_values):
        create_values.setdefault('currency_id', cls.env.ref('base.CZK').id)
        # sale_order_advance_invoice defaults this required field to the main company's
        # journal, which breaks the fresh test company (cross-company). Skip the default,
        # then assign a journal that belongs to the new company.
        create_values['advance_invoice_journal_id'] = False
        company = super()._create_company(**create_values)
        company.country_id = cls.env.ref('base.cz')
        company.tax_calculation_rounding_method = 'round_globally'
        company.advance_invoice_journal_id = cls.env['account.journal'].create({
            'name': "Tax Documents for Advance Invoices", 'code': 'TDADV',
            'type': 'sale', 'company_id': company.id})
        return company

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data['company']
        cls.builder = cls.env['account.edi.xml.isdoc']
        cls.company.partner_id.write({
            'street': "Příhon 943", 'zip': "696 15", 'city': "Čejkovice",
            'vat': 'CZ46342958', 'company_registry': '46342958'})
        cls.cz_customer = cls.env['res.partner'].create({
            'name': "Odběratel s.r.o.", 'street': "Vedlejší 2", 'zip': "60200", 'city': "Brno",
            'vat': 'CZ25663585', 'company_registry': '25663585', 'country_id': cls.env.ref('base.cz').id})
        cls.tax_sale_21 = cls.env['account.tax'].create({
            'name': "DPH 21%", 'amount': 21.0, 'amount_type': 'percent',
            'type_tax_use': 'sale', 'company_id': cls.company.id})
        with file_open('account_edi_isdoc/tests/schema/isdoc-invoice-6.0.2.xsd', 'rb') as f:
            cls.schema = etree.XMLSchema(etree.parse(f))

    def _find(self, root, path):
        return root.findtext('/'.join(f'{{{ISDOC_NS}}}{p}' for p in path.split('/')))

    def _advance_order(self):
        return self.env['sale.order'].with_company(self.company).sudo().create({
            'partner_id': self.cz_customer.id,
            'is_advance_invoice': True,
            'order_line': [Command.create({
                'product_id': self.product_a.id, 'product_uom_qty': 1, 'price_unit': 1000.0,
                'is_downpayment': True, 'tax_ids': [Command.set(self.tax_sale_21.ids)],
            })],
        })

    def test_advance_order_exports_as_proforma_type_4(self):
        # The zálohová faktura (an is_advance_invoice sale order) -> DocumentType 4.
        order = self._advance_order()
        xml, errors = order._export_isdoc_proforma()
        self.assertFalse(errors)
        root = etree.fromstring(xml)
        self.schema.assertValid(root)
        self.assertEqual(self._find(root, 'DocumentType'), '4')

    def test_tax_document_exports_as_type_5(self):
        # A move linked to an advance order's line is the daňový doklad k přijaté platbě -> 5.
        advance = self._advance_order()
        move = self.env['account.move'].with_company(self.company).sudo().create({
            'move_type': 'out_invoice', 'partner_id': self.cz_customer.id, 'invoice_date': '2024-07-10',
            'invoice_line_ids': [Command.create({
                'product_id': self.product_a.id, 'quantity': 1, 'price_unit': 1000.0,
                'tax_ids': [Command.set(self.tax_sale_21.ids)],
                'sale_line_ids': [Command.set(advance.order_line.ids)],
            })],
        })
        self.assertTrue(move.is_advance_invoice_tax_document)
        self.assertEqual(self.builder._get_document_type_code(move), '5')

        move.action_post()  # gives the move a name so <ID> is populated
        xml, errors = self.builder._export_invoice(move)
        self.assertFalse(errors)
        root = etree.fromstring(xml)
        self.schema.assertValid(root)
        self.assertEqual(self._find(root, 'DocumentType'), '5')

    def test_settlement_deduction_routed_to_deposit(self):
        # On a final invoice, an is_advance_tracking deduction line -> TaxedDeposit, not a line.
        advance = self._advance_order()
        parent = self.env['sale.order'].with_company(self.company).sudo().create({
            'partner_id': self.cz_customer.id})
        tracking = self.env['sale.order.line'].sudo().create({
            'order_id': parent.id, 'product_id': self.product_a.id, 'product_uom_qty': 0.0,
            'price_unit': 500.0, 'name': "Advance deduction",
            'is_advance_tracking': True, 'advance_source_order_id': advance.id})

        move = self.env['account.move'].with_company(self.company).sudo().create({
            'move_type': 'out_invoice', 'partner_id': self.cz_customer.id, 'invoice_date': '2024-07-10',
            'invoice_line_ids': [
                Command.create({'product_id': self.product_a.id, 'quantity': 1, 'price_unit': 1000.0,
                                'tax_ids': [Command.set(self.tax_sale_21.ids)]}),
                Command.create({'product_id': self.product_a.id, 'quantity': 1, 'price_unit': -500.0,
                                'tax_ids': [Command.set(self.tax_sale_21.ids)],
                                'sale_line_ids': [Command.set(tracking.ids)]}),
            ],
        })
        regular_lines, deposit_lines = self.builder._isdoc_split_lines(move)
        self.assertEqual(len(regular_lines), 1)
        self.assertEqual(len(deposit_lines), 1)
        # Deposit identity falls back to the advance order (no posted tax document yet).
        doc_id, _vs = self.builder._isdoc_deposit_source(deposit_lines)
        self.assertEqual(doc_id, advance.name)
