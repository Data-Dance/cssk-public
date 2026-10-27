# -*- coding: utf-8 -*-
import re
from datetime import date

from lxml import etree

from odoo import Command
from odoo.tests import tagged
from odoo.addons.l10n_account_edi_ubl_cii_tests.tests.common import TestUBLCommon

NS = {
    'cbc': "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    'cac': "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
}
PEPPOL_BILLING_CUSTOMIZATION_ID = (
    'urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0'
)


@tagged('post_install', '-at_install')
class TestUBLSlovakia(TestUBLCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sk_country = cls.env.ref('base.sk')
        cls.eur = cls.env['res.currency'].with_context(active_test=False).search(
            [('name', '=', 'EUR')], limit=1)
        cls.eur.active = True

        cls.seller = cls.env['res.partner'].create({
            'name': "SK Seller s.r.o.",
            'street': "Hlavna 1",
            'zip': "81101",
            'city': "Bratislava",
            'country_id': cls.sk_country.id,
            'vat': "SK2020000004",
            'company_registry': "12345679",
            'bank_ids': [Command.create({
                'acc_number': "SK3112000000198742637541",
                'allow_out_payment': True,  # trusted, so posting doesn't raise
            })],
        })
        cls.buyer = cls.env['res.partner'].create({
            'name': "SK Buyer a.s.",
            'street': "Vedlajsia 2",
            'zip': "04001",
            'city': "Kosice",
            'country_id': cls.sk_country.id,
            'vat': "SK2020000015",
        })

    # -------------------------------------------------------------------------
    # Format registration / auto-selection plumbing
    # -------------------------------------------------------------------------

    def test_format_is_registered_for_slovakia(self):
        info = self.env['res.partner']._get_ubl_cii_formats_info()
        self.assertIn('ubl_bis3_sk', info)
        self.assertEqual(info['ubl_bis3_sk']['countries'], ['SK'])
        self.assertTrue(info['ubl_bis3_sk']['on_peppol'])

    def test_builder_mapping(self):
        builder = self.buyer._get_edi_builder('ubl_bis3_sk')
        self.assertEqual(builder._name, 'account.edi.xml.ubl_sk')
        self.assertEqual(builder._description, "SK Peppol BIS Billing 3.0")

    def test_sk_partner_auto_suggests_sk_format(self):
        # Single format for SK -> it is the suggested one for Slovak partners.
        self.assertEqual(self.buyer._get_suggested_ubl_cii_edi_format(), 'ubl_bis3_sk')
        self.assertEqual(self.buyer._get_suggested_invoice_edi_format(), 'ubl_bis3_sk')

    # -------------------------------------------------------------------------
    # Export content
    # -------------------------------------------------------------------------

    def test_export_is_plain_peppol_bis3_with_sk_specifics(self):
        invoice = self._generate_move(
            self.seller, self.buyer, send=False,
            move_type='out_invoice',
            currency_id=self.eur.id,
            invoice_line_ids=[{
                'product_id': self.product_a.id,
                'quantity': 1,
                'price_unit': 100.0,
                'tax_ids': [Command.set(self.company_data['default_tax_sale'].ids)],
            }],
        )

        builder = self.env['account.edi.xml.ubl_sk']
        xml_bytes, _errors = builder._export_invoice(invoice)
        tree = etree.fromstring(xml_bytes)

        # 1. Plain Peppol BIS Billing 3.0 — no SK CIUS deviation.
        self.assertEqual(
            tree.findtext('cbc:CustomizationID', namespaces=NS),
            PEPPOL_BILLING_CUSTOMIZATION_ID,
        )

        # 2. Slovak IC DPH appears as SK########## in the supplier PartyTaxScheme
        #    (country-prefixed, no schemeID) — the EN16931 convention.
        supplier_vat = tree.findtext(
            'cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID',
            namespaces=NS,
        )
        self.assertEqual(supplier_vat, "SK2020000004")

        # 3. IBAN flows to the payee financial account.
        iban = tree.findtext(
            'cac:PaymentMeans/cac:PayeeFinancialAccount/cbc:ID', namespaces=NS)
        self.assertEqual((iban or '').replace(' ', ''), "SK3112000000198742637541")

        # 4. Variabilný symbol -> cbc:PaymentID (digits of the invoice number).
        expected_vs = re.sub(r'\D', '', invoice.name)[-10:]
        self.assertEqual(
            tree.findtext('cac:PaymentMeans/cbc:PaymentID', namespaces=NS),
            expected_vs,
        )

    def test_export_filename(self):
        invoice = self._generate_move(
            self.seller, self.buyer, send=False,
            move_type='out_invoice',
            currency_id=self.eur.id,
            invoice_line_ids=[{
                'product_id': self.product_a.id,
                'quantity': 1,
                'price_unit': 100.0,
                'tax_ids': [Command.set(self.company_data['default_tax_sale'].ids)],
            }],
        )
        filename = self.env['account.edi.xml.ubl_sk']._export_invoice_filename(invoice)
        self.assertTrue(filename.endswith('_ubl_bis3_sk.xml'))

    # -------------------------------------------------------------------------
    # Dátum dodania <-> cbc:TaxPointDate (BT-7)
    # -------------------------------------------------------------------------

    def _sk_move(self, **kwargs):
        return self._generate_move(
            self.seller, self.buyer, send=False,
            currency_id=self.eur.id,
            invoice_line_ids=[{
                'product_id': self.product_a.id,
                'quantity': 1,
                'price_unit': 100.0,
                'tax_ids': [Command.set(self.company_data['default_tax_sale'].ids)],
            }],
            **kwargs,
        )

    def test_export_tax_point_date_is_the_taxable_supply_date(self):
        invoice = self._sk_move(
            move_type='out_invoice',
            invoice_date='2026-01-20', date='2026-01-20',
            taxable_supply_date='2026-01-15',
        )
        xml_bytes, _errors = self.env['account.edi.xml.ubl_sk']._export_invoice(invoice)
        tree = etree.fromstring(xml_bytes)

        self.assertEqual(tree.findtext('cbc:IssueDate', namespaces=NS), '2026-01-20')
        self.assertEqual(tree.findtext('cbc:TaxPointDate', namespaces=NS), '2026-01-15')
        # BR-CO-3: BT-7 and BT-8 are mutually exclusive.
        self.assertIsNone(tree.find('cac:InvoicePeriod/cbc:DescriptionCode', namespaces=NS))
        # UBL 2.1 element order: after InvoiceTypeCode, before DocumentCurrencyCode.
        order = [etree.QName(child).localname for child in tree]
        self.assertLess(order.index('InvoiceTypeCode'), order.index('TaxPointDate'))
        self.assertLess(order.index('TaxPointDate'), order.index('DocumentCurrencyCode'))

    def test_export_tax_point_date_on_credit_note(self):
        refund = self._sk_move(
            move_type='out_refund',
            invoice_date='2026-01-20', date='2026-01-20',
            taxable_supply_date='2026-01-15',
        )
        xml_bytes, _errors = self.env['account.edi.xml.ubl_sk']._export_invoice(refund)
        tree = etree.fromstring(xml_bytes)
        self.assertEqual(etree.QName(tree).localname, 'CreditNote')
        self.assertEqual(tree.findtext('cbc:TaxPointDate', namespaces=NS), '2026-01-15')

    def test_import_tax_point_date_fills_taxable_supply_date(self):
        invoice = self._sk_move(
            move_type='out_invoice',
            invoice_date='2026-01-20', date='2026-01-20',
            taxable_supply_date='2026-01-15',
        )
        xml_bytes, _errors = self.env['account.edi.xml.ubl_sk']._export_invoice(invoice)
        self.assertIn(b'<cbc:TaxPointDate>2026-01-15</cbc:TaxPointDate>', xml_bytes)

        attachment = self.env['ir.attachment'].create({
            'name': 'inbound_sk_invoice.xml',
            'raw': xml_bytes,
            'mimetype': 'application/xml',
        })
        journal = self.company_data['default_journal_purchase']
        journal.create_document_from_attachment(attachment.ids)
        bill = self.env['account.move'].search([('journal_id', '=', journal.id)], order='id desc', limit=1)

        self.assertEqual(bill.move_type, 'in_invoice')
        self.assertEqual(bill.invoice_date, date(2026, 1, 20))
        # Inbound documents resolve to the generic BIS 3 builder by their
        # CustomizationID and take account.edi.ubl's import pipeline, so this
        # exercises that hook, not the Slovak builder.
        self.assertEqual(bill.taxable_supply_date, date(2026, 1, 15))

    def test_import_without_tax_point_date_keeps_the_default(self):
        invoice = self._sk_move(move_type='out_invoice', invoice_date='2026-01-20', date='2026-01-20')
        xml_bytes, _errors = self.env['account.edi.xml.ubl_sk']._export_invoice(invoice)
        # Strip the element to simulate a sender that does not fill BT-7.
        xml_bytes = re.sub(rb'<cbc:TaxPointDate>[^<]*</cbc:TaxPointDate>', b'', xml_bytes)
        self.assertNotIn(b'TaxPointDate', xml_bytes)

        attachment = self.env['ir.attachment'].create({
            'name': 'inbound_no_bt7.xml',
            'raw': xml_bytes,
            'mimetype': 'application/xml',
        })
        journal = self.company_data['default_journal_purchase']
        journal.create_document_from_attachment(attachment.ids)
        bill = self.env['account.move'].search([('journal_id', '=', journal.id)], order='id desc', limit=1)
        # The hook must not invent a date. (l10n_sk's own default — the invoice
        # date — keys on the company's FISCAL country, which the generic test
        # chart leaves outside Slovakia, so it does not apply here.)
        self.assertFalse(bill.taxable_supply_date)
