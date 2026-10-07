import json
from contextlib import contextmanager
from unittest.mock import patch

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.point_of_sale.tests.test_frontend import TestPointOfSaleHttpCommon

from .test_pos_vrp2 import (
    CODE_B,
    CODE_A,
    DASHBOARD,
    SALE_RESPONSE,
    VATLIST,
)


@tagged("post_install", "-at_install")
class TestPosVrp2Frontend(TestPointOfSaleHttpCommon):
    """The till itself: what the cashier sees and prints after validating."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        company = cls.main_pos_config.company_id
        company.vrp2_vatlist_json = json.dumps(VATLIST)
        rounding = cls.env["account.cash.rounding"].create({
            "name": "0.05 nearest",
            "rounding": 0.05,
            "rounding_method": "HALF-UP",
            "strategy": "add_invoice_line",
            "profit_account_id": company.default_cash_difference_income_account_id.id,
            "loss_account_id": company.default_cash_difference_expense_account_id.id,
        })
        cls.main_pos_config.write({
            "vrp2_enabled": True,
            "vrp2_login": "1234567890",
            "vrp2_round_5c": True,
            "cash_rounding": True,
            "rounding_method": rounding.id,
            "only_round_cash_method": True,
        })
        cls.main_pos_config.sudo().vrp2_dkp = "99920201234560002"
        vat19 = cls.env["account.tax"].create({
            "name": "VAT 19 % incl.",
            "amount": 19,
            "amount_type": "percent",
            "type_tax_use": "sale",
            "price_include_override": "tax_included",
            "company_id": company.id,
        })
        for name, price, code in (
            ("Káva A 250g", 8.99, CODE_A),
            ("Káva B 250g", 9.49, CODE_B),
        ):
            cls.env["product.template"].create({
                "name": name,
                "available_in_pos": True,
                "list_price": price,
                "taxes_id": [Command.set(vat19.ids)],
                "pos_categ_ids": [Command.set(cls.pos_desk_misc_test.ids)],
                "vrp2_code": code,
            })

    @contextmanager
    def _vrp2(self, valid):
        Client = type(self.env["vrp2.client"])

        def create_valid(holder, body):
            if isinstance(valid, Exception):
                raise valid
            return dict(valid)

        with patch.object(Client, "_ensure_session", return_value="TOK"), \
             patch.object(Client, "_get_dashboard", return_value=DASHBOARD), \
             patch.object(Client, "_create_receipt_valid", side_effect=create_valid):
            yield

    def test_receipt_carries_the_vrp2_block(self):
        with self._vrp2(SALE_RESPONSE):
            self.start_pos_tour("pos_vrp2_receipt_tour")
        order = self.env["pos.order"].search(
            [("config_id", "=", self.main_pos_config.id)], limit=1
        )
        self.assertEqual(order.vrp2_state, "fiscalized")
        self.assertEqual(order.vrp2_receipt_uuid, SALE_RESPONSE["receiptId"])

    def test_failed_receipt_is_shown_not_hidden(self):
        with self._vrp2(UserError("VRP2 error: boom")):
            self.start_pos_tour("pos_vrp2_receipt_failed_tour")
        order = self.env["pos.order"].search(
            [("config_id", "=", self.main_pos_config.id)], limit=1
        )
        self.assertEqual(order.state, "paid")
        self.assertEqual(order.vrp2_state, "error")
