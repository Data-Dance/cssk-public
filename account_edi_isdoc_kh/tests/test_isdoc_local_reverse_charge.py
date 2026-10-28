# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import Command, fields
from odoo.tests import tagged
from odoo.tools import file_open

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

NS = {"i": "http://isdoc.cz/namespace/2013"}


@tagged("post_install", "-at_install")
class TestIsdocLocalReverseCharge(AccountTestInvoicingCommon):

    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.partner_id.write({
            "street": "Příhon 943", "zip": "696 15", "city": "Čejkovice",
            "vat": "CZ46342958", "company_registry": "46342958",
        })
        cls.customer = cls.env["res.partner"].create({
            "name": "Odběratel s.r.o.", "street": "Diabasová 1141/11",
            "zip": "15500", "city": "Praha 13", "vat": "CZ25663585",
            "company_registry": "25663585",
            "country_id": cls.env.ref("base.cz").id,
        })
        ChartTemplate = cls.env["account.chart.template"].with_company(cls.company)
        cls.tax_rc = ChartTemplate.ref("l10n_cz_tax_reverse_charge_mode")
        vat1 = cls.env["account.account.tag"]._get_tax_tags(
            "VAT 1 Base", cls.env.ref("base.cz").id)
        cls.tax_21 = cls.env["account.tax"].search([
            ("type_tax_use", "=", "sale"), ("amount", "=", 21.0),
            ("company_id", "=", cls.company.id),
            ("invoice_repartition_line_ids.tag_ids", "in", vat1.ids),
        ], limit=1)
        cls.tax_exempt = cls.env["account.tax"].create({
            "name": "0% exempt", "amount": 0.0, "amount_type": "percent",
            "type_tax_use": "sale", "company_id": cls.company.id,
        })
        cls.construction = cls.env["product.product"].create({
            "name": "Stavební práce", "type": "service",
            "cssk_kh_commodity_code": "4",
        })
        cls.uncoded = cls.env["product.product"].create({
            "name": "Montáž", "type": "service",
        })
        with file_open("account_edi_isdoc/tests/schema/isdoc-invoice-6.0.2.xsd", "rb") as f:
            cls.schema = etree.XMLSchema(etree.parse(f))

    def _invoice(self, lines, move_type="out_invoice"):
        invoice = self.env["account.move"].create({
            "move_type": move_type,
            "partner_id": self.customer.id,
            "invoice_date": fields.Date.today(),
            "invoice_line_ids": [
                Command.create({
                    "product_id": product.id, "name": product.name,
                    "quantity": 1, "price_unit": price,
                    "tax_ids": [Command.set(tax.ids)],
                })
                for product, price, tax in lines
            ],
        })
        invoice.action_post()
        return invoice

    def _export(self, invoice, expect_errors=False):
        xml, errors = self.env["account.edi.xml.isdoc"]._export_invoice(invoice)
        if expect_errors:
            return errors
        self.assertFalse(errors, errors)
        root = etree.fromstring(xml)
        self.schema.assertValid(root)
        return root

    def test_reverse_charge_line_carries_code(self):
        """§ 92a ZDPH: the reverse-charge line says so and carries the code
        the customer reports in KH B.1."""
        invoice = self._invoice([
            (self.construction, 1000.0, self.tax_rc),
            (self.uncoded, 500.0, self.tax_21),
        ])
        root = self._export(invoice)
        lines = root.findall("i:InvoiceLines/i:InvoiceLine", NS)
        rc, ordinary = lines
        self.assertEqual(rc.findtext(
            "i:ClassifiedTaxCategory/i:LocalReverseCharge/i:LocalReverseChargeCode",
            namespaces=NS), "4")
        self.assertEqual(rc.findtext("i:ClassifiedTaxCategory/i:VATApplicable",
                                     namespaces=NS), "true")
        self.assertEqual(rc.findtext("i:LineExtensionTaxAmount", namespaces=NS), "0.00")
        self.assertIsNone(ordinary.find("i:ClassifiedTaxCategory/i:LocalReverseCharge", NS))
        flags = {
            sub.findtext("i:TaxCategory/i:Percent", namespaces=NS):
                sub.findtext("i:TaxCategory/i:LocalReverseChargeFlag", namespaces=NS)
            for sub in root.findall("i:TaxTotal/i:TaxSubTotal", NS)
        }
        self.assertEqual(flags, {"0.00": "true", "21.00": None})
        self.assertEqual(root.findtext("i:VATApplicable", namespaces=NS), "true")

    def test_reverse_charge_kept_apart_from_exempt_supply(self):
        """Both are 0 %; merged, the customer could not tell the reverse
        charge it must self-assess from the exempt supply it must not."""
        invoice = self._invoice([
            (self.construction, 1000.0, self.tax_rc),
            (self.uncoded, 300.0, self.tax_exempt),
        ])
        root = self._export(invoice)
        rows = [
            (sub.findtext("i:TaxableAmount", namespaces=NS),
             sub.findtext("i:TaxCategory/i:VATApplicable", namespaces=NS),
             sub.findtext("i:TaxCategory/i:LocalReverseChargeFlag", namespaces=NS))
            for sub in root.findall("i:TaxTotal/i:TaxSubTotal", NS)
        ]
        self.assertEqual(sorted(rows, key=str), sorted([
            ("1000.00", "true", "true"),
            ("300.00", "false", None),
        ], key=str))

    def test_only_reverse_charge_invoice_is_subject_to_vat(self):
        root = self._export(self._invoice([(self.construction, 1000.0, self.tax_rc)]))
        self.assertEqual(root.findtext("i:VATApplicable", namespaces=NS), "true")

    def test_credit_note(self):
        root = self._export(self._invoice(
            [(self.construction, 200.0, self.tax_rc)], move_type="out_refund"))
        self.assertEqual(root.findtext(
            "i:InvoiceLines/i:InvoiceLine/i:ClassifiedTaxCategory/"
            "i:LocalReverseCharge/i:LocalReverseChargeCode", namespaces=NS), "4")

    def test_code_from_the_reverse_charge_tax(self):
        """l10n_cz_kh's fallback: the code of a tax flagged as reverse
        charge, when the product has none."""
        tax = self.tax_rc.copy({
            "name": "0% RC kovy",
            "cssk_control_is_reverse_charge": True,
            "cssk_kh_commodity_code": "13",
        })
        root = self._export(self._invoice([(self.uncoded, 800.0, tax)]))
        self.assertEqual(root.findtext(
            "i:InvoiceLines/i:InvoiceLine/i:ClassifiedTaxCategory/"
            "i:LocalReverseCharge/i:LocalReverseChargeCode", namespaces=NS), "13")

    def test_missing_code_is_refused(self):
        errors = self._export(
            self._invoice([(self.uncoded, 1000.0, self.tax_rc)]), expect_errors=True)
        self.assertTrue(any("KH commodity code" in e for e in errors), errors)

    def test_ordinary_invoice_unchanged(self):
        root = self._export(self._invoice([(self.construction, 1000.0, self.tax_21)]))
        self.assertIsNone(root.find(".//i:LocalReverseCharge", NS))
        self.assertIsNone(root.find(".//i:LocalReverseChargeFlag", NS))
