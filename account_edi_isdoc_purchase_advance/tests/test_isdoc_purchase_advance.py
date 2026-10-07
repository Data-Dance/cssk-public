# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged

ISDOC_NS = "http://isdoc.cz/namespace/2013"

_SUPPLIER_PARTY = """
  <AccountingSupplierParty><Party>
    <PartyIdentification><ID>29261783</ID></PartyIdentification>
    <PartyName><Name>Dodavatel s.r.o.</Name></PartyName>
    <PostalAddress><StreetName>Hlavni</StreetName><BuildingNumber>1</BuildingNumber>
      <CityName>Praha</CityName><PostalZone>11000</PostalZone>
      <Country><IdentificationCode>CZ</IdentificationCode><Name>CZ</Name></Country></PostalAddress>
    <PartyTaxScheme><CompanyID>CZ29261783</CompanyID><TaxScheme>VAT</TaxScheme></PartyTaxScheme>
  </Party></AccountingSupplierParty>
  <AccountingCustomerParty><Party>
    <PartyIdentification><ID>46342958</ID></PartyIdentification>
    <PartyName><Name>My Company</Name></PartyName>
    <PostalAddress><StreetName>Vedlejsi</StreetName><BuildingNumber>2</BuildingNumber>
      <CityName>Brno</CityName><PostalZone>60200</PostalZone>
      <Country><IdentificationCode>CZ</IdentificationCode><Name>CZ</Name></Country></PostalAddress>
    <PartyTaxScheme><CompanyID>CZ46342958</CompanyID><TaxScheme>VAT</TaxScheme></PartyTaxScheme>
  </Party></AccountingCustomerParty>
"""


def _proforma(ref="ZF-2026-77", gross="1210"):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="{ISDOC_NS}" version="6.0.2">
  <DocumentType>4</DocumentType>
  <ID>{ref}</ID>
  <UUID>44444444-4444-4444-4444-444444444444</UUID>
  <IssueDate>2026-07-01</IssueDate>
  <VATApplicable>false</VATApplicable>
  <ElectronicPossibilityAgreementReference languageID="cs">http://</ElectronicPossibilityAgreementReference>
  <LocalCurrencyCode>CZK</LocalCurrencyCode>
  <CurrRate>1</CurrRate><RefCurrRate>1</RefCurrRate>
  {_SUPPLIER_PARTY}
  <InvoiceLines><InvoiceLine>
    <ID>1</ID>
    <InvoicedQuantity unitCode="ks">1</InvoicedQuantity>
    <LineExtensionAmount>{gross}</LineExtensionAmount>
    <LineExtensionAmountTaxInclusive>{gross}</LineExtensionAmountTaxInclusive>
    <LineExtensionTaxAmount>0</LineExtensionTaxAmount>
    <UnitPrice>{gross}</UnitPrice>
    <UnitPriceTaxInclusive>{gross}</UnitPriceTaxInclusive>
    <ClassifiedTaxCategory><Percent>0</Percent><VATCalculationMethod>0</VATCalculationMethod><VATApplicable>false</VATApplicable></ClassifiedTaxCategory>
    <Item><Description>Zaloha</Description></Item>
  </InvoiceLine></InvoiceLines>
  <TaxTotal><TaxSubTotal>
    <TaxableAmount>{gross}</TaxableAmount><TaxAmount>0</TaxAmount><TaxInclusiveAmount>{gross}</TaxInclusiveAmount>
    <TaxCategory><Percent>0</Percent><VATApplicable>false</VATApplicable></TaxCategory>
  </TaxSubTotal><TaxAmount>0</TaxAmount></TaxTotal>
  <LegalMonetaryTotal>
    <TaxExclusiveAmount>{gross}</TaxExclusiveAmount><TaxInclusiveAmount>{gross}</TaxInclusiveAmount>
    <PayableAmount>{gross}</PayableAmount>
  </LegalMonetaryTotal>
