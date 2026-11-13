# -*- coding: utf-8 -*-
"""Gift card / eWallet mapping to urceno_cerp_zuct / cerp_zuct (FS Q&A 585)."""
import base64

from odoo import Command, fields
from odoo.tests import tagged
from odoo.addons.point_of_sale.tests.common import TestPoSCommon
from odoo.addons.l10n_cz_eet2.tests.test_eet2_client import _throwaway_p12


@tagged("post_install", "-at_install")
class TestEet2PosLoyalty(TestPoSCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.basic_config
        p12, pw = _throwaway_p12(b"pw")
        cls.cert = cls.env["l10n.cz.eet2.certificate"].sudo().create({
            "name": "loyalty-test", "company_id": cls.company.id,
            "environment": "playground",
            "p12_file": base64.b64encode(p12), "password": "pw",
        })
        cls.company.sudo().write({
            "l10n_cz_eet2_enabled": True,
            "l10n_cz_eet2_eic_popl": "CZ00000019",
            "l10n_cz_eet2_id_jednotky": 303,
            "l10n_cz_eet2_certificate_id": cls.cert.id,
        })
        cls.drink = cls.create_product("Energy drink", cls.categ_basic, 50.0, tax_ids=False)
        cls.topup_product = cls.create_product("Wallet top-up", cls.categ_basic, 1000.0, tax_ids=False)
        Program = cls.env["loyalty.program"].with_context(default_program_type="ewallet")
        cls.program = Program.create({
            "name": "Club wallet",
            "program_type": "ewallet",
            "pos_ok": True,
            "company_id": cls.company.id,
            "currency_id": cls.config.currency_id.id,
            "rule_ids": [Command.clear(), Command.create({
                "reward_point_amount": 1, "reward_point_mode": "money",
                "product_ids": [Command.set(cls.topup_product.ids)]})],
            "reward_ids": [Command.clear(), Command.create({
                "reward_type": "discount", "discount_mode": "per_point",
                "discount": 1, "discount_applicability": "order",
                "required_points": 1, "description": "eWallet"})],
        })
        cls.reward = cls.program.reward_ids[:1]

    def _order(self, lines, payments_total):
        self.open_new_session()
        cmds = []
        total = 0.0
        for product, qty, price, reward in lines:
            sub = qty * price
            total += sub
            cmds.append(Command.create({
                "product_id": product.id, "qty": qty, "price_unit": price,
                "price_subtotal": sub, "price_subtotal_incl": sub,
                "is_reward_line": bool(reward),
                "reward_id": reward.id if reward else False,
            }))
        order = self.env["pos.order"].create({
            "session_id": self.pos_session.id,
            "company_id": self.company.id,
            "lines": cmds,
            "amount_tax": 0, "amount_total": total, "amount_paid": payments_total,
            "amount_return": 0,
        })
        if payments_total:
            self.env["pos.payment"].create({
                "pos_order_id": order.id, "payment_method_id": self.cash_pm1.id,
                "amount": payments_total, "payment_date": fields.Datetime.now()})
        return order

    def test_topup_plus_cash_item(self):
        """Top-up 1000 + drink 50 paid cash -> celk 1050, urceno 1000 (FS 585)."""
        order = self._order([(self.topup_product, 1, 1000.0, None),
                            (self.drink, 1, 50.0, None)], 1050.0)
        amounts = order._l10n_cz_eet2_amounts()
        self.assertAlmostEqual(amounts["celk_trzba"], 1050.0)
        self.assertAlmostEqual(amounts["urceno_cerp_zuct"], 1000.0)
        self.assertAlmostEqual(amounts["cerp_zuct"], 0.0)
        vals = order._l10n_cz_eet2_prepare_values()
        self.assertAlmostEqual(vals["urceno_cerp_zuct"], 1000.0)
        self.assertFalse(vals["cerp_zuct"])

    def test_redemption_entirely_from_wallet(self):
        """Redemption of 300 -> celk 300, cerp 300, in scope with no payment line."""
        order = self._order([(self.drink, 6, 50.0, None),
                            (self.reward.discount_line_product_id, 1, -300.0, self.reward)], 0.0)
        self.assertAlmostEqual(order.amount_total, 0.0)
        amounts = order._l10n_cz_eet2_amounts()
        self.assertAlmostEqual(amounts["celk_trzba"], 300.0)
        self.assertAlmostEqual(amounts["cerp_zuct"], 300.0)
        self.assertAlmostEqual(amounts["urceno_cerp_zuct"], 0.0)
        self.assertTrue(order._l10n_cz_eet2_in_scope())

    def test_partial_redemption_plus_cash(self):
        """Drawn 100 from the wallet, 200 cash -> celk 300, cerp 100."""
        order = self._order([(self.drink, 6, 50.0, None),
                            (self.reward.discount_line_product_id, 1, -100.0, self.reward)], 200.0)
        amounts = order._l10n_cz_eet2_amounts()
        self.assertAlmostEqual(amounts["celk_trzba"], 300.0)
        self.assertAlmostEqual(amounts["cerp_zuct"], 100.0)

    def test_refund_of_wallet_paid_order_is_negative_storno(self):
        """Item methodology ch. 14 ex. 3: refund paid back to the wallet ->
        celk_trzba -121 / cerp_zuct -121."""
        order = self._order([(self.drink, -1, 121.0, None),
                            (self.reward.discount_line_product_id, -1, -121.0, self.reward)], 0.0)
        amounts = order._l10n_cz_eet2_amounts()
        self.assertAlmostEqual(amounts["celk_trzba"], -121.0)
        self.assertAlmostEqual(amounts["cerp_zuct"], -121.0)
        self.assertTrue(order._l10n_cz_eet2_in_scope())

    def test_topup_detected_after_program_archived(self):
        order = self._order([(self.topup_product, 1, 1000.0, None)], 1000.0)
        self.program.active = False
        self.assertAlmostEqual(order._l10n_cz_eet2_amounts()["urceno_cerp_zuct"], 1000.0)
