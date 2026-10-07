from lxml import etree

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged
from odoo.tools import file_open

ISDOC_NS = "http://isdoc.cz/namespace/2013"


@tagged('post_install', '-at_install')
class TestISDOCExport(AccountTestInvoicingCommon):

    @classmethod
    def _create_company(cls, **create_values):
        # EXTENDS 'account' — ISDOC is a Czech, CZK format.
        create_values.setdefault('currency_id', cls.env.ref('base.CZK').id)
        company = super()._create_company(**create_values)
        company.country_id = cls.env.ref('base.cz')
        company.tax_calculation_rounding_method = 'round_globally'  # Czech VAT is rounded globally
        return company

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_data['company'].partner_id.write({
            'street': "Příhon 943",
            'zip': "696 15",
            'city': "Čejkovice",
            'vat': 'CZ46342958',
            'company_registry': '46342958',
            'phone': '+420511447174',
            'email': 'fakturace@example.cz',
        })
        cls.cz_customer = cls.env['res.partner'].create({
            'name': "Odběratel s.r.o.",
            'street': "Diabasová 1141/11",
            'zip': "15500",
            'city': "Praha 13",
            'vat': 'CZ25663585',
            'company_registry': '25663585',
            'country_id': cls.env.ref('base.cz').id,
        })
        cls.company_data['company'].partner_id.bank_ids = [Command.create({
            'acc_number': '2631172369/0800',
            'allow_out_payment': True,  # mark trusted so out_invoice posting isn't blocked
        })]
        cls.tax_21 = cls.env['account.tax'].create({
            'name': "DPH 21%",
            'amount': 21.0,
            'amount_type': 'percent',
            'type_tax_use': 'sale',
            'company_id': cls.company_data['company'].id,
        })
        cls.tax_12 = cls.env['account.tax'].create({
            'name': "DPH 12%",
            'amount': 12.0,
            'amount_type': 'percent',
            'type_tax_use': 'sale',
            'company_id': cls.company_data['company'].id,
        })
        with file_open('account_edi_isdoc/tests/schema/isdoc-invoice-6.0.2.xsd', 'rb') as f:
            cls.schema = etree.XMLSchema(etree.parse(f))

    def _export(self, invoice):
        builder = self.env['account.edi.xml.isdoc']
        xml, errors = builder._export_invoice(invoice)
        self.assertFalse(errors, "ISDOC export reported constraints: %s" % errors)
        root = etree.fromstring(xml)
        self.schema.assertValid(root)  # raises etree.DocumentInvalid with details on failure
        return root

    def _find(self, root, path):
        return root.findtext('/'.join(f'{{{ISDOC_NS}}}{p}' for p in path.split('/')))

    def test_out_invoice_two_tax_rates(self):
        invoice = self.init_invoice(
            'out_invoice', partner=self.cz_customer, invoice_date='2024-07-10',
            amounts=[201.48, 300.00], taxes=self.tax_12, post=True,
        )
        root = self._export(invoice)
        self.assertEqual(root.get('version'), '6.0.2')
        self.assertEqual(self._find(root, 'DocumentType'), '1')
        self.assertEqual(self._find(root, 'ID'), invoice.name)
        self.assertTrue(invoice.isdoc_uuid)
        self.assertEqual(self._find(root, 'UUID'), invoice.isdoc_uuid)
        self.assertEqual(self._find(root, 'LegalMonetaryTotal/PayableAmount'),
                         f'{invoice.amount_total:.2f}')
        lines = root.findall(f'{{{ISDOC_NS}}}InvoiceLines/{{{ISDOC_NS}}}InvoiceLine')
        self.assertEqual(len(lines), 2)

    def test_tax_point_is_the_duzp_not_the_issue_date(self):
        invoice = self.init_invoice(
            'out_invoice', partner=self.cz_customer, invoice_date='2024-08-03',
            amounts=[100.0], taxes=self.tax_21)
        invoice.taxable_supply_date = '2024-07-31'
        invoice.action_post()
        root = self._export(invoice)
        self.assertEqual(self._find(root, 'IssueDate'), '2024-08-03')
        self.assertEqual(self._find(root, 'TaxPointDate'), '2024-07-31')

    def test_out_invoice_mixed_rates_and_bank(self):
        invoice = self.init_invoice(
            'out_invoice', partner=self.cz_customer, invoice_date='2024-07-10',
            amounts=[100.0, 200.0], taxes=self.tax_21, post=True,
        )
        # second line at the 12% rate -> two TaxSubTotal groups
        invoice.button_draft()
        invoice.invoice_line_ids[1].tax_ids = self.tax_12
        invoice.partner_bank_id = self.company_data['company'].partner_id.bank_ids[0]
        invoice.action_post()
        root = self._export(invoice)
        subtotals = root.findall(f'{{{ISDOC_NS}}}TaxTotal/{{{ISDOC_NS}}}TaxSubTotal')
        self.assertEqual(len(subtotals), 2)
        self.assertEqual(self._find(root, 'PaymentMeans/Payment/Details/BankCode'), '0800')
        self.assertEqual(self._find(root, 'PaymentMeans/Payment/Details/ID'), '2631172369')

    def test_out_refund(self):
        invoice = self.init_invoice(
            'out_refund', partner=self.cz_customer, invoice_date='2024-07-11',
            amounts=[1209.0], taxes=self.tax_21, post=True,
        )
        root = self._export(invoice)
        self.assertEqual(self._find(root, 'DocumentType'), '2')

    def test_cz_bank_account_conversion(self):
        # Conversion lives in l10n_cz_base (res.partner.bank._cz_account_parts).
        # Stored as a Czech IBAN -> derive legacy account number + bank code, incl. computed fields.
        bank_iban = self.env['res.partner.bank'].create({
            'acc_number': 'CZ43 0800 0000 0026 3117 2369',
            'partner_id': self.company_data['company'].partner_id.id,
        })
        self.assertEqual(
            bank_iban._cz_account_parts(),
            ('2631172369', '0800', 'CZ4308000000002631172369'),
        )
        self.assertEqual(bank_iban.bank_local_code, '0800')
        self.assertEqual(bank_iban.acc_legacy_number, '2631172369')
        # Stored in legacy form (incl. a prefix) -> compute a valid IBAN.
        bank_legacy = self.env['res.partner.bank'].create({
            'acc_number': '19-2000145399/0100',
            'partner_id': self.cz_customer.id,
        })
        self.assertEqual(
            bank_legacy._cz_account_parts(),
            ('19-2000145399', '0100', 'CZ0801000000192000145399'),
        )
        # Fio bank code 2010 — the case the [6:14] slice got wrong.
        bank_fio = self.env['res.partner.bank'].create({
            'acc_number': '2801589782/2010',
            'partner_id': self.cz_customer.id,
        })
        self.assertEqual(
            bank_fio._cz_account_parts(),
            ('2801589782', '2010', 'CZ8120100000002801589782'),
        )
        # legacy -> IBAN model helper (used on import to store IBAN as primary)
        self.assertEqual(
            self.env['res.partner.bank']._cz_legacy_to_iban('2631172369/0800'),
            'CZ4308000000002631172369',
        )

    def test_missing_customer_address_is_flagged(self):
        self.cz_customer.write({'street': False, 'city': False, 'zip': False})
        invoice = self.init_invoice(
            'out_invoice', partner=self.cz_customer, invoice_date='2024-07-10',
            amounts=[100.0], taxes=self.tax_21, post=True,
        )
        _xml, errors = self.env['account.edi.xml.isdoc']._export_invoice(invoice)
        self.assertTrue(errors)
