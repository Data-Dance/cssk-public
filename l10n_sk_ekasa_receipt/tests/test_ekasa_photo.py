# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from datetime import datetime
from unittest.mock import patch

from odoo import fields
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged

from odoo.addons.l10n_cssk_receipt_capture.tests.qr_images import (
    LOYALTY_LINK, receipt_image,
)

from .common import QR_ONLINE_FUEL, load_fixture


@tagged("post_install", "-at_install")
class TestEkasaPhoto(AccountTestInvoicingCommon):
    """From a photograph to the registered receipt, and how failures are kinded.

    zxing-cpp is a hard dependency of this module, so nothing here skips.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.write({
            "l10n_sk_ekasa_enabled": True,
            "l10n_sk_ekasa_ip_notified": True,
            "cssk_receipt_expense_account_id":
                cls.company_data["default_account_expense"].id,
        })
        cls.env["account.tax"].create({
            "name": "DPH 23% (test)", "amount_type": "percent", "amount": 23.0,
            "type_tax_use": "purchase", "price_include_override": "tax_excluded",
            "company_id": cls.company.id,
        })
        cls.provider_cls = type(cls.env["cssk.receipt.provider.sk_ekasa"])
        # Only eKasa may answer here; another installed reader would blur what
        # these tests are about.
        cls.env["cssk.receipt.provider"].search(
            [("code", "!=", "sk_ekasa")]).active = False

    def _photo_receipt(self, codes):
        attachment = self.env["ir.attachment"].create({
            "name": "receipt.jpg", "mimetype": "image/jpeg",
            "datas": base64.b64encode(receipt_image(codes)),
        })
        return self.env["cssk.receipt"].create({
            "company_id": self.company.id,
            "currency_id": self.company.currency_id.id,
            "attachment_id": attachment.id,
        })

    def _fetch(self, fixture=None, outcome="found", message="x"):
        payload = load_fixture(fixture) if fixture else None

        def _fake(self_model, company, request):
            return payload, {"outcome": outcome, "http_status": 200,
                             "return_value": 0, "message": message}
        return patch.object(self.provider_cls, "_fetch", _fake)

    # ------------------------------------------------------------------
    def test_a_photograph_is_captured_from_its_fiscal_code(self):
        """The case that failed on a real fuel receipt: a loyalty-app QR printed
        above the fiscal one. Only the fiscal code may be looked up."""
        receipt = self._photo_receipt([LOYALTY_LINK, QR_ONLINE_FUEL])
        with self._fetch("receipt_online_fuel.json"):
            receipt.action_capture()
        self.assertEqual(receipt.state, "captured", receipt.review_reason)
        self.assertEqual(receipt.qr_source, "decoded")
        self.assertEqual(receipt.qr_raw, QR_ONLINE_FUEL)
        self.assertIn(LOYALTY_LINK, receipt.qr_detected)
        self.assertEqual(receipt.receipt_uid, QR_ONLINE_FUEL)
        self.assertEqual(receipt.amount_total, 57.85)
        self.assertEqual(receipt.l10n_sk_ekasa_call_ids.request_key, QR_ONLINE_FUEL)

    def test_an_archived_reader_is_named_not_called_a_non_receipt_code(self):
        """With eKasa archived, its code was reported as "not a receipt
        verification code" — true of the loyalty link, false of this one."""
        self.env["cssk.receipt.provider"].search(
            [("code", "=", "sk_ekasa")]).active = False
        receipt = self._photo_receipt([LOYALTY_LINK, QR_ONLINE_FUEL])
        receipt._prepare_qr()
        self.assertFalse(receipt.qr_raw)
        lines = receipt.qr_detected.splitlines()
        fiscal = next(line for line in lines if QR_ONLINE_FUEL in line)
        loyalty = next(line for line in lines if LOYALTY_LINK in line)
        self.assertIn("archived", fiscal)
        self.assertNotIn("not a receipt verification code", fiscal)
        self.assertIn("not a receipt verification code", loyalty)

    def test_the_issue_time_is_bratislava_time_stored_in_utc(self):
        """The fixture says 20.03.2026 09:36:36 — winter time, so 08:36:36 UTC,
        whatever the capturing user's own time zone."""
        self.env.user.tz = "America/New_York"
        receipt = self._photo_receipt([QR_ONLINE_FUEL])
        with self._fetch("receipt_online_fuel.json"):
            receipt.action_capture()
        self.assertEqual(receipt.issue_date, datetime(2026, 3, 20, 8, 36, 36))
        self.assertEqual(receipt.issue_tz, "Europe/Bratislava")
        self.assertEqual(receipt._issue_local_date(), fields.Date.to_date("2026-03-20"))

    def test_switched_off_is_unavailable_and_says_so(self):
        self.company.l10n_sk_ekasa_enabled = False
        receipt = self._photo_receipt([QR_ONLINE_FUEL])
        receipt.action_capture()
        self.assertEqual(receipt.state, "error")
        self.assertIn("switched off", receipt.review_reason)
        self.assertEqual(receipt.attempt_ids.outcome, "unavailable")
        self.assertFalse(receipt.next_attempt_at)

    def test_a_network_failure_is_retried_on_a_schedule(self):
        receipt = self._photo_receipt([QR_ONLINE_FUEL])
        with self._fetch(outcome="transport", message="timed out"):
            receipt.action_capture()
        self.assertEqual(receipt.state, "error")
        self.assertTrue(receipt.next_attempt_at)
        self.assertTrue(receipt.attempt_ids.transient)

    def test_an_unregistered_receipt_is_not(self):
        receipt = self._photo_receipt([QR_ONLINE_FUEL])
        with self._fetch(outcome="not_found", message="no receipt"):
            receipt.action_capture()
        self.assertEqual(receipt.state, "error")
        self.assertFalse(receipt.next_attempt_at)
        self.assertFalse(receipt.attempt_ids.transient)

    def test_the_provider_recognises_its_codes_and_nothing_else(self):
        impl = self.env["cssk.receipt.provider.sk_ekasa"]
        self.assertTrue(impl._accepts_qr(QR_ONLINE_FUEL))
        self.assertTrue(impl._accepts_qr("0-ABCDEF0000000002ABCDEF0000000002"))
        self.assertFalse(impl._accepts_qr(LOYALTY_LINK))
        self.assertIn("OVERTE DOKLAD POMOCOU QR K", impl._scan_hint())
        self.assertEqual(impl._issue_timezone(False), "Europe/Bratislava")
