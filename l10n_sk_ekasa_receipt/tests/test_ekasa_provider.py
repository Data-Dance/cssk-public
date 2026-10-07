# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from unittest.mock import patch

from odoo import fields
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import QR_OFFLINE_RESTAURANT, QR_ONLINE_FUEL, load_fixture


@tagged("post_install", "-at_install")
class TestEkasaProvider(AccountTestInvoicingCommon):
    """The provider end to end, with the network call replaced by a fixture."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.write({
            "l10n_sk_ekasa_enabled": True,
            "l10n_sk_ekasa_ip_notified": True,
            "l10n_sk_ekasa_ip_address": "192.0.2.10",
            "l10n_sk_ekasa_ip_notified_on": "2026-10-01",
            "cssk_receipt_expense_account_id":
                cls.company_data["default_account_expense"].id,
        })
        for rate in (23.0, 19.0, 5.0):
            cls.env["account.tax"].create({
                "name": "DPH %g%% (test)" % rate,
                "amount_type": "percent",
                "amount": rate,
                "type_tax_use": "purchase",
                "company_id": cls.company.id,
            })
        cls.provider = cls.env.ref("l10n_sk_ekasa_receipt.provider_sk_ekasa")
        # The provider class, not our instance: patching the instance leaves
        # the registry class untouched and the override never runs.
        cls.provider_cls = type(cls.env["cssk.receipt.provider.sk_ekasa"])

    def _receipt(self, qr):
        return self.env["cssk.receipt"].create({
            "company_id": self.company.id,
            "currency_id": self.company.currency_id.id,
            "qr_raw": qr,
        })

    def _answer(self, fixture=None, outcome="found", message=None):
        """Stand in for ``_fetch``, returning (payload, call_vals)."""
        payload = load_fixture(fixture) if fixture else None
        call_vals = {"outcome": outcome, "http_status": 200, "return_value": 0}
        if message:
            call_vals["message"] = message

        def _fake_fetch(self_model, company, request):
            return payload, dict(call_vals)
        return _fake_fetch

    # ------------------------------------------------------------------
    # provider selection
    # ------------------------------------------------------------------
    def test_provider_claims_only_an_ekasa_qr(self):
        impl = self.env["cssk.receipt.provider.sk_ekasa"]
        self.assertTrue(impl._can_capture(self._receipt(QR_ONLINE_FUEL)))
        self.assertTrue(impl._can_capture(self._receipt(QR_OFFLINE_RESTAURANT)))
        self.assertFalse(impl._can_capture(self._receipt("a photograph")))
        self.assertFalse(impl._can_capture(self._receipt(False)))

    def test_provider_is_picked_automatically(self):
        receipt = self._receipt(QR_ONLINE_FUEL)
        self.assertIn(self.provider, receipt._candidate_providers())

    # ------------------------------------------------------------------
    # the § 18 ods. 11 gate
    # ------------------------------------------------------------------
    def test_lookup_refused_until_the_ip_notification_is_declared(self):
        self.company.l10n_sk_ekasa_ip_notified = False
        receipt = self._receipt(QR_ONLINE_FUEL)
        receipt.action_capture()
        self.assertEqual(receipt.state, "error")
        self.assertIn("§ 18 ods. 11", receipt.review_reason)

    def test_lookup_refused_when_switched_off(self):
        self.company.l10n_sk_ekasa_enabled = False
        receipt = self._receipt(QR_ONLINE_FUEL)
        receipt.action_capture()
        self.assertEqual(receipt.state, "error")
        self.assertIn("switched off", receipt.review_reason)

    # ------------------------------------------------------------------
    # the hourly budget
    # ------------------------------------------------------------------
    def test_budget_is_counted_per_clock_hour(self):
        Call = self.env["sk.ekasa.call"]
        self.company.l10n_sk_ekasa_hourly_budget = 2
        for index in range(2):
            Call.create({
                "company_id": self.company.id,
                "request_key": "O-%032X" % index,
                "outcome": "found",
            })
        self.assertEqual(Call._used_this_hour(self.company), 2)
        with self.assertRaisesRegex(UserError, "hourly eKasa lookup budget"):
            Call._check_budget(self.company)

    def test_zero_budget_blocks_rather_than_meaning_the_default(self):
        """Zero must not read as "unset, use 60"."""
        self.company.l10n_sk_ekasa_hourly_budget = 0
        receipt = self._receipt(QR_ONLINE_FUEL)
        receipt.action_capture()
        self.assertEqual(receipt.state, "error")
        self.assertIn("zero", receipt.review_reason)

    def test_spent_budget_refuses_the_capture_rather_than_the_address(self):
        Call = self.env["sk.ekasa.call"]
        self.company.l10n_sk_ekasa_hourly_budget = 1
        Call.create({"company_id": self.company.id,
                     "request_key": "O-%032X" % 1, "outcome": "found"})
        receipt = self._receipt(QR_ONLINE_FUEL)
        receipt.action_capture()
        self.assertEqual(receipt.state, "error")
        self.assertIn("budget", receipt.review_reason)
        # Nothing was sent: the refusal happens before the network.
        self.assertEqual(
            Call.search_count([("receipt_id", "=", receipt.id)]), 0)

    def test_post_init_hook_gives_existing_companies_a_budget(self):
        """A NULL column reads as 0, which would block every existing company."""
        from odoo.addons.l10n_sk_ekasa_receipt.hooks import (
            DEFAULT_HOURLY_BUDGET, post_init_hook,
        )
        self.company.l10n_sk_ekasa_hourly_budget = 0
        post_init_hook(self.env)
        self.assertEqual(self.company.l10n_sk_ekasa_hourly_budget,
                         DEFAULT_HOURLY_BUDGET)

    # ------------------------------------------------------------------
    # a successful capture
    # ------------------------------------------------------------------
    def test_fuel_receipt_captures_and_reconciles(self):
        receipt = self._receipt(QR_ONLINE_FUEL)
        with patch.object(self.provider_cls, "_fetch",
                          self._answer("receipt_online_fuel.json")):
            receipt.action_capture()
        self.assertEqual(receipt.state, "captured", receipt.review_reason)
        self.assertEqual(receipt.receipt_uid, QR_ONLINE_FUEL)
        self.assertEqual(receipt.amount_total, 57.85)
        self.assertEqual(receipt.amount_untaxed, 47.03)
        self.assertEqual(receipt.amount_tax, 10.82)
        self.assertEqual(receipt.seller_vat, "SK7199000006")
        self.assertEqual(receipt.seller_tax_id, "2077000002")
        self.assertEqual(len(receipt.line_ids), 1)
        self.assertEqual(receipt.line_ids.quantity, 31.17)
        self.assertTrue(receipt.payload_raw)
        self.assertEqual(len(receipt.l10n_sk_ekasa_call_ids), 1)
        self.assertEqual(receipt.l10n_sk_ekasa_call_ids.outcome, "found")
        self.assertEqual(receipt.l10n_sk_ekasa_call_count, 1)

    def test_restaurant_receipt_captures_three_rates(self):
        receipt = self._receipt(QR_OFFLINE_RESTAURANT)
        with patch.object(self.provider_cls, "_fetch",
                          self._answer("receipt_offline_restaurant.json")):
            receipt.action_capture()
        self.assertEqual(receipt.state, "captured", receipt.review_reason)
        self.assertEqual(len(receipt.line_ids), 12)
        self.assertEqual(len(receipt.tax_summary_ids), 3)
        self.assertEqual(
            sorted(receipt.tax_summary_ids.mapped("vat_rate")),
            [5.0, 19.0, 23.0])
        self.assertEqual(receipt.amount_total, 181.90)
        self.assertEqual(receipt.amount_untaxed, 166.08)
        self.assertEqual(receipt.amount_tax, 15.82)

    def test_offline_capture_stores_the_returned_identifier(self):
        """Not the QR string: the same purchase has two possible QR payloads."""
        receipt = self._receipt(QR_OFFLINE_RESTAURANT)
        with patch.object(self.provider_cls, "_fetch",
                          self._answer("receipt_offline_restaurant.json")):
            receipt.action_capture()
        self.assertTrue(receipt.receipt_uid.startswith("O-"))
        self.assertNotEqual(receipt.receipt_uid, QR_OFFLINE_RESTAURANT)
        # The log records the key as it was SENT, with the timestamp in the
        # service's own dotted format rather than the QR's YYMMDDHHMMSS.
        key = receipt.l10n_sk_ekasa_call_ids.request_key
        self.assertTrue(key.startswith("AAAA0001-BBBB0002"))
        self.assertIn("14.03.2026 19:59:02", key)
        self.assertNotIn("260314195902", key)

    def test_recapture_does_not_duplicate_the_detail(self):
        receipt = self._receipt(QR_OFFLINE_RESTAURANT)
        with patch.object(self.provider_cls, "_fetch",
                          self._answer("receipt_offline_restaurant.json")):
            receipt.action_capture()
            self.assertEqual(len(receipt.line_ids), 12)
            receipt.action_capture()
        self.assertEqual(len(receipt.line_ids), 12)
        self.assertEqual(len(receipt.tax_summary_ids), 3)

    # ------------------------------------------------------------------
    # failures
    # ------------------------------------------------------------------
    def test_unregistered_receipt_is_an_error_not_an_empty_success(self):
        """A miss is HTTP 200 with a null body, so it must be tested for."""
        receipt = self._receipt(QR_ONLINE_FUEL)
        with patch.object(
                self.provider_cls, "_fetch",
                self._answer(outcome="not_found",
                             message="Finančná správa holds no receipt")):
            receipt.action_capture()
        self.assertEqual(receipt.state, "error")
        self.assertIn("no receipt", receipt.review_reason)
        self.assertFalse(receipt.line_ids)
        self.assertEqual(receipt.l10n_sk_ekasa_call_ids.outcome, "not_found")

    def test_transport_failure_leaves_the_receipt_alone(self):
        receipt = self._receipt(QR_ONLINE_FUEL)
        with patch.object(
                self.provider_cls, "_fetch",
                self._answer(outcome="transport",
                             message="Could not reach the service")):
            receipt.action_capture()
        self.assertEqual(receipt.state, "error")
        self.assertFalse(receipt.amount_total)
        self.assertEqual(receipt.l10n_sk_ekasa_call_ids.outcome, "transport")

    def test_malformed_qr_never_reaches_the_network(self):
        receipt = self._receipt(QR_ONLINE_FUEL)
        receipt.qr_raw = "O-NOTHEXADECIMAL"
        receipt.provider_id = self.provider
        called = []

        def _should_not_run(self_model, company, request):
            called.append(request)
            return None, {"outcome": "found"}

        with patch.object(self.provider_cls, "_fetch", _should_not_run):
            receipt.action_capture()
        self.assertEqual(receipt.state, "error")
        self.assertFalse(called)
        self.assertEqual(self.env["sk.ekasa.call"].search_count(
            [("receipt_id", "=", receipt.id)]), 0)

    # ------------------------------------------------------------------
    # all the way to a document
    # ------------------------------------------------------------------
    def test_capture_then_bill_posts_the_sellers_own_vat(self):
        receipt = self._receipt(QR_OFFLINE_RESTAURANT)
        with patch.object(self.provider_cls, "_fetch",
                          self._answer("receipt_offline_restaurant.json")):
            receipt.action_capture()
        receipt.action_create_partner()
        move = receipt.action_create_bill()
        self.assertEqual(len(move.invoice_line_ids), 3)
        self.assertAlmostEqual(move.amount_untaxed, 166.08, places=2)
        self.assertAlmostEqual(move.amount_tax, 15.82, places=2)
        self.assertAlmostEqual(move.amount_total, 181.90, places=2)
        self.assertEqual(move.state, "draft")
        self.assertEqual(receipt.state, "done")

    def test_fuel_bill_matches_to_the_cent(self):
        receipt = self._receipt(QR_ONLINE_FUEL)
        with patch.object(self.provider_cls, "_fetch",
                          self._answer("receipt_online_fuel.json")):
            receipt.action_capture()
        receipt.action_create_partner()
        move = receipt.action_create_bill()
        self.assertAlmostEqual(move.amount_total, 57.85, places=2)
        self.assertAlmostEqual(move.amount_tax, 10.82, places=2)
        self.assertEqual(move.invoice_line_ids.price_unit, 47.03)
        self.assertEqual(move.invoice_date, fields.Date.to_date("2026-03-20"))
