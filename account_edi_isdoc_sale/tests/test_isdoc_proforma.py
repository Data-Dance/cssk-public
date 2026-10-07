from lxml import etree

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged
from odoo.tools import file_open

ISDOC_NS = "http://isdoc.cz/namespace/2013"

# A minimal incoming proforma (DocumentType 4): one 1000 + 21% line, payable 1210.
PROFORMA = f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="{ISDOC_NS}" version="6.0.2">
  <DocumentType>4</DocumentType>
  <ID>ZAL-2024-001</ID>
  <UUID>22222222-2222-2222-2222-222222222222</UUID>
  <IssueDate>2024-07-10</IssueDate>
  <VATApplicable>true</VATApplicable>
  <ElectronicPossibilityAgreementReference languageID="cs">http://</ElectronicPossibilityAgreementReference>
  <LocalCurrencyCode>CZK</LocalCurrencyCode>
  <CurrRate>1</CurrRate>
  <RefCurrRate>1</RefCurrRate>
  <AccountingSupplierParty><Party>
    <PartyIdentification><ID>29261783</ID></PartyIdentification>
    <PartyName><Name>Dodavatel s.r.o.</Name></PartyName>
    <PostalAddress><StreetName>Hlavní</StreetName><BuildingNumber>1</BuildingNumber>
      <CityName>Praha</CityName><PostalZone>11000</PostalZone>
      <Country><IdentificationCode>CZ</IdentificationCode><Name>Česká republika</Name></Country></PostalAddress>
    <PartyTaxScheme><CompanyID>CZ29261783</CompanyID><TaxScheme>VAT</TaxScheme></PartyTaxScheme>
  </Party></AccountingSupplierParty>
  <AccountingCustomerParty><Party>
    <PartyIdentification><ID>25663585</ID></PartyIdentification>
    <PartyName><Name>Odberatel s.r.o.</Name></PartyName>
    <PostalAddress><StreetName>Vedlejší</StreetName><BuildingNumber>2</BuildingNumber>
      <CityName>Brno</CityName><PostalZone>60200</PostalZone>
      <Country><IdentificationCode>CZ</IdentificationCode><Name>Česká republika</Name></Country></PostalAddress>
    <PartyTaxScheme><CompanyID>CZ25663585</CompanyID><TaxScheme>VAT</TaxScheme></PartyTaxScheme>
  </Party></AccountingCustomerParty>
  <InvoiceLines><InvoiceLine>
    <ID>1</ID>
    <InvoicedQuantity unitCode="ks">1</InvoicedQuantity>
    <LineExtensionAmount>1000</LineExtensionAmount>
    <LineExtensionAmountTaxInclusive>1210</LineExtensionAmountTaxInclusive>
    <LineExtensionTaxAmount>210</LineExtensionTaxAmount>
    <UnitPrice>1000</UnitPrice>
    <UnitPriceTaxInclusive>1210</UnitPriceTaxInclusive>
    <ClassifiedTaxCategory><Percent>21</Percent><VATCalculationMethod>0</VATCalculationMethod><VATApplicable>true</VATApplicable></ClassifiedTaxCategory>
    <Item><Description>Záloha na dodávku</Description></Item>
  </InvoiceLine></InvoiceLines>
  <TaxTotal><TaxSubTotal>
    <TaxableAmount>1000</TaxableAmount><TaxAmount>210</TaxAmount><TaxInclusiveAmount>1210</TaxInclusiveAmount>
    <AlreadyClaimedTaxableAmount>0</AlreadyClaimedTaxableAmount><AlreadyClaimedTaxAmount>0</AlreadyClaimedTaxAmount><AlreadyClaimedTaxInclusiveAmount>0</AlreadyClaimedTaxInclusiveAmount>
    <DifferenceTaxableAmount>1000</DifferenceTaxableAmount><DifferenceTaxAmount>210</DifferenceTaxAmount><DifferenceTaxInclusiveAmount>1210</DifferenceTaxInclusiveAmount>
    <TaxCategory><Percent>21</Percent><VATApplicable>true</VATApplicable></TaxCategory>
  </TaxSubTotal><TaxAmount>210</TaxAmount></TaxTotal>
  <LegalMonetaryTotal>
    <TaxExclusiveAmount>1000</TaxExclusiveAmount><TaxInclusiveAmount>1210</TaxInclusiveAmount>
    <AlreadyClaimedTaxExclusiveAmount>0</AlreadyClaimedTaxExclusiveAmount><AlreadyClaimedTaxInclusiveAmount>0</AlreadyClaimedTaxInclusiveAmount>
    <DifferenceTaxExclusiveAmount>1000</DifferenceTaxExclusiveAmount><DifferenceTaxInclusiveAmount>1210</DifferenceTaxInclusiveAmount>
    <PaidDepositsAmount>0</PaidDepositsAmount><PayableAmount>1210</PayableAmount>
  </LegalMonetaryTotal>
