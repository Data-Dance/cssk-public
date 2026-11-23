# -*- coding: utf-8 -*-
import re
from datetime import date
from unittest.mock import patch

from lxml import etree

from odoo import Command
from odoo.tools.misc import file_path
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
        # account_payment_order, when installed alongside, takes bank-account
        # rights away from the partner managers and gives them to its own
        # Accounting / Payments group; the core helper writes bank accounts.
        payments = cls.env.ref(
            'account_payment_order.group_account_payment', raise_if_not_found=False)
        if payments:
            cls.env.user.group_ids |= payments
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

    def test_export_no_tax_point_date_when_it_is_the_issue_date(self):
        """Transposition v1.13, BT-7: only when BT-7 differs from BT-2."""
        invoice = self._sk_move(
            move_type='out_invoice',
            invoice_date='2026-01-20', date='2026-01-20',
            taxable_supply_date='2026-01-20',
        )
        xml_bytes, _errors = self.env['account.edi.xml.ubl_sk']._export_invoice(invoice)
        tree = etree.fromstring(xml_bytes)
        self.assertEqual(tree.findtext('cbc:IssueDate', namespaces=NS), '2026-01-20')
        self.assertIsNone(tree.find('cbc:TaxPointDate', namespaces=NS))

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

    # -------------------------------------------------------------------------
    # IČO -> PartyLegalEntity/CompanyID (BT-30 / BT-47), scheme 0158
    # -------------------------------------------------------------------------

    def _export_tree(self, move):
        # The fixtures carry no DIČ, so the export reports that; the document
        # is built all the same, as in the tests above.
        xml_bytes, _errors = self.env['account.edi.xml.ubl_sk']._export_invoice(move)
        return etree.fromstring(xml_bytes)

    def test_export_legal_entity_id_is_the_ico(self):
        self.buyer.company_registry = "36 421 928"
        tree = self._export_tree(self._sk_move(move_type='out_invoice'))

        for role, ico, vat in (
            ('Supplier', "12345679", "SK2020000004"),
            ('Customer', "36421928", "SK2020000015"),
        ):
            party = f'cac:Accounting{role}Party/cac:Party'
            company_id = tree.find(f'{party}/cac:PartyLegalEntity/cbc:CompanyID', namespaces=NS)
            self.assertEqual(company_id.text, ico, role)
            self.assertEqual(company_id.get('schemeID'), '0158', role)
            # The IČ DPH stays where it belongs, and only there.
            self.assertEqual(
                tree.findtext(f'{party}/cac:PartyTaxScheme/cbc:CompanyID', namespaces=NS),
                vat, role)

    def test_export_seller_legal_form_and_register_entry(self):
        """BT-33: the seller's legal form and register entry, seller only."""
        text = ("Spoločnosť s ručením obmedzeným, zapísaná v Obchodnom registri "
                "Mestského súdu Bratislava III, oddiel Sro, vložka č. 1234/B")
        builder = type(self.env['account.edi.xml.ubl_sk'])
        with patch.object(builder, '_l10n_sk_legal_form_text',
                          lambda self, partner: text):
            tree = self._export_tree(self._sk_move(move_type='out_invoice'))
        supplier = tree.find(
            'cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity', namespaces=NS)
        self.assertEqual(
            [etree.QName(child).localname for child in supplier],
            ['RegistrationName', 'CompanyID', 'CompanyLegalForm'])
        self.assertEqual(supplier.findtext('cbc:CompanyLegalForm', namespaces=NS), text)
        self.assertIsNone(tree.find(
            'cac:AccountingCustomerParty/cac:Party/cac:PartyLegalEntity/'
            'cbc:CompanyLegalForm', namespaces=NS))

    def test_export_no_legal_form_without_register_data(self):
        self.assertFalse(self.env['account.edi.xml.ubl_sk']._l10n_sk_legal_form_text(
            self.env['res.partner'].new({'name': "Bez údajov"})))
        tree = self._export_tree(self._sk_move(move_type='out_invoice'))
        if 'l10n_sk_trade_registry_statement' not in self.seller._fields:
            self.assertIsNone(tree.find(
                'cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/'
                'cbc:CompanyLegalForm', namespaces=NS))

    def test_legal_form_text_from_the_trade_registry(self):
        if 'l10n_sk_trade_registry_statement' not in self.seller._fields:
            self.skipTest("l10n_sk_trade_registry is not installed")
        self.seller.write({
            'l10n_sk_legal_form': "Spoločnosť s ručením obmedzeným",
            'l10n_sk_trade_registry_statement': "Zapísaná v Obchodnom registri, vložka č. 1/B",
        })
        self.assertEqual(
            self.env['account.edi.xml.ubl_sk']._l10n_sk_legal_form_text(self.seller),
            "Spoločnosť s ručením obmedzeným, zapísaná v Obchodnom registri, vložka č. 1/B")
        tree = self._export_tree(self._sk_move(move_type='out_invoice'))
        self.assertEqual(tree.findtext(
            'cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/'
            'cbc:CompanyLegalForm', namespaces=NS),
            "Spoločnosť s ručením obmedzeným, zapísaná v Obchodnom registri, vložka č. 1/B")

    def test_transposition_pin_matches_the_guide(self):
        """The version of Finančná správa's transposition the module was read
        against is pinned in data/TRANSPOSITION_VERSION and named in the
        guide; the two must not drift apart."""
        pin = {}
        with open(file_path('l10n_sk_ubl_bis3/data/TRANSPOSITION_VERSION'), encoding='utf-8') as handle:
            for line in handle:
                if line.strip() and not line.startswith('#'):
                    key, _sep, value = line.partition(':')
                    pin[key.strip()] = value.strip()
        self.assertTrue(re.fullmatch(r'\d+\.\d+', pin['version']), pin)
        self.assertTrue(re.fullmatch(r'[0-9a-f]{32}', pin['md5']), pin)
        self.assertIn('v%s' % pin['version'].replace('.', '_'), pin['file'])
        for lang in ('en', 'sk'):
            with open(file_path('l10n_sk_ubl_bis3/doc/%s.md' % lang), encoding='utf-8') as handle:
                self.assertIn('%s (' % pin['version'], handle.read(), lang)

    def test_export_legal_entity_without_ico_carries_no_vat_number(self):
        # The buyer has no IČO: no CompanyID, rather than its IČ DPH under a
        # legal-registration label (which is what core writes).
        self.assertFalse(self.buyer.company_registry)
        tree = self._export_tree(self._sk_move(move_type='out_invoice'))
        legal = tree.find(
            'cac:AccountingCustomerParty/cac:Party/cac:PartyLegalEntity', namespaces=NS)
        self.assertEqual(legal.findtext('cbc:RegistrationName', namespaces=NS), "SK Buyer a.s.")
        self.assertIsNone(legal.find('cbc:CompanyID', namespaces=NS))

    def test_export_legal_entity_of_a_foreign_party_is_left_to_core(self):
        self.buyer.write({
            'country_id': self.env.ref('base.cz').id,
            'vat': "CZ12345679",
            'company_registry': "12345679",
        })
        tree = self._export_tree(self._sk_move(move_type='out_invoice'))
        company_id = tree.find(
            'cac:AccountingCustomerParty/cac:Party/cac:PartyLegalEntity/cbc:CompanyID',
            namespaces=NS)
        self.assertNotEqual(company_id.get('schemeID'), '0158')

    def test_ico_normalisation(self):
        builder = self.env['account.edi.xml.ubl_sk']
        partner = self.buyer
        for stored, expected in (
            ("36421928", "36421928"),
            (" 36 421 928 ", "36421928"),
            ("123456", "00123456"),        # pre-1996 six-digit IČO
            ("HRB 12345", ""),             # a foreign register number is not an IČO
            ("123456789", ""),
            (False, ""),
        ):
            partner.company_registry = stored
            self.assertEqual(builder._l10n_sk_ico(partner), expected, stored)

    # -------------------------------------------------------------------------
    # Opravná faktúra: BillingReference (BT-25 / BT-26), OrderReference, 383
    # -------------------------------------------------------------------------

    def _billing_references(self, tree):
        return [
            (ref.findtext('cbc:ID', namespaces=NS), ref.findtext('cbc:IssueDate', namespaces=NS))
            for ref in tree.findall(
                'cac:BillingReference/cac:InvoiceDocumentReference', namespaces=NS)
        ]

    def test_export_credit_note_names_the_original_invoice(self):
        invoice = self._sk_move(
            move_type='out_invoice', invoice_date='2026-01-20', date='2026-01-20', ref=False)
        refund = self._sk_move(
            move_type='out_refund', invoice_date='2026-02-03', date='2026-02-03',
            reversed_entry_id=invoice.id,
            ref=f"Storno: {invoice.name}, vrátenie tovaru",
        )
        tree = self._export_tree(refund)

        self.assertEqual(etree.QName(tree).localname, 'CreditNote')
        self.assertEqual(self._billing_references(tree), [(invoice.name, '2026-01-20')])
        # The wizard's text is not an order number; the original had none, so
        # the document number stands in, as core does for an empty ref.
        self.assertEqual(
            tree.findtext('cac:OrderReference/cbc:ID', namespaces=NS), refund.name)

    def test_export_credit_note_inherits_the_original_order_reference(self):
        invoice = self._sk_move(move_type='out_invoice', ref="PO-77")
        refund = self._sk_move(
            move_type='out_refund', reversed_entry_id=invoice.id,
            ref=f"Storno: {invoice.name}",
        )
        tree = self._export_tree(refund)
        self.assertEqual(tree.findtext('cac:OrderReference/cbc:ID', namespaces=NS), "PO-77")

    def test_export_credit_note_keeps_a_typed_order_reference(self):
        invoice = self._sk_move(move_type='out_invoice', ref="PO-77")
        refund = self._sk_move(
            move_type='out_refund', reversed_entry_id=invoice.id, ref="PO-78")
        tree = self._export_tree(refund)
        self.assertEqual(tree.findtext('cac:OrderReference/cbc:ID', namespaces=NS), "PO-78")
        self.assertEqual(len(self._billing_references(tree)), 1)

    def test_export_reconciled_credit_note_references_the_original_once(self):
        invoice = self._sk_move(
            move_type='out_invoice', invoice_date='2026-01-20', date='2026-01-20')
        refund = self._sk_move(
            move_type='out_refund', invoice_date='2026-02-03', date='2026-02-03',
            reversed_entry_id=invoice.id,
        )
        receivable = (invoice + refund).line_ids.filtered(
            lambda l: l.account_id.account_type == 'asset_receivable')
        if not all(receivable.mapped('reconciled')):
            receivable.filtered(lambda l: not l.reconciled).reconcile()
        self.assertTrue(all(receivable.mapped('reconciled')))
        # Whether or not core finds the invoice through the reconciliation,
        # it is referenced exactly once, with its date.
        tree = self._export_tree(refund)
        self.assertEqual(self._billing_references(tree), [(invoice.name, '2026-01-20')])

    def test_export_plain_invoice_has_no_billing_reference_and_is_380(self):
        tree = self._export_tree(self._sk_move(move_type='out_invoice'))
        self.assertEqual(tree.findtext('cbc:InvoiceTypeCode', namespaces=NS), '380')
        self.assertEqual(self._billing_references(tree), [])
        self.assertEqual(tree.findtext('cac:OrderReference/cbc:ID', namespaces=NS), 'ref_move')

    def test_export_debit_note_is_383_and_names_the_original_invoice(self):
        if 'debit_origin_id' not in self.env['account.move']._fields:
            self.skipTest("account_debit_note is not installed")
        invoice = self._sk_move(
            move_type='out_invoice', invoice_date='2026-01-20', date='2026-01-20', ref=False)
        debit_note = self._sk_move(
            move_type='out_invoice', invoice_date='2026-02-03', date='2026-02-03',
            debit_origin_id=invoice.id,
            ref=f"{invoice.name}, oprava ceny",
        )
        tree = self._export_tree(debit_note)

        # BIS Billing 3.0 has no DebitNote document: an Invoice, typed 383.
        self.assertEqual(etree.QName(tree).localname, 'Invoice')
        self.assertEqual(tree.findtext('cbc:InvoiceTypeCode', namespaces=NS), '383')
        self.assertEqual(self._billing_references(tree), [(invoice.name, '2026-01-20')])
        self.assertEqual(
            tree.findtext('cac:OrderReference/cbc:ID', namespaces=NS), debit_note.name)
        # UBL 2.1 element order: BillingReference after OrderReference.
        order = [etree.QName(child).localname for child in tree]
        self.assertLess(order.index('OrderReference'), order.index('BillingReference'))

    def test_order_reference_is_kept_when_it_only_resembles_the_original_number(self):
        invoice = self._sk_move(move_type='out_invoice', ref=False)
        refund = self._sk_move(
            move_type='out_refund', reversed_entry_id=invoice.id,
            ref=f"{invoice.name}0",   # a longer number that merely starts the same
        )
        tree = self._export_tree(refund)
        self.assertEqual(
            tree.findtext('cac:OrderReference/cbc:ID', namespaces=NS), f"{invoice.name}0")

    # -------------------------------------------------------------------------
    # The correction reason in the note (BT-22)
    # -------------------------------------------------------------------------

    def test_export_credit_note_carries_the_reason_in_the_note(self):
        invoice = self._sk_move(move_type='out_invoice', ref=False)
        refund = self._sk_move(
            move_type='out_refund', reversed_entry_id=invoice.id,
            ref=f"Storno: {invoice.name}, vrátenie tovaru",
            narration="Ďakujeme.",
        )
        tree = self._export_tree(refund)
        notes = tree.findall('cbc:Note', namespaces=NS)
        self.assertEqual(len(notes), 1)   # ibr-sr-51: at most one
        self.assertTrue(notes[0].text.endswith("vrátenie tovaru Ďakujeme."), notes[0].text)
        self.assertNotEqual(notes[0].text, "vrátenie tovaru Ďakujeme.")   # labelled

    def test_export_credit_note_without_a_reason_leaves_the_note_alone(self):
        invoice = self._sk_move(move_type='out_invoice', ref=False)
        for ref in (f"Storno: {invoice.name}", "PO-78, urgent", f"{invoice.name}0, x"):
            refund = self._sk_move(
                move_type='out_refund', reversed_entry_id=invoice.id, ref=ref,
                narration="Ďakujeme.")
            tree = self._export_tree(refund)
            self.assertEqual(tree.findtext('cbc:Note', namespaces=NS), "Ďakujeme.", ref)

    def test_export_debit_note_carries_the_reason_in_the_note(self):
        if 'debit_origin_id' not in self.env['account.move']._fields:
            self.skipTest("account_debit_note is not installed")
        invoice = self._sk_move(move_type='out_invoice', ref=False)
        debit_note = self._sk_move(
            move_type='out_invoice', debit_origin_id=invoice.id,
            ref=f"{invoice.name}, doúčtovanie dopravy", narration=False,
        )
        tree = self._export_tree(debit_note)
        self.assertTrue(
            tree.findtext('cbc:Note', namespaces=NS).endswith("doúčtovanie dopravy"))

    # -------------------------------------------------------------------------
    # A credit note typed by hand: the original numbers the user gives
    # -------------------------------------------------------------------------

    def test_export_credit_note_typed_by_hand_names_the_given_invoices(self):
        invoice = self._sk_move(
            move_type='out_invoice', invoice_date='2026-01-20', date='2026-01-20')
        refund = self._sk_move(
            move_type='out_refund',
            l10n_sk_original_invoice_ref=f"{invoice.name}; OLD/2025/0042, {invoice.name}",
        )
        tree = self._export_tree(refund)
        # Our own invoice gets its date; a number we do not know goes as typed.
        self.assertEqual(
            self._billing_references(tree),
            [(invoice.name, '2026-01-20'), ("OLD/2025/0042", None)])

    def test_export_typed_number_does_not_repeat_the_linked_original(self):
        invoice = self._sk_move(
            move_type='out_invoice', invoice_date='2026-01-20', date='2026-01-20')
        refund = self._sk_move(
            move_type='out_refund', reversed_entry_id=invoice.id,
            l10n_sk_original_invoice_ref=invoice.name,
        )
        self.assertEqual(
            self._billing_references(self._export_tree(refund)),
            [(invoice.name, '2026-01-20')])

    # -------------------------------------------------------------------------
    # Warnings on the invoice form (never a refusal)
    # -------------------------------------------------------------------------

    def _sk_alerts(self, move):
        move.invalidate_recordset(['alerts'])
        return {key for key in (move.alerts or {}) if key.startswith('l10n_sk_ubl_bis3_')}

    def test_alert_invoice_without_a_bank_account(self):
        invoice = self._sk_move(move_type='out_invoice')
        self.assertTrue(invoice.partner_bank_id)
        self.assertFalse(self._sk_alerts(invoice))

        invoice.partner_bank_id = False
        self.assertEqual(self._sk_alerts(invoice), {'l10n_sk_ubl_bis3_no_bank_account'})
        # A warning only: the export has nothing to say about it.
        _xml, errors = self.env['account.edi.xml.ubl_sk']._export_invoice(invoice)
        self.assertFalse([e for e in errors if 'bank' in e.lower()])

        # A customer on another format is none of this module's business.
        self.buyer.invoice_edi_format = False
        self.assertFalse(self._sk_alerts(invoice))

    def test_alert_credit_note_without_an_original(self):
        invoice = self._sk_move(move_type='out_invoice')
        linked = self._sk_move(move_type='out_refund', reversed_entry_id=invoice.id)
        self.assertFalse(self._sk_alerts(linked))

        typed = self._sk_move(move_type='out_refund')
        self.assertEqual(self._sk_alerts(typed), {'l10n_sk_ubl_bis3_no_original_invoice'})
        typed.l10n_sk_original_invoice_ref = "OLD/2025/0042"
        self.assertFalse(self._sk_alerts(typed))

    # -------------------------------------------------------------------------
    # The contacts whose e-invoice would be refused
    # -------------------------------------------------------------------------

    def test_filter_contacts_whose_einvoice_would_be_refused(self):
        Partner = self.env['res.partner']
        values = {
            'is_company': True, 'country_id': self.sk_country.id,
            'street': "Hlavna 1", 'zip': "81101", 'city': "Bratislava",
            'l10n_sk_dic': "2020317068", 'company_registry': "31333532",
        }
        complete = Partner.create({**values, 'name': "Complete s.r.o."})
        no_dic = Partner.create({**values, 'name': "No DIC s.r.o.", 'l10n_sk_dic': False})
        no_street = Partner.create({**values, 'name': "No street s.r.o.", 'street': False})
        bad_ico = Partner.create({**values, 'name': "Bad ICO s.r.o.", 'company_registry': "HRB 1234"})
        person = Partner.create({**values, 'name': "Ján Novák", 'is_company': False, 'street': False})
        czech = Partner.create({
            **values, 'name': "Czech s.r.o.", 'country_id': self.env.ref('base.cz').id,
            'street': False, 'l10n_sk_dic': False,
        })
        everyone = complete + no_dic + no_street + bad_ico + person + czech

        found = Partner.search([
            ('l10n_sk_einvoice_incomplete', '=', True), ('id', 'in', everyone.ids)])
        self.assertEqual(found, no_dic + no_street + bad_ico)
        self.assertEqual(
            everyone.filtered('l10n_sk_einvoice_incomplete'), no_dic + no_street + bad_ico)
        not_found = Partner.search([
            ('l10n_sk_einvoice_incomplete', '=', False), ('id', 'in', everyone.ids)])
        self.assertEqual(not_found, complete + person + czech)
        self.assertEqual(
            Partner.search([
                ('l10n_sk_einvoice_incomplete', 'in', [False]), ('id', 'in', everyone.ids)]),
            complete + person + czech)
