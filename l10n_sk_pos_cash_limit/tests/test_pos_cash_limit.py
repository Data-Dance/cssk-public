# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import Command
from odoo.tests import tagged

from odoo.addons.point_of_sale.tests.test_frontend import TestPointOfSaleHttpCommon


@tagged("post_install", "-at_install")
class TestPosCashLimit(TestPointOfSaleHttpCommon):
    @classmethod
    @TestPointOfSaleHttpCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        for name, price in (("Strieborná tehla", 4000.0), ("Zlatá tehla", 6000.0)):
            cls.env["product.template"].create({
                "name": name,
                "available_in_pos": True,
                "list_price": price,
                "taxes_id": [Command.clear()],
                "pos_categ_ids": [Command.set(cls.pos_desk_misc_test.ids)],
            })
        cls.cash_method = cls.main_pos_config.payment_method_ids.filtered("is_cash_count")

    def _order(self, payments):
        return self.env["pos.order"].new({
            "company_id": self.main_pos_config.company_id.id,
            "payment_ids": [
                Command.create({"amount": amount, "payment_method_id": method.id})
                for method, amount in payments
            ],
        })

    def test_cash_above_the_limit_is_flagged(self):
        order = self._order([(self.cash_method, 5000.01)])
        self.assertIn("394/2012", order.l10n_sk_cash_limit_warning)

    def test_change_and_card_are_netted_off(self):
        order = self._order([
            (self.cash_method, 5500.0), (self.cash_method, -600.0),
            (self.bank_payment_method, 2000.0),
        ])
        self.assertFalse(order.l10n_sk_cash_limit_warning)

    def test_till_asks_before_taking_too_much_cash(self):
        self.main_pos_config.with_user(self.pos_user).open_ui()
        self.start_pos_tour("l10n_sk_pos_cash_limit_tour")
        orders = self.env["pos.order"].search(
            [("session_id", "=", self.main_pos_config.current_session_id.id)]
        )
        self.assertEqual(sorted(orders.mapped("amount_total")), [4000.0, 6000.0])
        flagged = orders.filtered("l10n_sk_cash_limit_warning")
        self.assertEqual(flagged.mapped("amount_total"), [6000.0])