</Invoice>"""


def _tax_document(ref="DD-2026-55", order_ref="", vs="", net="1000",
                  tax="210", gross="1210"):
    order_refs = (
        f"<OrderReferences><OrderReference>"
        f"<ExternalOrderID>{order_ref}</ExternalOrderID>"
        f"</OrderReference></OrderReferences>"
        if order_ref else ""
    )
    payment_means = (
        f"<PaymentMeans><Payment>"
        f"<PaidAmount>{gross}</PaidAmount><PaymentMeansCode>42</PaymentMeansCode>"
        f"<Details><PaymentDueDate>2026-07-15</PaymentDueDate>"
        f"<ID></ID><BankCode></BankCode><Name></Name><IBAN></IBAN><BIC></BIC>"
        f"<VariableSymbol>{vs}</VariableSymbol>"
        f"</Details></Payment></PaymentMeans>"
        if vs else ""
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="{ISDOC_NS}" version="6.0.2">
  <DocumentType>5</DocumentType>
  <ID>{ref}</ID>
  <UUID>55555555-5555-5555-5555-555555555555</UUID>
  <IssueDate>2026-07-10</IssueDate>
  <TaxPointDate>2026-07-08</TaxPointDate>
  <VATApplicable>true</VATApplicable>
  <ElectronicPossibilityAgreementReference languageID="cs">http://</ElectronicPossibilityAgreementReference>
  <LocalCurrencyCode>CZK</LocalCurrencyCode>
  <CurrRate>1</CurrRate><RefCurrRate>1</RefCurrRate>
  {order_refs}
  {_SUPPLIER_PARTY}
  <InvoiceLines><InvoiceLine>
    <ID>1</ID>
    <InvoicedQuantity unitCode="ks">1</InvoicedQuantity>
    <LineExtensionAmount>{net}</LineExtensionAmount>
    <LineExtensionAmountTaxInclusive>{gross}</LineExtensionAmountTaxInclusive>
    <LineExtensionTaxAmount>{tax}</LineExtensionTaxAmount>
    <UnitPrice>{net}</UnitPrice>
    <UnitPriceTaxInclusive>{gross}</UnitPriceTaxInclusive>
    <ClassifiedTaxCategory><Percent>21</Percent><VATCalculationMethod>0</VATCalculationMethod><VATApplicable>true</VATApplicable></ClassifiedTaxCategory>
    <Item><Description>Danovy doklad k platbe</Description></Item>
  </InvoiceLine></InvoiceLines>
  {payment_means}
  <TaxTotal><TaxSubTotal>
    <TaxableAmount>{net}</TaxableAmount><TaxAmount>{tax}</TaxAmount><TaxInclusiveAmount>{gross}</TaxInclusiveAmount>
    <TaxCategory><Percent>21</Percent><VATApplicable>true</VATApplicable></TaxCategory>
  </TaxSubTotal><TaxAmount>{tax}</TaxAmount></TaxTotal>
  <LegalMonetaryTotal>
    <TaxExclusiveAmount>{net}</TaxExclusiveAmount><TaxInclusiveAmount>{gross}</TaxInclusiveAmount>
    <PayableAmount>{gross}</PayableAmount>
  </LegalMonetaryTotal>
</Invoice>"""


