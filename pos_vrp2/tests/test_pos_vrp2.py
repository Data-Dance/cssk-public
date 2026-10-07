import base64
import json
from contextlib import contextmanager
from unittest.mock import patch

import psycopg2

from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, tagged

from odoo.addons.l10n_sk_vrp2_base.models.vrp2_client import _compact_json
from odoo.addons.point_of_sale.tests.common import TestPoSCommon

# The register profile of the 2026-10-06 capture (getdashboard, trimmed).
DASHBOARD = {
    "returnValue": 0,
    "cashRegister": {
        "dkp": "99920201234560002",
        "login": "1234567890",
        "version": 1662177617338,
        "organization": {"name": "Testovacia s.r.o.", "vatPayer": True},
    },
}

# GET /v1/vat/vatlist of the same capture.
VATLIST = [
    {"id": 2000, "vatRate": 0},
    {"id": 2050, "vatRate": 0.1},
    {"id": 2100, "vatRate": 0.2},
    {"id": 500, "vatRate": 0.05},
    {"id": 501, "vatRate": 0.19},
    {"id": 502, "vatRate": 0.23},
]

SALE_UUID = "V-0000000000000000000000000000A019"
CODE_A = "800000000000000000001"
CODE_B = "800000000000000000002"
# VRP2's catalogue name, trailing space and all: a refund must repeat it.
NAME_B = "Káva B 250g "


def _data_b64(items):
    return base64.b64encode(
        json.dumps({"returnValue": 0, "dto": {"items": items}}).encode()
    ).decode()


# POST /v5/receipt/create/valid — the sale, byte for byte as captured.
SALE_REQUEST = {
    "vatPayer": True,
    "items": [
        {"priceWithVat": 8.99, "discount": 0, "quantity": 1,
         "type": "POSITIVE", "serviceCode": CODE_A, "vatRate": 0.19},
        {"priceWithVat": 9.49, "discount": 0, "quantity": 1,
         "type": "POSITIVE", "serviceCode": CODE_B, "vatRate": 0.19},
    ],
    "payments": [{"type": "CASH", "sum": 18.5, "currency": "EUR",
                  "exchangeRate": None, "amount": 18.5}],
    "priceWithVat": 18.5,
    "version": 1662177617338,
    "useRounding": True,
}
SALE_RESPONSE = {
    "returnValue": 0,
    "id": 1019,
    "createDate": 1791285713461,
    "receiptId": SALE_UUID,
    "receiptNumber": 19,
    "okp": "00000000-00000000-00000000-00000000-00000019",
    "pdfBase64": base64.b64encode(b"%PDF-1.4 sale").decode(),
    "dataBase64": _data_b64([
        {"unitPriceWithVat": 8.99, "quantity": 1, "type": "POSITIVE",
         "service": {"name": "Káva A 250g"}, "itemName": None},
        {"unitPriceWithVat": 9.49, "quantity": 1, "type": "POSITIVE",
         "service": {"name": NAME_B}, "itemName": None},
    ]),
}

# The storno of that sale, byte for byte as captured: REFUND items, no
# rounding, EXPENSE for the exact item total (−18.48 against 18.50 paid).
STORNO_REQUEST = {
    "vatPayer": True,
    "items": [
        {"priceWithVat": -8.99, "discount": 0, "quantity": 1,
         "type": "REFUND", "vatRate": 0.19,
         "referenceReceiptId": SALE_UUID,
         "receiptItemName": "Káva A 250g"},
        {"priceWithVat": -9.49, "discount": 0, "quantity": 1,
         "type": "REFUND", "vatRate": 0.19,
         "referenceReceiptId": SALE_UUID,
         "receiptItemName": NAME_B},
    ],
    "payments": [{"type": "EXPENSE", "sum": -18.48, "currency": "EUR",
                  "exchangeRate": None, "amount": -18.48}],
    "priceWithVat": -18.48,
    "version": 1662177617338,
    "useRounding": False,
}
STORNO_RESPONSE = {
    "returnValue": 0,
    "id": 1020,
    "createDate": 1791285827790,
    "receiptId": "V-0000000000000000000000000000A020",
    "receiptNumber": 20,
    "okp": "00000000-00000000-00000000-00000000-00000020",
}


