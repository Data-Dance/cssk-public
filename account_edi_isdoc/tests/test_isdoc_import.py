from lxml import etree

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged
from odoo.tools import file_open

NS = "http://isdoc.cz/namespace/2013"


def _party(role_name, vat):
    return f"""<Party>
    <PartyIdentification><ID>{vat[2:]}</ID></PartyIdentification>
    <PartyName><Name>{role_name}</Name></PartyName>
    <PostalAddress><StreetName>Hlavní</StreetName><BuildingNumber>1</BuildingNumber>
      <CityName>Praha</CityName><PostalZone>11000</PostalZone>
      <Country><IdentificationCode>CZ</IdentificationCode><Name>Česká republika</Name></Country></PostalAddress>
    <PartyTaxScheme><CompanyID>{vat}</CompanyID><TaxScheme>VAT</TaxScheme></PartyTaxScheme>
  </Party>"""


# A plain invoice: two 12% lines -> untaxed 500, tax 60, total 560.
INVOICE = f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="{NS}" version="6.0.2">
  <DocumentType>1</DocumentType><ID>FA-2024-001</ID>
  <UUID>AAAA1111-1111-1111-1111-111111111111</UUID>
  <IssueDate>2024-07-10</IssueDate><VATApplicable>true</VATApplicable>
  <ElectronicPossibilityAgreementReference languageID="cs">http://</ElectronicPossibilityAgreementReference>
  <LocalCurrencyCode>CZK</LocalCurrencyCode><CurrRate>1</CurrRate><RefCurrRate>1</RefCurrRate>
  <AccountingSupplierParty>{_party("Dodavatel s.r.o.", "CZ12345679")}</AccountingSupplierParty>
  <AccountingCustomerParty>{_party("Odběratel s.r.o.", "CZ25663585")}</AccountingCustomerParty>
  <InvoiceLines>
    <InvoiceLine><ID>1</ID><InvoicedQuantity unitCode="ks">2</InvoicedQuantity>
      <LineExtensionAmount>200</LineExtensionAmount><LineExtensionAmountTaxInclusive>224</LineExtensionAmountTaxInclusive>
      <LineExtensionTaxAmount>24</LineExtensionTaxAmount><UnitPrice>100</UnitPrice><UnitPriceTaxInclusive>112</UnitPriceTaxInclusive>
      <ClassifiedTaxCategory><Percent>12</Percent><VATCalculationMethod>0</VATCalculationMethod><VATApplicable>true</VATApplicable></ClassifiedTaxCategory>
      <Item><Description>Zboží A</Description></Item></InvoiceLine>
    <InvoiceLine><ID>2</ID><InvoicedQuantity unitCode="ks">1</InvoicedQuantity>
      <LineExtensionAmount>300</LineExtensionAmount><LineExtensionAmountTaxInclusive>336</LineExtensionAmountTaxInclusive>
      <LineExtensionTaxAmount>36</LineExtensionTaxAmount><UnitPrice>300</UnitPrice><UnitPriceTaxInclusive>336</UnitPriceTaxInclusive>
      <ClassifiedTaxCategory><Percent>12</Percent><VATCalculationMethod>0</VATCalculationMethod><VATApplicable>true</VATApplicable></ClassifiedTaxCategory>
      <Item><Description>Zboží B</Description></Item></InvoiceLine>
  </InvoiceLines>
  <TaxTotal><TaxSubTotal>
    <TaxableAmount>500</TaxableAmount><TaxAmount>60</TaxAmount><TaxInclusiveAmount>560</TaxInclusiveAmount>
    <AlreadyClaimedTaxableAmount>0</AlreadyClaimedTaxableAmount><AlreadyClaimedTaxAmount>0</AlreadyClaimedTaxAmount><AlreadyClaimedTaxInclusiveAmount>0</AlreadyClaimedTaxInclusiveAmount>
    <DifferenceTaxableAmount>500</DifferenceTaxableAmount><DifferenceTaxAmount>60</DifferenceTaxAmount><DifferenceTaxInclusiveAmount>560</DifferenceTaxInclusiveAmount>
    <TaxCategory><Percent>12</Percent><VATApplicable>true</VATApplicable></TaxCategory>
  </TaxSubTotal><TaxAmount>60</TaxAmount></TaxTotal>
  <LegalMonetaryTotal>
    <TaxExclusiveAmount>500</TaxExclusiveAmount><TaxInclusiveAmount>560</TaxInclusiveAmount>
    <AlreadyClaimedTaxExclusiveAmount>0</AlreadyClaimedTaxExclusiveAmount><AlreadyClaimedTaxInclusiveAmount>0</AlreadyClaimedTaxInclusiveAmount>
    <DifferenceTaxExclusiveAmount>500</DifferenceTaxExclusiveAmount><DifferenceTaxInclusiveAmount>560</DifferenceTaxInclusiveAmount>
    <PaidDepositsAmount>0</PaidDepositsAmount><PayableAmount>560</PayableAmount>
  </LegalMonetaryTotal>
