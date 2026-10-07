from lxml import etree

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged
from odoo.tools import file_open

ISDOC_NS = "http://isdoc.cz/namespace/2013"

# A final invoice (DocumentType 1) settling one 21% taxed advance of 500 + VAT:
#   full line 1000 + 21% = 1210 ; advance already claimed 500 + 105 = 605 ; net payable 605.
DEPOSIT_INVOICE = f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="{ISDOC_NS}" version="6.0.2">
  <DocumentType>1</DocumentType>
  <ID>FV-DEP-1</ID>
  <UUID>11111111-1111-1111-1111-111111111111</UUID>
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
    <Item><Description>Zboží</Description></Item>
  </InvoiceLine></InvoiceLines>
  <TaxedDeposits><TaxedDeposit>
    <ID>ZAL-1</ID>
    <VariableSymbol>12345</VariableSymbol>
    <TaxableDepositAmount>500</TaxableDepositAmount>
    <TaxInclusiveDepositAmount>605</TaxInclusiveDepositAmount>
    <ClassifiedTaxCategory><Percent>21</Percent><VATCalculationMethod>0</VATCalculationMethod><VATApplicable>true</VATApplicable></ClassifiedTaxCategory>
  </TaxedDeposit></TaxedDeposits>
  <TaxTotal><TaxSubTotal>
    <TaxableAmount>1000</TaxableAmount><TaxAmount>210</TaxAmount><TaxInclusiveAmount>1210</TaxInclusiveAmount>
    <AlreadyClaimedTaxableAmount>500</AlreadyClaimedTaxableAmount><AlreadyClaimedTaxAmount>105</AlreadyClaimedTaxAmount><AlreadyClaimedTaxInclusiveAmount>605</AlreadyClaimedTaxInclusiveAmount>
    <DifferenceTaxableAmount>500</DifferenceTaxableAmount><DifferenceTaxAmount>105</DifferenceTaxAmount><DifferenceTaxInclusiveAmount>605</DifferenceTaxInclusiveAmount>
    <TaxCategory><Percent>21</Percent><VATApplicable>true</VATApplicable></TaxCategory>
  </TaxSubTotal><TaxAmount>210</TaxAmount></TaxTotal>
  <LegalMonetaryTotal>
    <TaxExclusiveAmount>1000</TaxExclusiveAmount><TaxInclusiveAmount>1210</TaxInclusiveAmount>
    <AlreadyClaimedTaxExclusiveAmount>500</AlreadyClaimedTaxExclusiveAmount><AlreadyClaimedTaxInclusiveAmount>605</AlreadyClaimedTaxInclusiveAmount>
    <DifferenceTaxExclusiveAmount>500</DifferenceTaxExclusiveAmount><DifferenceTaxInclusiveAmount>605</DifferenceTaxInclusiveAmount>
    <PaidDepositsAmount>605</PaidDepositsAmount><PayableAmount>605</PayableAmount>
  </LegalMonetaryTotal>
</Invoice>"""


@tagged('post_install', '-at_install')
class TestISDOCAdvance(AccountTestInvoicingCommon):

    @classmethod
    def _create_company(cls, **create_values):
        create_values.setdefault('currency_id', cls.env.ref('base.CZK').id)
        company = super()._create_company(**create_values)
        company.country_id = cls.env.ref('base.cz')
        company.tax_calculation_rounding_method = 'round_globally'  # Czech VAT is rounded globally
        return company

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data['company']
        cls.purchase_journal = cls.company_data['default_journal_purchase']
        cls.tax_sale_21 = cls.env['account.tax'].create({
            'name': "DPH 21%", 'amount': 21.0, 'amount_type': 'percent',
            'type_tax_use': 'sale', 'company_id': cls.company.id})
        cls.tax_purchase_21 = cls.env['account.tax'].create({
            'name': "DPH 21% (nákup)", 'amount': 21.0, 'amount_type': 'percent',
            'type_tax_use': 'purchase', 'company_id': cls.company.id})
        cls.cz_customer = cls.env['res.partner'].create({
            'name': "Odběratel", 'street': "Vedlejší 2", 'zip': "60200", 'city': "Brno",
            'vat': 'CZ25663585', 'company_registry': '25663585',
            'country_id': cls.env.ref('base.cz').id})
        cls.company.partner_id.write({
            'street': "Hlavní 1", 'zip': "11000", 'city': "Praha",
            'vat': 'CZ46342958', 'company_registry': '46342958'})
        with file_open('account_edi_isdoc/tests/schema/isdoc-invoice-6.0.2.xsd', 'rb') as f:
            cls.schema = etree.XMLSchema(etree.parse(f))

    def _find(self, root, path):
        return root.findtext('/'.join(f'{{{ISDOC_NS}}}{p}' for p in path.split('/')))

    # ----- Import: deducted advance becomes a negative line -----

    def test_import_taxed_deposit_nets_to_payable(self):
        invoice = self.env['account.move'].with_company(self.company).create({
            'move_type': 'in_invoice', 'journal_id': self.purchase_journal.id})
        self.env['account.edi.xml.isdoc'].with_company(self.company)._import_invoice_ubl_cii(
            invoice, {'xml_tree': etree.fromstring(DEPOSIT_INVOICE.encode()),
                      'attachment': self.env['ir.attachment']})
        lines = invoice.invoice_line_ids.filtered(lambda l: l.display_type == 'product')
        self.assertEqual(len(lines), 2)  # full line + advance deduction
        # full 1000 + 21% = 1210, less advance 500 + 105 = 605  ->  net 605
        self.assertAlmostEqual(invoice.amount_untaxed, 500.0, places=2)
        self.assertAlmostEqual(invoice.amount_total, 605.0, places=2)

    # ----- Export: advance deduction -> AlreadyClaimed + TaxedDeposits -----

    def test_export_advance_deduction(self):
        if 'is_downpayment' not in self.env['account.move.line']._fields:
            self.skipTest("`sale` not installed; down-payment lines unavailable")
        invoice = self.env['account.move'].with_company(self.company).create({
            'move_type': 'out_invoice', 'partner_id': self.cz_customer.id, 'invoice_date': '2024-07-10',
            'invoice_line_ids': [
                Command.create({'name': "Zboží", 'quantity': 1, 'price_unit': 1000.0,
                                'tax_ids': [Command.set(self.tax_sale_21.ids)]}),
                Command.create({'name': "Záloha", 'quantity': 1, 'price_unit': -500.0, 'is_downpayment': True,
                                'tax_ids': [Command.set(self.tax_sale_21.ids)]}),
            ]})
        invoice.action_post()
        self.assertEqual(invoice.amount_total, 605.0)  # net

        xml, errors = self.env['account.edi.xml.isdoc']._export_invoice(invoice)
        self.assertFalse(errors)
        root = etree.fromstring(xml)
        self.schema.assertValid(root)
        # Only the regular line is in InvoiceLines.
        self.assertEqual(len(root.findall(f'{{{ISDOC_NS}}}InvoiceLines/{{{ISDOC_NS}}}InvoiceLine')), 1)
        # The advance shows up as a TaxedDeposit and in the already-claimed totals.
        self.assertEqual(self._find(root, 'TaxedDeposits/TaxedDeposit/TaxableDepositAmount'), '500.00')
        self.assertEqual(self._find(root, 'LegalMonetaryTotal/AlreadyClaimedTaxExclusiveAmount'), '500.00')
        self.assertEqual(self._find(root, 'LegalMonetaryTotal/PayableAmount'), '605.00')
        self.assertEqual(self._find(root, 'TaxTotal/TaxSubTotal/DifferenceTaxInclusiveAmount'), '605.00')