@tagged("post_install", "-at_install")
class TestIsdocPurchaseAdvance(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids |= cls.env.ref("purchase.group_purchase_manager")
        cls.company = cls.env.company
        Account = cls.env["account.account"]
        cls.clearing = Account.create({
            "code": "314001", "name": "Paid advances clearing",
            "account_type": "liability_payable", "reconcile": True,
        })
        cls.net_advance = Account.create({
            "code": "314000", "name": "Paid advances",
            "account_type": "asset_current",
        })
        cls.adv_journal = cls.env["account.journal"].create({
            "name": "Advance Tax Documents (Purchase)",
            "code": "PDADV", "type": "purchase",
        })
        cls.company.advance_purchase_journal_id = cls.adv_journal
        cls.company.advance_paid_clearing_account_id = cls.clearing
        cls.company.advance_paid_account_id = cls.net_advance
        cls.supplier = cls.env["res.partner"].create({
            "name": "Dodavatel s.r.o.", "vat": "CZ29261783",
            "country_id": cls.env.ref("base.cz").id,
        })
        cls.tax_purchase_21 = cls.env["account.tax"].create({
            "name": "DPH 21% (nákup)", "amount": 21.0,
            "amount_type": "percent", "type_tax_use": "purchase",
            "company_id": cls.company.id,
        })

    def _import(self, xml, move_type="in_invoice"):
        invoice = self.env["account.move"].create({
            "move_type": move_type,
            "journal_id": self.company_data["default_journal_purchase"].id,
        })
        self.env["account.edi.xml.isdoc"]._import_invoice_ubl_cii(
            invoice,
            {
                "xml_tree": etree.fromstring(xml.encode()),
                "attachment": self.env["ir.attachment"],
            },
        )
        return invoice

    def _paid_advance(self, price=1210.0):
        order = self.env["purchase.order"].create({
            "partner_id": self.supplier.id,
            "is_advance_invoice": True,
            "order_line": [
                Command.create({
                    "product_id": self.env.ref(
                        "account_edi_isdoc_purchase_advance"
                        ".product_imported_advance"
                    ).id,
                    "product_qty": 1,
                    "price_unit": price,
                    "tax_ids": [Command.clear()],
                })
            ],
        })
        bank_journal = self.company_data["default_journal_bank"]
        method_line = bank_journal.outbound_payment_method_line_ids[:1]
        if not method_line.payment_account_id:
            method_line.payment_account_id = self.env["account.account"].create({
                "code": "OUTPAY", "name": "Outstanding Payments",
                "account_type": "asset_current", "reconcile": True,
            })
        wizard = self.env["purchase.advance.payment.wizard"].with_context(
            active_model="purchase.order", active_id=order.id
        ).create({
            "journal_id": bank_journal.id,
            "payment_method_line_id": method_line.id,
        })
        wizard.action_create_payment()
        return order

    def test_proforma_creates_received_advance(self):
        invoice = self._import(_proforma(ref="ZF-2026-77", gross="1210"))
        order = invoice.advance_purchase_order_id
        self.assertTrue(order)
        self.assertTrue(order.is_advance_invoice)
        self.assertTrue(order.name.startswith("PADV"))
        self.assertEqual(order.partner_ref, "ZF-2026-77")
        self.assertEqual(order.partner_id, self.supplier)
        self.assertAlmostEqual(order.amount_total, 1210.0)
        self.assertFalse(order.order_line.tax_ids)

    def test_tax_document_matched_by_order_reference(self):
        advance = self._paid_advance()
        invoice = self._import(_tax_document(order_ref=advance.name))
        self.assertEqual(invoice.journal_id, self.adv_journal)
        self.assertEqual(invoice.advance_purchase_order_id, advance)
        self.assertEqual(str(invoice.taxable_supply_date), "2026-07-08")
        product_lines = invoice.invoice_line_ids.filtered(
            lambda line: line.display_type == "product"
        )
        self.assertEqual(product_lines.account_id, self.net_advance)
        term_lines = invoice.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        )
        self.assertEqual(term_lines.account_id, self.clearing)

    def test_tax_document_matched_by_amount(self):
        advance = self._paid_advance(price=1210.0)
        invoice = self._import(_tax_document())
        self.assertEqual(invoice.advance_purchase_order_id, advance)

    def test_tax_document_ambiguous_bails(self):
        self._paid_advance(price=1210.0)
        self._paid_advance(price=1210.0)
        invoice = self._import(_tax_document())
        self.assertFalse(invoice.advance_purchase_order_id)
        # journal/accounts still routed — it IS an advance tax document
        self.assertEqual(invoice.journal_id, self.adv_journal)