</Invoice>"""

# A credit note (DocumentType 2) with a legacy bank account and a variable symbol.
CREDIT_NOTE = f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="{NS}" version="6.0.2">
  <DocumentType>2</DocumentType><ID>OD-2024-007</ID>
  <UUID>BBBB2222-2222-2222-2222-222222222222</UUID>
  <IssueDate>2024-07-11</IssueDate><VATApplicable>true</VATApplicable>
  <ElectronicPossibilityAgreementReference languageID="cs">http://</ElectronicPossibilityAgreementReference>
  <LocalCurrencyCode>CZK</LocalCurrencyCode><CurrRate>1</CurrRate><RefCurrRate>1</RefCurrRate>
  <AccountingSupplierParty>{_party("Dodavatel Plus s.r.o.", "CZ29261783")}</AccountingSupplierParty>
  <AccountingCustomerParty>{_party("Odběratel s.r.o.", "CZ25663585")}</AccountingCustomerParty>
  <InvoiceLines><InvoiceLine><ID>1</ID><InvoicedQuantity unitCode="ks">1</InvoicedQuantity>
    <LineExtensionAmount>1000</LineExtensionAmount><LineExtensionAmountTaxInclusive>1210</LineExtensionAmountTaxInclusive>
    <LineExtensionTaxAmount>210</LineExtensionTaxAmount><UnitPrice>1000</UnitPrice><UnitPriceTaxInclusive>1210</UnitPriceTaxInclusive>
    <ClassifiedTaxCategory><Percent>21</Percent><VATCalculationMethod>0</VATCalculationMethod><VATApplicable>true</VATApplicable></ClassifiedTaxCategory>
    <Item><Description>Vrácené zboží</Description></Item></InvoiceLine></InvoiceLines>
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
  <PaymentMeans><Payment><PaidAmount>-1210</PaidAmount><PaymentMeansCode>42</PaymentMeansCode>
    <Details><PaymentDueDate>2024-07-25</PaymentDueDate>
      <ID>2631172369</ID><BankCode>0800</BankCode><Name>Česká spořitelna</Name><IBAN></IBAN><BIC></BIC>
      <VariableSymbol>20240007</VariableSymbol></Details></Payment></PaymentMeans>
</Invoice>"""


