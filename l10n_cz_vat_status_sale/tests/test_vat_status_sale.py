# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestCzVatStatusSale(AccountTestInvoicingCommon):

    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        ref = cls.env["account.chart.template"].with_company(cls.company).ref
        cls.sale21 = ref("l10n_cz_21_domestic_supplies")
        cls.product = cls.env["product.product"].create({
            "name": "Služba", "type": "service", "lst_price": 100.0,
            "taxes_id": [Command.set(cls.sale21.ids)]})
        cls.partner = cls.env["res.partner"].create({"name": "Zákazník"})
        cls.env.user.group_ids |= cls.env.ref("sales_team.group_sale_manager")

    def _order(self, day):
        return self.env["sale.order"].create({
            "partner_id": self.partner.id, "date_order": "%s 10:00:00" % day,
            "order_line": [Command.create({"product_id": self.product.id})]})

    def test_order_taxes_follow_the_status_on_the_order_date(self):
        self.env["l10n.cz.vat.status.period"].create({
            "company_id": self.company.id, "date_from": "2026-07-01",
            "status": "non_payer"})
        self.assertEqual(self._order("2026-06-30").order_line.tax_ids, self.sale21)
        self.assertFalse(self._order("2026-07-01").order_line.tax_ids)

    def test_no_history_leaves_orders_alone(self):
        self.assertEqual(self._order("2026-07-01").order_line.tax_ids, self.sale21)
