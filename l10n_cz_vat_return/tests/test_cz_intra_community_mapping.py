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


@tagged("post_install", "-at_install")
class TestCzIntraCommunitySaleMapping(AccountTestInvoicingCommon):
    """The Intra-Community position must tell goods from services on SALES.

    ``l10n_cz`` gives ``0% EU S`` the domestic GOODS sale taxes as originals,
    so a goods line sold to an EU VAT payer got ``0% EU G`` and ``0% EU S``
    (the base declared twice, as goods and as a service) while ``21% S``
    stayed ``21% S``.
    """

    chart_template = "cz"

    def _ref(self, xmlid):
        return self.env["account.chart.template"].ref(xmlid)

    def test_goods_get_one_tax_and_services_are_mapped(self):
        position = self._ref("fiscal_position_intra_community")
        goods_eu = self._ref("l10n_cz_supply_goods_eu")
        service_eu = self._ref("l10n_cz_supply_service_eu")
        for src, dest in (
            ("l10n_cz_21_domestic_supplies", goods_eu),
            ("l10n_cz_12_domestic_supplies", goods_eu),
            ("l10n_cz_21_domestic_services", service_eu),
            ("l10n_cz_12_domestic_service", service_eu),
        ):
            self.assertEqual(
                position.map_tax(self._ref(src)), dest,
                "%s must become %s alone under Intra-Community"
                % (src, dest.name))

    def test_eu_customer_invoice_has_one_tax_per_line(self):
        position = self._ref("fiscal_position_intra_community")
        lines = []
        for name, scope, tax in (
            ("EU goods", "consu", "l10n_cz_21_domestic_supplies"),
            ("EU service", "service", "l10n_cz_21_domestic_services"),
        ):
            product = self.env["product.product"].create({
                "name": name, "type": scope,
                "taxes_id": [(6, 0, self._ref(tax).ids)],
            })
            lines.append((0, 0, {"product_id": product.id, "price_unit": 100.0,
                                 "quantity": 1}))
        invoice = self.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": self.partner_a.id,
            "fiscal_position_id": position.id,
            "invoice_date": "2026-09-01",
            "invoice_line_ids": lines,
        })
        goods, service = invoice.invoice_line_ids
        self.assertEqual(goods.tax_ids, self._ref("l10n_cz_supply_goods_eu"))
        self.assertEqual(service.tax_ids, self._ref("l10n_cz_supply_service_eu"))
        self.assertAlmostEqual(invoice.amount_total, 200.0)

    def test_the_repair_is_idempotent_and_keeps_other_links(self):
        service_eu = self._ref("l10n_cz_supply_service_eu")
        other = self._ref("l10n_cz_other_transaction_deduction")
        self.assertIn(other, service_eu.original_tax_ids)
        self.assertEqual(
            self.env.company._cz_map_intra_community_sale_service_taxes(), 0,
            "a second run must report no change")

    def test_historical_rates_are_mapped_alike(self):
        """The archived 20 % / 15 % ... copies carry the chart's wiring too."""
        Tax = self.env["account.tax"].with_context(active_test=False)
        service_eu = self._ref("l10n_cz_supply_service_eu").with_context(active_test=False)
        clones = Tax.search([
            ("company_id", "=", self.env.company.id),
            ("cssk_historic_source_tax_id", "!=", False),
            ("type_tax_use", "=", "sale"),
            ("tax_scope", "in", ("consu", "service")),
        ])
        if not clones:
            self.skipTest("no historical sale rates in this company")
        for clone in clones:
            if clone.cssk_historic_source_tax_id in service_eu.original_tax_ids \
                    or clone.cssk_historic_source_tax_id == service_eu:
                continue
            if clone.tax_scope == "consu":
                self.assertNotIn(clone, service_eu.original_tax_ids,
                                 "%s still maps to 0%% EU S" % clone.name)
        services = clones.filtered(
            lambda t: t.cssk_historic_source_tax_id in (
                self._ref("l10n_cz_21_domestic_services")
                | self._ref("l10n_cz_12_domestic_service")))
        self.assertTrue(services, "no historical service rates to check")
        for clone in services:
            self.assertIn(clone, service_eu.original_tax_ids,
                          "%s does not map to 0%% EU S" % clone.name)
