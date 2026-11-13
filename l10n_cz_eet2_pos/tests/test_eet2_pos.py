# -*- coding: utf-8 -*-
"""POS mapping: sale time = payment time, amounts hook, bounded sync send."""
import base64
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.addons.point_of_sale.tests.common import TestPoSCommon
from odoo.addons.l10n_cz_eet2.lib import eet2_client
from odoo.addons.l10n_cz_eet2.tests.test_eet2_client import _throwaway_p12


def _ok():
    return eet2_client.SendResult(
        eet2_client.Odpoved(pok="b3a09b52-7c87-4014-a496-4c7a53cf9125-ff", test=True),
        b"<ok/>", "x")


@tagged("post_install", "-at_install")
class TestEet2Pos(TestPoSCommon):
    _PATCH = "odoo.addons.l10n_cz_eet2.lib.eet2_client.send"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.basic_config
        p12, pw = _throwaway_p12(b"pw")
        cls.cert = cls.env["l10n.cz.eet2.certificate"].sudo().create({
            "name": "pos-test", "company_id": cls.company.id,
            "environment": "playground",
            "p12_file": base64.b64encode(p12), "password": "pw",
        })
        cls.company.sudo().write({
            "l10n_cz_eet2_enabled": True,
            "l10n_cz_eet2_eic_popl": "CZ00000019",
            "l10n_cz_eet2_id_jednotky": 303,
            "l10n_cz_eet2_certificate_id": cls.cert.id,
            "l10n_cz_eet2_response_timeout": 4.0,
        })
        cls.product_a = cls.create_product("EET product", cls.categ_basic, 100.0, tax_ids=False)

    def test_order_registered_at_payment_time_with_company_timeout(self):
        self.open_new_session()
        with patch(self._PATCH, return_value=_ok()) as send:
            orders = self._create_orders([{
                "pos_order_lines_ui_args": [(self.product_a, 2)],
                "payments": [(self.cash_pm1, 200.0)],
                "uid": "00100-010-0001",
            }])
        order = list(orders.values())[0]
        tx = order.l10n_cz_eet2_transaction_id
        self.assertTrue(tx, "a cash sale is registered on sync")
        self.assertEqual(tx.state, "accepted")
        self.assertEqual(order.l10n_cz_eet2_pok, tx.pok)
        self.assertEqual(tx.dat_trzby, max(order.payment_ids.mapped("payment_date")))
        self.assertEqual(send.call_args.kwargs["timeout"], 4.0, "§ 19 limit at the till")
        if order.currency_id != self.env.ref("base.CZK"):
            self.assertEqual(tx.source_currency_id, order.currency_id)
            self.assertAlmostEqual(tx.source_amount, 200.0, places=2)
        else:
            self.assertAlmostEqual(tx.celk_trzba, 200.0, places=2)
        self.assertFalse(tx.urceno_cerp_zuct)
        self.assertFalse(tx.cerp_zuct)

    def test_sale_datetime_falls_back_to_date_order(self):
        self.open_new_session()
        order = self.env["pos.order"].create({
            "session_id": self.pos_session.id,
            "company_id": self.company.id,
            "amount_tax": 0, "amount_total": 0, "amount_paid": 0, "amount_return": 0,
            "date_order": fields.Datetime.to_datetime("2027-02-01 10:00:00"),
        })
        self.assertEqual(order._l10n_cz_eet2_sale_datetime(),
                        fields.Datetime.to_datetime("2027-02-01 10:00:00"))

    def test_pos_config_unit_id_shape(self):
        with self.assertRaises(ValidationError):
            self.config.l10n_cz_eet2_id_jednotky = 125
        self.config.l10n_cz_eet2_id_jednotky = 121

    def test_only_contact_payment_lines_are_registered(self):
        """§ 5–6 ZoET: a method flagged remote does not count; the cash half does."""
        self.bank_pm1.l10n_cz_eet2_contact_payment = False
        self.open_new_session()
        with patch(self._PATCH, return_value=_ok()):
            orders = self._create_orders([{
                "pos_order_lines_ui_args": [(self.product_a, 2)],
                "payments": [(self.cash_pm1, 150.0), (self.bank_pm1, 50.0)],
                "uid": "00100-010-0002",
            }])
        order = list(orders.values())[0]
        tx = order.l10n_cz_eet2_transaction_id
        self.assertTrue(tx)
        amounts = order._l10n_cz_eet2_amounts()
        self.assertAlmostEqual(amounts["celk_trzba"], 150.0, places=2)
        self.assertAlmostEqual(tx.source_amount or tx.celk_trzba, 150.0, places=2)

    def test_no_contact_money_registers_nothing(self):
        self.bank_pm1.l10n_cz_eet2_contact_payment = False
        self.open_new_session()
        with patch(self._PATCH, return_value=_ok()) as send:
            orders = self._create_orders([{
                "pos_order_lines_ui_args": [(self.product_a, 1)],
                "payments": [(self.bank_pm1, 100.0)],
                "uid": "00100-010-0003",
            }])
        order = list(orders.values())[0]
        self.assertFalse(order.l10n_cz_eet2_transaction_id)
        self.assertFalse(send.called)

    def test_refund_registers_the_negative_contact_sum(self):
        self.open_new_session()
        order = self.env["pos.order"].create({
            "session_id": self.pos_session.id,
            "company_id": self.company.id,
            "amount_tax": 0, "amount_total": -100.0, "amount_paid": -100.0,
            "amount_return": 0,
        })
        self.env["pos.payment"].create({
            "pos_order_id": order.id, "payment_method_id": self.cash_pm1.id,
            "amount": -100.0, "payment_date": fields.Datetime.now()})
        self.assertTrue(order._l10n_cz_eet2_in_scope())
        self.assertAlmostEqual(order._l10n_cz_eet2_amounts()["celk_trzba"], -100.0, places=2)

    def test_change_given_back_is_not_registered(self):
        """500 tendered on a 450 sale: the -50 change line nets out."""
        self.open_new_session()
        order = self.env["pos.order"].create({
            "session_id": self.pos_session.id,
            "company_id": self.company.id,
            "amount_tax": 0, "amount_total": 450.0, "amount_paid": 450.0,
            "amount_return": 50.0,
        })
        for amount in (500.0, -50.0):
            self.env["pos.payment"].create({
                "pos_order_id": order.id, "payment_method_id": self.cash_pm1.id,
                "amount": amount, "payment_date": fields.Datetime.now()})
        self.assertAlmostEqual(order._l10n_cz_eet2_amounts()["celk_trzba"], 450.0, places=2)

    def test_session_closing_payment_is_never_registered(self):
        """The orders were registered at the till; the session total is not a sale."""
        self.open_new_session()
        journal = self.company_data["default_journal_cash"]
        journal.l10n_cz_eet2_contact = True
        vals = {"payment_type": "inbound", "partner_type": "customer",
                "partner_id": self.partner_a.id, "journal_id": journal.id,
                "amount": 1234.0}
        plain = self.env["account.payment"].create(vals)
        closing = self.env["account.payment"].create(
            dict(vals, pos_session_id=self.pos_session.id))
        self.assertTrue(plain.l10n_cz_eet2_needed)
        self.assertFalse(closing.l10n_cz_eet2_needed)
        closing.action_post()
        self.assertFalse(closing.l10n_cz_eet2_transaction_id)
        self.assertFalse(closing.l10n_cz_eet2_transaction_ids)

    def test_payment_method_flag_reaches_the_frontend(self):
        self.open_new_session()
        params = self.pos_session._loader_params_pos_payment_method()
        self.assertIn("l10n_cz_eet2_contact_payment", params["search_params"]["fields"])
        loaded = self.pos_session._get_pos_ui_pos_payment_method(params)
        self.assertTrue(all("l10n_cz_eet2_contact_payment" in pm for pm in loaded))
        config = self.pos_session._get_pos_ui_pos_config(
            self.pos_session._loader_params_pos_config())
        self.assertTrue(config["l10n_cz_eet2_enabled"])

    def test_reloaded_order_carries_the_pok(self):
        """Ticket screen / reprint: the order exported back to the till has
        the EET result the receipt prints."""
        self.open_new_session()
        with patch(self._PATCH, return_value=_ok()):
            orders = self._create_orders([{
                "pos_order_lines_ui_args": [(self.product_a, 1)],
                "payments": [(self.cash_pm1, 100.0)],
                "uid": "00100-010-0006",
            }])
        order = list(orders.values())[0]
        exported = order.export_for_ui()[0]
        self.assertEqual(exported["l10n_cz_eet2_pok"], order.l10n_cz_eet2_pok)
        self.assertEqual(exported["l10n_cz_eet2_state"], "accepted")
        self.assertTrue(exported["l10n_cz_eet2_is_test"])

    def test_draft_order_is_not_registered(self):
        """An order synced as a draft (restaurant table, not yet paid) is no sale."""
        self.open_new_session()
        data = self.create_ui_order_data(
            [(self.product_a, 1)], payments=[(self.cash_pm1, 100.0)], uid="00100-010-0007")
        with patch(self._PATCH, return_value=_ok()) as send:
            res = self.env["pos.order"].create_from_ui([data], draft=True)
        order = self.env["pos.order"].browse(res[0]["id"])
        self.assertFalse(order.l10n_cz_eet2_transaction_id)
        self.assertFalse(send.called)

    def test_one_live_sale_per_order(self):
        """A second live sale message for the same order is refused by the
        database, and a resend reuses the order's message."""
        from psycopg2 import IntegrityError
        from odoo.tools import mute_logger
        self.open_new_session()
        with patch(self._PATCH, side_effect=ConnectionError("down")):
            orders = self._create_orders([{
                "pos_order_lines_ui_args": [(self.product_a, 1)],
                "payments": [(self.cash_pm1, 100.0)],
                "uid": "00100-010-0004",
            }])
        order = list(orders.values())[0]
        tx = order.l10n_cz_eet2_transaction_id
        self.assertEqual(tx.pos_order_id, order)
        self.assertEqual(tx.state, "retry")
        Tx = self.env["l10n.cz.eet2.transaction"]
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.env.cr.savepoint():
            Tx.create_from_values(order.company_id, **order._l10n_cz_eet2_prepare_values())
            Tx.flush_model()
        with patch(self._PATCH, return_value=_ok()):
            order.l10n_cz_eet2_resend()
        self.assertEqual(order.l10n_cz_eet2_transaction_id, tx, "the message is reused")
        self.assertEqual(tx.state, "accepted")
        self.assertEqual(Tx.search_count([("pos_order_id", "=", order.id)]), 1)
        # a storno of a POS message keeps the order link
        storno = tx._create_storno()
        self.assertEqual(storno.pos_order_id, order)
        self.assertEqual(storno.storno_of_id, tx)

    def test_racing_registration_adopts_the_existing_message(self):
        """A second registration of an order that already has a live message
        links the existing one instead of failing."""
        self.open_new_session()
        with patch(self._PATCH, return_value=_ok()):
            orders = self._create_orders([{
                "pos_order_lines_ui_args": [(self.product_a, 1)],
                "payments": [(self.cash_pm1, 100.0)],
                "uid": "00100-010-0005",
            }])
        order = list(orders.values())[0]
        tx = order.l10n_cz_eet2_transaction_id
        # pretend this worker never saw the link, as a parallel sync would not
        order.invalidate_recordset(["l10n_cz_eet2_transaction_id"])
        self.env.cr.execute("UPDATE pos_order SET l10n_cz_eet2_transaction_id = NULL WHERE id = %s", (order.id,))
        order.invalidate_recordset()
        self.assertFalse(order.l10n_cz_eet2_transaction_id)
        with patch(self._PATCH, return_value=_ok()) as send:
            order._l10n_cz_eet2_try_register()
        self.assertEqual(order.l10n_cz_eet2_transaction_id, tx, "the live message is adopted")
        self.assertFalse(send.called, "nothing is sent twice")