</Invoice>"""


@tagged('post_install', '-at_install')
class TestISDOCProforma(AccountTestInvoicingCommon):

    @classmethod
    def _create_company(cls, **create_values):
        create_values.setdefault('currency_id', cls.env.ref('base.CZK').id)
        company = super()._create_company(**create_values)
        company.country_id = cls.env.ref('base.cz')
        company.tax_calculation_rounding_method = 'round_globally'
        return company

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data['company']
        cls.purchase_journal = cls.company_data['default_journal_purchase']
        cls.company.partner_id.write({
            'street': "Příhon 943", 'zip': "696 15", 'city': "Čejkovice",
            'vat': 'CZ46342958', 'company_registry': '46342958'})
        cls.company.partner_id.bank_ids = [Command.create({'acc_number': '2631172369/0800'})]
        cls.cz_customer = cls.env['res.partner'].create({
            'name': "Odběratel s.r.o.", 'street': "Vedlejší 2", 'zip': "60200", 'city': "Brno",
            'vat': 'CZ25663585', 'company_registry': '25663585', 'country_id': cls.env.ref('base.cz').id})
        cls.tax_sale_21 = cls.env['account.tax'].create({
            'name': "DPH 21%", 'amount': 21.0, 'amount_type': 'percent',
            'type_tax_use': 'sale', 'company_id': cls.company.id})
        cls.tax_purchase_21 = cls.env['account.tax'].create({
            'name': "DPH 21% (nákup)", 'amount': 21.0, 'amount_type': 'percent',
            'type_tax_use': 'purchase', 'company_id': cls.company.id})
        with file_open('account_edi_isdoc/tests/schema/isdoc-invoice-6.0.2.xsd', 'rb') as f:
            cls.schema = etree.XMLSchema(etree.parse(f))

    def _find(self, root, path):
        return root.findtext('/'.join(f'{{{ISDOC_NS}}}{p}' for p in path.split('/')))

    def test_export_proforma_from_sale_order(self):
        order = self.env['sale.order'].with_company(self.company).sudo().create({
            'partner_id': self.cz_customer.id,
            'order_line': [Command.create({
                'product_id': self.product_a.id, 'product_uom_qty': 2, 'price_unit': 500.0,
                'tax_ids': [Command.set(self.tax_sale_21.ids)],
            })],
        })
        xml, errors = order._export_isdoc_proforma()
        self.assertFalse(errors)
        root = etree.fromstring(xml)
        self.schema.assertValid(root)
        self.assertEqual(self._find(root, 'DocumentType'), '4')  # proforma
        self.assertEqual(self._find(root, 'ID'), order.name)
        self.assertTrue(order.isdoc_uuid)
        self.assertEqual(self._find(root, 'LegalMonetaryTotal/PayableAmount'),
                         f'{order.amount_total:.2f}')
        self.assertEqual(len(root.findall(f'{{{ISDOC_NS}}}InvoiceLines/{{{ISDOC_NS}}}InvoiceLine')), 1)
        # Bank account on the proforma (the company's, where the advance is paid).
        self.assertEqual(self._find(root, 'PaymentMeans/Payment/Details/BankCode'), '0800')

    def test_import_proforma_as_draft_bill(self):
        invoice = self.env['account.move'].with_company(self.company).create({
            'move_type': 'in_invoice', 'journal_id': self.purchase_journal.id})
        self.env['account.edi.xml.isdoc'].with_company(self.company)._import_invoice_ubl_cii(
            invoice, {'xml_tree': etree.fromstring(PROFORMA.encode()),
                      'attachment': self.env['ir.attachment']})
        # A proforma is not a tax document -> it lands as a DRAFT vendor bill.
        self.assertEqual(invoice.state, 'draft')
        self.assertEqual(invoice.move_type, 'in_invoice')
        self.assertEqual(invoice.ref, 'ZAL-2024-001')
        self.assertAlmostEqual(invoice.amount_total, 1210.0, places=2)
