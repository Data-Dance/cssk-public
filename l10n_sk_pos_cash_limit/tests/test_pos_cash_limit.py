# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import timedelta

from odoo import Command, fields
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
        cls.buyer = cls.env["res.partner"].create({"name": "Kupec Opakovaný"})

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

    def test_till_gets_the_limit_and_the_rate(self):
        self.assertEqual(self.main_pos_config._l10n_sk_cash_rate(), 1.0)
        data = self.main_pos_config.l10n_sk_cash_limit_context(False)
        self.assertEqual((data["rate"], data["limit"], data["earlier"]), (1.0, 5000.0, 0.0))

    def test_no_rate_outside_slovakia(self):
        self.main_pos_config.company_id.account_fiscal_country_id = self.env.ref("base.cz")
        self.assertFalse(self.main_pos_config._l10n_sk_cash_rate())

    def test_same_customer_same_day_adds_up(self):
        self.main_pos_config.with_user(self.pos_user).open_ui()
        self.start_pos_tour("l10n_sk_pos_cash_limit_same_customer_tour")
        orders = self.env["pos.order"].search(
            [("session_id", "=", self.main_pos_config.current_session_id.id)],
            order="id",
        )
        self.assertEqual(orders.mapped("partner_id"), self.buyer)
        self.assertEqual(len(orders), 2)
        self.assertFalse(orders[0].l10n_sk_cash_limit_warning)
        self.assertIn("8000", orders[1].l10n_sk_cash_limit_warning.replace(" ", "").replace("\u202f", ""))
        self.assertEqual(
            self.env["pos.order"].l10n_sk_cash_paid_today(self.buyer.id, self.main_pos_config.id),
            8000.0,
        )

    def test_koruna_till_converts_at_yesterdays_rate(self):
        czk = self.env.ref("base.CZK")
        czk.active = True
        config = self.main_pos_config
        # Stored compute: write the currency directly rather than re-plumb
        # the sale journal, which has entries by now.
        config.currency_id = czk
        self.assertFalse(config._l10n_sk_cash_rate(), "no rate known: refuse, do not use 1")
        yesterday = fields.Date.context_today(config) - timedelta(days=1)
        self.env["res.currency.rate"].create({
            "currency_id": czk.id, "company_id": config.company_id.root_id.id,
            "name": yesterday - timedelta(days=3), "rate": 25.0,
        })
        self.assertAlmostEqual(config._l10n_sk_cash_rate(), 0.04)

    def test_refund_is_not_added_to_payments(self):
        order = self._order([(self.cash_method, -3000.0)])
        order.partner_id = self.buyer
        self.assertFalse(order.l10n_sk_cash_limit_warning)