@tagged('post_install', '-at_install')
class TestISDOCImport(AccountTestInvoicingCommon):

    @classmethod
    def _create_company(cls, **create_values):
        create_values.setdefault('currency_id', cls.env.ref('base.CZK').id)
        company = super()._create_company(**create_values)
        company.country_id = cls.env.ref('base.cz')
        company.tax_calculation_rounding_method = 'round_globally'  # Czech VAT is rounded globally
        return company

    @classmethod
    def get_default_groups(cls):
        # account_payment_order (OCA) moves the bank-account access rule to
        # its own group; without it these setups cannot create bank accounts.
        return super().get_default_groups() | (
            cls.env.ref("account_payment_order.group_account_payment", False)
            or cls.env["res.groups"]
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data['company']
        cls.purchase_journal = cls.company_data['default_journal_purchase']
        cls.taxes = {}
        for rate in (5.0, 9.0, 12.0, 19.0, 21.0):
            cls.taxes[rate] = cls.env['account.tax'].create({
                'name': f"DPH {rate:.0f}% (nákup)", 'amount': rate, 'amount_type': 'percent',
                'type_tax_use': 'purchase', 'company_id': cls.company.id})

    def _import(self, source):
        tree = source if isinstance(source, etree._Element) else etree.fromstring(source)
        invoice = self.env['account.move'].with_company(self.company).create({
            'move_type': 'in_invoice', 'journal_id': self.purchase_journal.id})
        self.env['account.edi.xml.isdoc'].with_company(self.company)._import_invoice_ubl_cii(
            invoice, {'xml_tree': tree, 'attachment': self.env['ir.attachment']})
        return invoice

    def _import_file(self, filename):
        with file_open(f'account_edi_isdoc/tests/test_files/import/{filename}', 'rb') as f:
            return self._import(etree.fromstring(f.read()))

    def test_import_invoice(self):
        invoice = self._import(INVOICE.encode())
        self.assertEqual(invoice.move_type, 'in_invoice')
        self.assertEqual(invoice.ref, 'FA-2024-001')
        self.assertTrue(invoice.isdoc_uuid)
        self.assertEqual(invoice.currency_id, self.env.ref('base.CZK'))
        self.assertEqual(invoice.partner_id.name, "Dodavatel s.r.o.")
        product_lines = invoice.invoice_line_ids.filtered(lambda l: l.display_type == 'product')
        self.assertEqual(len(product_lines), 2)
        self.assertTrue(all(l.tax_ids == self.taxes[12.0] for l in product_lines))
        self.assertAlmostEqual(invoice.amount_untaxed, 500.0, places=2)
        self.assertAlmostEqual(invoice.amount_tax, 60.0, places=2)
        self.assertAlmostEqual(invoice.amount_total, 560.0, places=2)

    def test_import_reads_the_duzp(self):
        """An ordinary vendor bill takes its DUZP from TaxPointDate; only the
        advance tax document used to."""
        xml = INVOICE.replace(
            '<IssueDate>2024-07-10</IssueDate>',
            '<IssueDate>2024-07-10</IssueDate><TaxPointDate>2024-06-28</TaxPointDate>')
        self.assertIn('TaxPointDate', xml)
        invoice = self._import(xml.encode())
        self.assertEqual(str(invoice.invoice_date), '2024-07-10')
        self.assertEqual(str(invoice.taxable_supply_date), '2024-06-28')
        if 'cssk_vat_deduction_date' in invoice._fields:
            # The deduction period is ours to set, not the supplier's.
            self.assertFalse(invoice.cssk_vat_deduction_date)

    def test_import_credit_note_with_legacy_bank(self):
        invoice = self._import(CREDIT_NOTE.encode())
        self.assertEqual(invoice.move_type, 'in_refund')
        self.assertEqual(invoice.ref, 'OD-2024-007')
        self.assertEqual(invoice.partner_id.name, "Dodavatel Plus s.r.o.")
        self.assertEqual(invoice.payment_reference, '20240007')  # VariableSymbol
        # Legacy <ID>/<BankCode> normalised to IBAN (via l10n_cz_base), legacy parts computed.
        self.assertTrue(invoice.partner_bank_id)
        self.assertEqual(invoice.partner_bank_id.sanitized_acc_number, 'CZ4308000000002631172369')
        self.assertEqual(invoice.partner_bank_id.bank_local_code, '0800')
        self.assertAlmostEqual(invoice.amount_total, 1210.0, places=2)

    def test_import_real_isdoc_5_1_document(self):
        # The official ABRA demo is ISDOC 5.1 (namespace .../invoice) — the importer is
        # version-agnostic, so it must still decode it (a settlement invoice with deposits).
        invoice = self._import_file('doklad.isdoc')
        self.assertEqual(invoice.move_type, 'in_invoice')
        self.assertEqual(invoice.ref, 'FV-111999/2008')
        self.assertEqual(invoice.partner_id.name, "ABRA Software a.s.")
        self.assertTrue(invoice.isdoc_uuid)
        # 3 product lines + advance deductions (TaxedDeposits/NonTaxedDeposits) + rounding line.
        product_lines = invoice.invoice_line_ids.filtered(lambda l: l.display_type == 'product')
        self.assertGreater(len(product_lines), 3)

    # ----- Vendor by IČO -----

    def test_import_finds_the_vendor_by_ico(self):
        """The supplier is known under another name and without a DIČ: only the
        IČO identifies it. Core's search would have created a second partner."""
        known = self.env['res.partner'].create({
            'name': "Dodavatel (smluvní název)", 'company_registry': '12345679',
            'is_company': True})
        invoice = self._import(INVOICE.encode())
        self.assertEqual(invoice.partner_id, known)

    def test_import_finds_a_non_payer_by_ico(self):
        """A non-payer of VAT has no DIČ; the IČO is all there is."""
        known = self.env['res.partner'].create({
            'name': "Neplátce", 'company_registry': '12345679', 'is_company': True})
        xml = INVOICE.replace(
            '<PartyTaxScheme><CompanyID>CZ12345679</CompanyID><TaxScheme>VAT</TaxScheme></PartyTaxScheme>', '', 1)
        self.assertNotIn('CZ12345679', xml)
        invoice = self._import(xml.encode())
        self.assertEqual(invoice.partner_id, known)

    def test_an_ico_contradicted_by_the_dic_is_not_trusted(self):
        """Same IČO, different DIČ: the IČO match is dropped, not forced."""
        other = self.env['res.partner'].create({
            'name': "Někdo jiný", 'company_registry': '12345679', 'vat': 'CZ29261783',
            'is_company': True})
        invoice = self._import(INVOICE.encode())
        self.assertNotEqual(invoice.partner_id, other)
        self.assertEqual(invoice.partner_id.name, "Dodavatel s.r.o.")

    def test_a_vendor_created_by_the_import_keeps_its_ico(self):
        invoice = self._import(INVOICE.encode())
        self.assertEqual(invoice.partner_id.company_registry, '12345679')

    # ----- Local reverse charge (§ 92a) -----

    def _reverse_charge_invoice(self):
        """The first line in the local reverse-charge regime: 200 at 21 %, no VAT
        charged (construction work, code 4); the second an ordinary 12 % line."""
        xml = INVOICE.replace(
            '<LineExtensionAmount>200</LineExtensionAmount><LineExtensionAmountTaxInclusive>224</LineExtensionAmountTaxInclusive>\n'
            '      <LineExtensionTaxAmount>24</LineExtensionTaxAmount><UnitPrice>100</UnitPrice><UnitPriceTaxInclusive>112</UnitPriceTaxInclusive>\n'
            '      <ClassifiedTaxCategory><Percent>12</Percent><VATCalculationMethod>0</VATCalculationMethod><VATApplicable>true</VATApplicable></ClassifiedTaxCategory>',
            '<LineExtensionAmount>200</LineExtensionAmount><LineExtensionAmountTaxInclusive>200</LineExtensionAmountTaxInclusive>\n'
            '      <LineExtensionTaxAmount>0</LineExtensionTaxAmount><UnitPrice>100</UnitPrice><UnitPriceTaxInclusive>100</UnitPriceTaxInclusive>\n'
            '      <ClassifiedTaxCategory><Percent>21</Percent><VATCalculationMethod>0</VATCalculationMethod><VATApplicable>true</VATApplicable>'
            '<LocalReverseCharge><LocalReverseChargeCode>4</LocalReverseChargeCode></LocalReverseCharge></ClassifiedTaxCategory>', 1)
        self.assertIn('LocalReverseCharge', xml)
        return xml.encode()

    def test_a_reverse_charge_line_takes_the_reverse_charge_tax(self):
        rc_tax = self.env['account.tax'].create({
            'name': "21% RC", 'amount': 21.0, 'amount_type': 'percent',
            'type_tax_use': 'purchase', 'company_id': self.company.id})
        self.env['ir.model.data'].create({
            'module': 'account', 'model': 'account.tax', 'res_id': rc_tax.id,
            'name': f'{self.company.id}_l10n_cz_21_tax_reverse_charge_scheme'})
        invoice = self._import(self._reverse_charge_invoice())
        rc_line = invoice.invoice_line_ids.filtered(lambda l: l.name == "Zboží A")
        self.assertEqual(rc_line.tax_ids, rc_tax)
        other = invoice.invoice_line_ids.filtered(lambda l: l.name == "Zboží B")
        self.assertEqual(other.tax_ids, self.taxes[12.0])

    def test_a_reverse_charge_line_never_takes_the_ordinary_rate(self):
        """Without a reverse-charge tax the line is left untaxed: the ordinary
        21 % would bill the supplier's VAT that the supplier never charged."""
        invoice = self._import(self._reverse_charge_invoice())
        rc_line = invoice.invoice_line_ids.filtered(lambda l: l.name == "Zboží A")
        self.assertFalse(rc_line.tax_ids)
        self.assertAlmostEqual(invoice.amount_tax, 36.0, places=2, msg="only the 12 % line's VAT")
