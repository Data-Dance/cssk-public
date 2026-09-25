from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestSkEuServices(AccountTestInvoicingCommon):
    """A service bought from an EU supplier is § 69 ods. 3, not an acquisition
    of goods — row 09, not row 07.

    Reported by an external accountant: stock ``l10n_sk`` maps every purchase
    tax under "Eu intra" to the goods-acquisition taxes, and has nothing for
    services at all."""

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cid = cls.company.id
        cls.fp_eu = cls.env.ref("account.%s_fiscal_position_template_2" % cid)
        cls.dom_s = cls.env.ref("account.%s_vs_tuz_23_s" % cid)
        cls.eu_s = cls.env.ref("account.%s_vs_eu_s_23" % cid)
        cls.supplier = cls.env["res.partner"].create({
            "name": "Hosting GmbH", "country_id": cls.env.ref("base.de").id,
            "vat": "DE123456788"})

    def _tags(self, lines):
        return set(lines.tax_tag_ids.mapped("name"))

    def test_the_eu_position_sends_services_to_row_09_and_goods_to_row_07(self):
        self.assertEqual(self.dom_s.tax_scope, "service")
        self.assertEqual(self.fp_eu.map_tax(self.dom_s), self.eu_s)
        goods = self.env.ref("account.%s_vs_tuz_23" % self.company.id)
        self.assertEqual(
            self.fp_eu.map_tax(goods),
            self.env.ref("account.%s_vs_nad_eu_23" % self.company.id),
            "goods must still map to the acquisition of goods")

    def test_a_received_eu_service_self_assesses_in_09b_and_10b(self):
        bill = self.env["account.move"].create({
            "move_type": "in_invoice", "partner_id": self.supplier.id,
            "fiscal_position_id": self.fp_eu.id,
            "invoice_date": "2026-06-10",
            "invoice_line_ids": [Command.create({
                "name": "Hosting", "quantity": 1, "price_unit": 1000.0,
                "tax_ids": [Command.set(self.eu_s.ids)]})],
        })
        bill.action_post()
        self.assertEqual(bill.amount_tax, 0.0, "self-assessed: the legs net")
        base = bill.line_ids.filtered("tax_ids")
        self.assertIn("09b", {t.lstrip("+-") for t in self._tags(base)})
        tax_tags = self._tags(bill.line_ids.filtered("tax_line_id"))
        self.assertTrue(
            any(t.lstrip("+-") == "19" for t in tax_tags)
            and any(t.lstrip("+-") == "10b" for t in tax_tags), tax_tags)
        if "cssk_control_is_reverse_charge" in self.eu_s._fields:
            self.assertTrue(self.eu_s.cssk_control_is_reverse_charge)
            self.assertEqual(base.cssk_control_section_code, "B.1")

    def test_an_existing_company_gets_only_what_it_lacks(self):
        Chart = self.env["account.chart.template"]
        self.assertEqual(Chart._cssk_load_sk_eu_service_taxes(self.company), 0)
        five = self.env.ref("account.%s_vs_eu_s_5" % self.company.id)
        five.unlink()
        self.assertEqual(Chart._cssk_load_sk_eu_service_taxes(self.company), 1)
        again = self.env.ref("account.%s_vs_eu_s_5" % self.company.id)
        self.assertEqual(len(again.repartition_line_ids), 6)
        self.assertEqual(
            self.env["account.tax"].search_count([
                ("company_id", "=", self.company.id),
                ("name", "=", self.eu_s.name)]), 1,
            "re-running must not duplicate a tax that exists")

    def test_a_company_missing_what_the_taxes_refer_to_is_skipped(self):
        """Raised by a second-opinion review: the loader runs in the install
        hook and the upgrade, where one company's broken chart must not abort
        the module for every company."""
        for xmlid in ("vs_eu_s_23", "vs_eu_s_19", "vs_eu_s_5"):
            self.env.ref("account.%s_%s" % (self.company.id, xmlid)).unlink()
        self.fp_eu.unlink()
        with self.assertLogs(
                "odoo.addons.l10n_sk_vat_return.models.account_chart_template",
                level="WARNING"):
            loaded = self.env["account.chart.template"]\
                ._cssk_load_sk_eu_service_taxes(self.company)
        self.assertEqual(loaded, 0)
