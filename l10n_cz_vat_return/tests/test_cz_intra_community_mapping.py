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
