# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestCzIntraCommunityMapping(AccountTestInvoicingCommon):
    """The Intra-Community position must replace the domestic purchase tax.

    ``l10n_cz`` gives its four EU acquisition taxes no original tax, so
    ``map_tax(21% G)`` returned ``21% G`` and a vendor bill from an EU
    supplier charged Czech VAT instead of self-assessing it: 30.00 of goods
    billed at 36.30.
    """

    chart_template = "cz"

    def _ref(self, xmlid):
        return self.env["account.chart.template"].ref(xmlid)

    def test_domestic_purchase_taxes_map_to_eu_acquisition(self):
        position = self._ref("fiscal_position_intra_community")
        for src, dest in (
            ("l10n_cz_21_receipt_domestic_supplies",
             "l10n_cz_21_acquisition_goods_eu"),
            ("l10n_cz_12_receipt_domestic_supplies",
             "l10n_cz_12_purchase_goods_eu"),
            ("l10n_cz_21_receipt_domestic_services",
             "l10n_cz_21_receipt_service_person_eu"),
            ("l10n_cz_12_receipt_domestic_service",
             "l10n_cz_12_receipt_service_person_eu"),
        ):
            self.assertEqual(
                position.map_tax(self._ref(src)), self._ref(dest),
                "%s must become %s under Intra-Community" % (src, dest))

    def test_eu_vendor_bill_self_assesses(self):
        position = self._ref("fiscal_position_intra_community")
        domestic = self._ref("l10n_cz_21_receipt_domestic_supplies")
        product = self.env["product.product"].create({
            "name": "EU goods", "type": "consu",
            "supplier_taxes_id": [(6, 0, domestic.ids)],
        })
        bill = self.env["account.move"].create({
            "move_type": "in_invoice",
            "partner_id": self.partner_a.id,
            "fiscal_position_id": position.id,
            "invoice_date": "2026-09-01",
            "invoice_line_ids": [(0, 0, {
                "product_id": product.id, "price_unit": 30.0, "quantity": 1,
            })],
        })
        self.assertEqual(
            bill.invoice_line_ids.tax_ids,
            self._ref("l10n_cz_21_acquisition_goods_eu"))
        self.assertAlmostEqual(bill.amount_total, 30.0)

    def test_the_repair_is_idempotent_and_keeps_manual_links(self):
        company = self.env.company
        dest = self._ref("l10n_cz_21_acquisition_goods_eu")
        extra = self._ref("l10n_cz_21_tax_reverse_charge_scheme")
        dest.original_tax_ids = [(4, extra.id)]
        self.assertEqual(company._cz_map_intra_community_purchase_taxes(), 0)
        self.assertIn(extra, dest.original_tax_ids)


@tagged("post_install", "-at_install")
class TestCzExtraCommunityMapping(AccountTestInvoicingCommon):
    """The Extra-Community position must tell goods from services.

    ``l10n_cz`` points BOTH extra-Community service taxes at the domestic
    **goods** tax, so the position mapped one 1 000 CZK line onto three taxes
    — ``21% EX G``, ``21% EX S`` and ``0% EX G.Custom`` — declaring the same
    purchase on ř. 7, ř. 12 and ř. 42 and deducting 420.00 on ř. 43 against a
    real 210.00. The bill still totalled 1 000.00, because each
    self-assessment cancels itself, so nothing on the document disagreed.
    """

    chart_template = "cz"

    def _ref(self, xmlid):
        return self.env["account.chart.template"].ref(xmlid)

    def test_a_service_bought_outside_the_eu_self_assesses(self):
        """The direction nobody notices: ``21% S`` mapped to nothing at all.

        So the Czech 21 % the foreign supplier never charged stayed on the
        bill, and ř. 12 reported nothing.
        """
        position = self._ref("fiscal_position_extra_community")
        for src, dest in (
            ("l10n_cz_21_receipt_domestic_services",
             "l10n_cz_21_receipt_service_person_non_eu"),
            ("l10n_cz_12_receipt_domestic_service",
             "l10n_cz_12_receipt_service_person_non_eu"),
        ):
            self.assertIn(
                self._ref(dest), position.map_tax(self._ref(src)),
                "%s must become %s under Extra-Community" % (src, dest))

    def test_goods_are_not_also_declared_as_a_service(self):
        """``map_tax`` returns a LIST, so a wrong source is not harmless."""
        position = self._ref("fiscal_position_extra_community")
        for goods in ("l10n_cz_21_receipt_domestic_supplies",
                      "l10n_cz_12_receipt_domestic_supplies"):
            mapped = position.map_tax(self._ref(goods))
            services = mapped.filtered(lambda t: t.tax_scope == "service")
            self.assertFalse(
                services,
                "%s is also self-assessed as a service: %s"
                % (goods, mapped.mapped("name")))

    def test_the_repair_is_idempotent(self):
        self.assertEqual(
            self.env.company._cz_map_extra_community_service_taxes(), 0,
            "a second run must report no change")
