"""ř. 30 / ř. 31: the middle party of a § 17 triangular trade."""

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestCzTriangularTrade(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.vat = "CZ25663585"
        cls.version = cls.env.ref("l10n_cz_vat_return.dphdp3_version_2025")
        cls.partner = cls.env["res.partner"].create({
            "name": "Käufer GmbH", "vat": "DE811907980",
            "country_id": cls.env.ref("base.de").id})
        cls.supply = cls._tagged_tax("sale", "VAT 31")
        cls.acquisition = cls._tagged_tax("purchase", "VAT 30")

    @classmethod
    def _tagged_tax(cls, use, tag_name):
        tag = cls.env["account.account.tag"].search([
            ("name", "=", tag_name), ("applicability", "=", "taxes"),
            ("country_id.code", "=", "CZ")], limit=1)
        tax = cls.env["account.tax"].create({
            "name": "triangular %s" % use, "amount": 0.0,
            "amount_type": "percent", "type_tax_use": use,
            "company_id": cls.company.id,
            "country_id": cls.company.account_fiscal_country_id.id,
        })
        for side in ("invoice_repartition_line_ids", "refund_repartition_line_ids"):
            tax[side].filtered(
                lambda r: r.repartition_type == "base").tag_ids = tag
        return tax

    def _doc(self, move_type, tax, amount):
        move = self.env["account.move"].create({
            "move_type": move_type, "partner_id": self.partner.id,
            "invoice_date": "2025-06-15", "date": "2025-06-15",
            "taxable_supply_date": "2025-06-15",
            "invoice_line_ids": [Command.create({
                "name": "x", "quantity": 1, "price_unit": amount,
                "tax_ids": [Command.set(tax.ids)]})],
        })
        move.action_post()
        return move

    def _value(self, code):
        ret = self.env["cssk.vat.return"].create({
            "company_id": self.company.id, "version_id": self.version.id,
            "statement_type_id": self.env.ref(
                "l10n_cz_vat_return.dphdp3_type_B").id,
            "period_type": "month",
            "date_from": "2025-06-01", "date_to": "2025-06-30",
        })
        ret.action_compute_lines()
        return ret.line_ids.filtered(lambda l: l.code == code).value

    def test_the_supply_of_the_middle_party_is_computed_on_r31(self):
        """It was a manual line; a supply tagged VAT 31 now reaches it."""
        self._doc("out_invoice", self.supply, 1000.0)
        self._doc("out_refund", self.supply, 300.0)
        self.assertEqual(self._value("tri_dozb"), 700.0)

    def test_the_acquisition_of_the_middle_party_is_on_r30(self):
        self._doc("in_invoice", self.acquisition, 500.0)
        self.assertEqual(self._value("tri_pozb"), 500.0)