@tagged("post_install", "-at_install")
class TestPosVrp2(TestPoSCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.basic_config
        cls.rounding_5c = cls.env["account.cash.rounding"].create({
            "name": "0.05 nearest",
            "rounding": 0.05,
            "rounding_method": "HALF-UP",
            "strategy": "add_invoice_line",
            "profit_account_id": cls.company_data["default_account_revenue"].id,
            "loss_account_id": cls.company_data["default_account_expense"].id,
        })
        cls.config.write({
            "vrp2_enabled": True,
            "vrp2_auto_fiscalize": True,
            "vrp2_login": "1234567890",
            "vrp2_round_5c": True,
            "cash_rounding": True,
            "rounding_method": cls.rounding_5c.id,
            "only_round_cash_method": True,
        })
        cls.company.vrp2_vatlist_json = json.dumps(VATLIST)
        cls.vat19 = cls.env["account.tax"].create({
            "name": "VAT 19 % incl.",
            "amount": 19,
            "amount_type": "percent",
            "type_tax_use": "sale",
            "price_include_override": "tax_included",
            "company_id": cls.company.id,
        })
        cls.coffee_a = cls.create_product(
            "Káva A 250g", cls.categ_basic, 8.99,
            tax_ids=cls.vat19.ids,
        )
        cls.coffee_b = cls.create_product(
            "Káva B 250g", cls.categ_basic, 9.49,
            tax_ids=cls.vat19.ids,
        )
        cls.coffee_a.product_tmpl_id.vrp2_code = CODE_A
        cls.coffee_b.product_tmpl_id.vrp2_code = CODE_B
        # A deposit bottle: outside VAT, so no tax and vatRate 0.
        cls.bottle = cls.create_product("Záloha PET", cls.categ_basic, 0.15)
        cls.bottle.product_tmpl_id.write({
            "vrp2_code": "800000000000000000015",
            "vrp2_returnable_packaging": True,
        })

    def setUp(self):
        super().setUp()
        self.open_new_session()
        self.calls = []

    # ---- helpers ---------------------------------------------------------

    @contextmanager
    def _vrp2(self, valid=None, invoice=None):
        """Mock the network edge of vrp2.client, recording every body."""
        Client = type(self.env["vrp2.client"])

        def recorder(kind, response):
            def call(holder, body):
                self.calls.append((kind, body))
                if isinstance(response, Exception):
                    raise response
                return dict(response or {})
            return call

        with patch.object(Client, "_ensure_session", return_value="TOK"), \
             patch.object(Client, "_get_dashboard", return_value=DASHBOARD), \
             patch.object(Client, "_create_receipt_valid",
                          side_effect=recorder("valid", valid)), \
             patch.object(Client, "_create_invoice",
                          side_effect=recorder("invoice", invoice)):
            yield

    def _sync(self, lines, payments=None, commit=True, **kwargs):
        """Sync an order as the till does; ``commit`` then runs what the
        commit of that request would trigger (the post-commit fiscalization).
        """
        data = self.create_ui_order_data(lines, payments=payments, **kwargs)
        result = self.env["pos.order"].sync_from_ui([data])
        order = self.env["pos.order"].browse(
            [o["id"] for o in result["pos.order"]]
        ).filtered(lambda o: o.uuid == data["uuid"])
        if commit:
            with self.enter_registry_test_mode():
                self.env.cr.postcommit.run()
            order.invalidate_recordset()
        return order

    def _expected(self, body):
        """The captured body, in this test company's currency."""
        body = json.loads(json.dumps(body))
        for payment in body["payments"]:
            payment["currency"] = self.currency.name
        return body

    def _sale(self):
        # Odoo rounds the cash due exactly as VRP2 does, so the till takes
        # the same 18.50 the register records.
        with self._vrp2(valid=SALE_RESPONSE):
            return self._sync(
                [(self.coffee_a, 1), (self.coffee_b, 1)],
                payments=[(self.cash_pm1, 18.50)],
            )

    # ---- the capture, replayed -------------------------------------------

    def test_sale_matches_capture(self):
        """A synced paid order is fiscalized with exactly the captured body."""
        order = self._sale()
        self.assertEqual(order.state, "paid")
        self.assertEqual(len(self.calls), 1)
        kind, body = self.calls[0]
        self.assertEqual(kind, "valid")
        # Compare the BYTES that are sent (and checksummed), not just values:
        # 1 and 1.0 are equal in Python but not on the wire.
        self.assertEqual(
            _compact_json(body), _compact_json(self._expected(SALE_REQUEST))
        )

        self.assertEqual(order.vrp2_state, "fiscalized")
        # Odoo's drawer and VRP2's receipt agree to the cent.
        self.assertEqual(order.amount_paid, body["payments"][0]["amount"])
        self.assertEqual(order.vrp2_receipt_number, "19")
        self.assertEqual(order.vrp2_receipt_uuid, SALE_UUID)
        self.assertEqual(order.vrp2_server_id, "1019")
        self.assertTrue(order.vrp2_pdf)
        self.assertEqual(
            order.lines.sorted("id").mapped("vrp2_item_name"),
            ["Káva A 250g", NAME_B],
        )

    def test_refund_matches_storno_capture(self):
        """Refunding the whole order is VRP2's storno: REFUND items against
        the original receipt, the names VRP2 printed, no rounding."""
        sale = self._sale()
        line_a, line_b = sale.lines.sorted("id")
        self.calls.clear()
        with self._vrp2(valid=STORNO_RESPONSE):
            refund = self._sync(
                [
                    {"product": self.coffee_a, "quantity": -1,
                     "refunded_orderline_id": line_a.id},
                    {"product": self.coffee_b, "quantity": -1,
                     "refunded_orderline_id": line_b.id},
                ],
                payments=[(self.cash_pm1, -18.48)],
            )
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(
            _compact_json(self.calls[0][1]),
            _compact_json(self._expected(STORNO_REQUEST)),
        )
        self.assertEqual(refund.vrp2_state, "fiscalized")
        self.assertEqual(refund.vrp2_receipt_number, "20")

    def test_nothing_reaches_vrp2_before_the_commit(self):
        """A sync whose transaction never commits issues no receipt — so a
        rolled-back batch cannot leave a receipt behind to be re-issued."""
        with self._vrp2(valid=SALE_RESPONSE):
            order = self._sync([(self.coffee_a, 1)],
                               payments=[(self.cash_pm1, 8.99)], commit=False)
            self.assertFalse(self.calls)
            self.assertEqual(order.vrp2_state, "not_fiscalized")
            with self.enter_registry_test_mode():
                self.env.cr.postcommit.run()
        order.invalidate_recordset()
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(order.vrp2_state, "fiscalized")

    def test_overpaid_by_card_with_cash_is_refused(self):
        with self._vrp2(valid={}):
            order = self._sync([(self.coffee_a, 1)],
                               payments=[(self.bank_pm1, 9.50),
                                         (self.cash_pm1, -0.51)])
        self.assertEqual(order.vrp2_state, "error")
        self.assertFalse(self.calls)

    # ---- payments and rounding ------------------------------------------

    def test_only_the_cash_share_is_rounded(self):
        with self._vrp2(valid=SALE_RESPONSE):
            self._sync(
                [(self.coffee_a, 1), (self.coffee_b, 1)],
                payments=[(self.bank_pm1, 10.0), (self.cash_pm1, 8.50)],
            )
        body = self.calls[0][1]
        self.assertEqual(body["priceWithVat"], 18.5)
        self.assertEqual(
            [(p["type"], p["amount"]) for p in body["payments"]],
            [("CARD", 10.0), ("CASH", 8.5)],
        )

    def test_card_only_is_not_rounded(self):
        with self._vrp2(valid=SALE_RESPONSE):
            self._sync(
                [(self.coffee_a, 1), (self.coffee_b, 1)],
                payments=[(self.bank_pm1, 18.48)],
            )
        body = self.calls[0][1]
        self.assertEqual(body["priceWithVat"], 18.48)
        self.assertEqual(
            [(p["type"], p["amount"]) for p in body["payments"]],
            [("CARD", 18.48)],
        )

    def test_rounding_off_on_the_till(self):
        self.config.write({"vrp2_round_5c": False, "cash_rounding": False})
        with self._vrp2(valid=SALE_RESPONSE):
            self._sync([(self.coffee_a, 1), (self.coffee_b, 1)],
                       payments=[(self.cash_pm1, 18.48)])
        body = self.calls[0][1]
        self.assertFalse(body["useRounding"])
        self.assertEqual(body["priceWithVat"], 18.48)
        self.assertEqual(body["payments"][0]["amount"], 18.48)

    def test_quantity_and_discount_are_per_unit(self):
        """priceWithVat is the unit price and discount an absolute amount
        per unit (web app parseToAPI), never line totals."""
        with self._vrp2(valid={}):
            self._sync([(self.coffee_a, 3, 10.0)],
                       payments=[(self.cash_pm1, 24.25)])
        item = self.calls[0][1]["items"][0]
        self.assertEqual(item["priceWithVat"], 8.99)
        self.assertEqual(item["quantity"], 3)
        self.assertEqual(item["discount"], 0.899)
        # VRP2's own line total: zaokruhli2((8.99 − 0.899) × 3) = 24.27,
        # cash-rounded to 24.25.
        self.assertEqual(self.calls[0][1]["priceWithVat"], 24.25)

    # ---- Odoo cash rounding must match the register's ------------------

    def test_vrp2_rounding_requires_matching_odoo_rounding(self):
        with self.assertRaisesRegex(ValidationError, "0.05"):
            self.config.cash_rounding = False
        with self.assertRaisesRegex(ValidationError, "0.05"):
            self.config.rounding_method = self.env["account.cash.rounding"].create({
                "name": "0.10", "rounding": 0.10, "rounding_method": "HALF-UP",
                "strategy": "add_invoice_line",
                "profit_account_id": self.rounding_5c.profit_account_id.id,
                "loss_account_id": self.rounding_5c.loss_account_id.id,
            })
        with self.assertRaisesRegex(ValidationError, "0.05"):
            self.config.only_round_cash_method = False

    def test_no_vrp2_rounding_forbids_odoo_rounding(self):
        with self.assertRaisesRegex(ValidationError, "must not round"):
            self.config.vrp2_round_5c = False

    def test_enabling_vrp2_sets_odoo_rounding(self):
        config = self.env["pos.config"].create({"name": "Second till"})
        with Form(config) as form:
            form.vrp2_enabled = True
        self.assertTrue(config.cash_rounding)
        self.assertTrue(config.only_round_cash_method)
        self.assertEqual(config.rounding_method.rounding, 0.05)
        self.assertEqual(config.rounding_method.rounding_method, "HALF-UP")

    # ---- returned packaging ("vrátené obaly") ------------------------------

    def test_returned_packaging_is_a_negative_item(self):
        """Bottles taken back with a sale: NEGATIVE items, which keep their
        serviceCode (unlike REFUND); a positive total is still rounded."""
        with self._vrp2(valid={}):
            order = self._sync([(self.coffee_a, 1), (self.bottle, -2)],
                               payments=[(self.cash_pm1, 8.70)])
        body = self.calls[0][1]
        self.assertEqual(body["items"][1], {
            "priceWithVat": -0.15, "discount": 0, "quantity": 2,
            "type": "NEGATIVE", "serviceCode": "800000000000000000015",
            "vatRate": 0,
        })
        self.assertTrue(body["useRounding"])
        self.assertEqual(body["priceWithVat"], 8.7)
        self.assertEqual(body["payments"][0]["amount"], 8.7)
        self.assertEqual(order.vrp2_state, "fiscalized")

    def test_packaging_only_return_pays_out_unrounded(self):
        with self._vrp2(valid={}):
            self._sync([(self.bottle, -2)], payments=[(self.cash_pm1, -0.30)])
        body = self.calls[0][1]
        self.assertFalse(body["useRounding"])
        self.assertEqual(body["priceWithVat"], -0.3)
        self.assertEqual(
            [(p["type"], p["amount"]) for p in body["payments"]],
            [("EXPENSE", -0.3)],
        )

    def test_packaging_outside_the_catalogue_is_an_error(self):
        self.bottle.product_tmpl_id.vrp2_code = False
        with self._vrp2(valid={}):
            order = self._sync([(self.bottle, -1)],
                               payments=[(self.cash_pm1, -0.15)])
        self.assertEqual(order.vrp2_state, "error")
        self.assertIn("Packaging", order.vrp2_error_message)
        self.assertFalse(self.calls)

    # ---- failure handling ------------------------------------------------

    def test_vrp2_failure_never_blocks_the_sale(self):
        with self._vrp2(valid=UserError("VRP2 error: boom")):
            order = self._sync([(self.coffee_a, 1)],
                               payments=[(self.cash_pm1, 8.99)])
        self.assertEqual(order.state, "paid")
        self.assertEqual(order.vrp2_state, "error")
        self.assertIn("boom", order.vrp2_error_message)
        # The savepoint discarded the failed attempt's request.
        self.assertFalse(order.vrp2_request_json)

        # Retrying from the form succeeds and clears the error.
        with self._vrp2(valid=SALE_RESPONSE):
            order.action_vrp2_fiscalize()
        self.assertEqual(order.vrp2_state, "fiscalized")
        self.assertFalse(order.vrp2_error_message)

    def test_concurrent_fiscalization_is_not_an_error(self):
        """Another transaction holding or having just fiscalized the order
        must never be recorded as a VRP2 error over its receipt."""
        Order = type(self.env["pos.order"])
        with self._vrp2(valid=SALE_RESPONSE):
            order = self._sync([(self.coffee_a, 1)],
                               payments=[(self.cash_pm1, 9.00)], commit=False)
        for error in (psycopg2.errors.LockNotAvailable,
                      psycopg2.errors.SerializationFailure):
            with patch.object(Order, "_vrp2_fiscalize", side_effect=error()):
                # Background paths skip ...
                order._vrp2_fiscalize_or_record_error()
                self.assertEqual(order.vrp2_state, "not_fiscalized")
                self.assertFalse(order.vrp2_error_message)
                # ... the till's call re-raises, so Odoo replays the request
                # on a fresh snapshot and the cashier sees the real result.
                with self.assertRaises(error):
                    order.vrp2_receipt_for_ui()

    def test_fiscalized_order_is_never_refiscalized(self):
        order = self._sale()
        with patch.object(type(order), "_vrp2_fiscalize",
                          side_effect=AssertionError("must not be called")):
            order._vrp2_fiscalize_or_record_error()
            info = order.vrp2_receipt_for_ui()
        self.assertEqual(order.vrp2_state, "fiscalized")
        self.assertEqual(info["state"], "fiscalized")
        self.assertEqual(info["receipt_uuid"], SALE_UUID)
        self.assertEqual(info["dkp"], "99920201234560002")

    def test_pos_does_not_load_the_audit_payloads(self):
        order = self._sale()
        rows = self.env["pos.order"]._load_pos_data_read(order, self.config)
        self.assertEqual(rows[0]["vrp2_receipt_uuid"], SALE_UUID)
        for key in ("vrp2_pdf", "vrp2_qr_content", "vrp2_request_json",
                    "vrp2_response_json"):
            self.assertNotIn(key, rows[0])

    def test_product_outside_the_catalogue_is_an_error(self):
        self.coffee_b.product_tmpl_id.vrp2_code = False
        with self._vrp2(valid=SALE_RESPONSE):
            order = self._sync([(self.coffee_b, 1)],
                               payments=[(self.cash_pm1, 9.49)])
        self.assertEqual(order.vrp2_state, "error")
        self.assertIn("service code", order.vrp2_error_message)
        self.assertFalse(self.calls, "nothing may reach VRP2")

    def test_unreferenced_return_is_refused(self):
        with self._vrp2(valid={}):
            order = self._sync([(self.coffee_a, -1)],
                               payments=[(self.cash_pm1, -8.99)])
        self.assertEqual(order.vrp2_state, "error")
        self.assertIn("original receipt", order.vrp2_error_message)
        self.assertFalse(self.calls)

    def test_customer_account_payment_is_refused(self):
        self.assertFalse(self.pay_later_pm.vrp2_payment_type)
        self.assertEqual(self.cash_pm1.vrp2_payment_type, "CASH")
        self.assertEqual(self.bank_pm1.vrp2_payment_type, "CARD")
        with self._vrp2(valid={}):
            order = self._sync([(self.coffee_a, 1)],
                               payments=[(self.pay_later_pm, 8.99)],
                               customer=self.customer)
        self.assertEqual(order.vrp2_state, "error")
        self.assertFalse(self.calls)

    def test_auto_fiscalize_off(self):
        self.config.vrp2_auto_fiscalize = False
        with self._vrp2(valid=SALE_RESPONSE):
            order = self._sync([(self.coffee_a, 1)],
                               payments=[(self.cash_pm1, 8.99)])
        self.assertEqual(order.vrp2_state, "not_fiscalized")
        self.assertFalse(self.calls)

    # ---- invoiced orders -------------------------------------------------

    def test_invoiced_order_is_an_invoice_payment(self):
        with self._vrp2(invoice={"receiptId": "V-INV", "receiptNumber": 21}):
            order = self._sync([(self.coffee_a, 1), (self.coffee_b, 1)],
                               payments=[(self.cash_pm1, 18.48)],
                               customer=self.customer, is_invoiced=True)
        self.assertTrue(order.account_move)
        self.assertEqual(len(self.calls), 1)
        kind, body = self.calls[0]
        self.assertEqual(kind, "invoice")
        self.assertNotIn("items", body)
        self.assertEqual(body["invoiceNumber"], order.account_move.name)
        self.assertEqual(body["priceWithVat"], 18.48)
        self.assertEqual(body["payments"][0]["amount"], 18.5)
        self.assertEqual(body["roundingAmount"], 0.02)
        self.assertEqual(order.vrp2_state, "fiscalized")
