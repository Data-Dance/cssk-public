# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import json
from datetime import datetime, timedelta
from unittest import skipUnless
from unittest.mock import patch

from odoo import fields
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged

from ..tools.errors import CaptureFailed, ProviderUnavailable
from .qr_images import FISCAL_ID, LOYALTY_LINK, qr_available, receipt_image


class FakeImpl:
    """A stand-in provider implementation, so every path can be forced."""

    def __init__(self, can=True, accepts=None, capture=None, printed=None,
                 tz="Europe/Bratislava", hint=None):
        self.can, self.accepts, self.capture = can, accepts, capture
        self.printed, self.tz, self.hint, self.calls = printed, tz, hint, []

    def _can_capture(self, receipt):
        return self.can(receipt) if callable(self.can) else self.can

    def _accepts_qr(self, payload):
        return bool(self.accepts and self.accepts(payload))

    def _qr_from_printed(self, identifiers):
        return self.printed(identifiers) if self.printed else []

    def _issue_timezone(self, receipt):
        return self.tz

    def _scan_hint(self):
        return self.hint

    def _capture(self, receipt):
        self.calls.append(receipt.qr_raw)
        return self.capture(receipt)


def fuel_vals(uid=None, issued=datetime(2026, 3, 20, 9, 36, 36), total=57.85,
              usage=None):
    vals = {
        "issue_date": issued,
        "amount_total": total,
        "seller_name": "Vzorová čerpacia stanica, a. s.",
        "seller_vat": "SK7199000006",
        "line_ids": [fields.Command.create({
            "name": "Benzín 95", "quantity": 31.17, "vat_rate": 23.0,
            "amount_total": total})],
        "tax_summary_ids": [fields.Command.create({
            "vat_rate": 23.0, "amount_untaxed": 47.03, "amount_tax": 10.82})],
    }
    if uid:
        vals["receipt_uid"] = uid
    if usage:
        vals["_usage"] = usage
    return vals


@tagged("post_install", "-at_install")
class TestCaptureFlow(AccountTestInvoicingCommon):
    """The capture loop, driven by stand-in providers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.cssk_receipt_expense_account_id = cls.company_data[
            "default_account_expense"]
        Provider = cls.env["cssk.receipt.provider"]
        # Isolate from whatever real providers this database has installed.
        Provider.search([]).active = False
        cls.prov_a = Provider.create({"name": "Reader A", "code": "test_a",
                                      "sequence": 1})
        cls.prov_b = Provider.create({"name": "Reader B", "code": "test_b",
                                      "sequence": 2})
        cls.tax_23 = cls.env["account.tax"].create({
            "name": "DPH 23% (test)", "amount_type": "percent", "amount": 23.0,
            "type_tax_use": "purchase", "price_include_override": "tax_excluded",
            "company_id": cls.company.id,
        })

    def _receipt(self, **vals):
        vals.setdefault("company_id", self.company.id)
        vals.setdefault("currency_id", self.company.currency_id.id)
        return self.env["cssk.receipt"].create(vals)

    def _with(self, **impls):
        """Patch the registry so provider code -> FakeImpl."""
        return patch.object(
            type(self.env["cssk.receipt.provider"]), "_implementation",
            lambda rec: impls.get(rec.code))

    # ------------------------------------------------------------------
    # fall-through, attempts, retries
    # ------------------------------------------------------------------
    def test_unavailable_provider_falls_through_to_the_next(self):
        """eKasa switched off must not stop the photograph being read."""
        def off(receipt):
            raise ProviderUnavailable("switched off here")
        receipt = self._receipt(qr_raw=FISCAL_ID)
        with self._with(test_a=FakeImpl(capture=off),
                        test_b=FakeImpl(capture=lambda r: fuel_vals())):
            receipt.action_capture()
        self.assertEqual(receipt.state, "captured", receipt.review_reason)
        self.assertEqual(receipt.provider_id, self.prov_b)
        self.assertEqual(receipt.attempt_ids.sorted("id").mapped("outcome"),
                         ["unavailable", "captured"])

    def test_every_provider_unavailable_says_why_for_each(self):
        def off(receipt):
            raise ProviderUnavailable("not configured")
        receipt = self._receipt(qr_raw=FISCAL_ID)
        with self._with(test_a=FakeImpl(capture=off), test_b=FakeImpl(capture=off)):
            receipt.action_capture()
        self.assertEqual(receipt.state, "error")
        self.assertIn("Reader A", receipt.review_reason)
        self.assertIn("Reader B", receipt.review_reason)

    def test_transient_failure_is_scheduled_and_permanent_is_not(self):
        def busy(receipt):
            raise CaptureFailed("busy", transient=True,
                                usage={"cost": 0.004, "input_tokens": 900})
        def refused(receipt):
            raise CaptureFailed("not registered")
        transient = self._receipt(qr_raw=FISCAL_ID)
        permanent = self._receipt(qr_raw=FISCAL_ID.replace("2", "3"))
        with self._with(test_a=FakeImpl(capture=busy)):
            transient.action_capture()
        with self._with(test_a=FakeImpl(capture=refused)):
            permanent.action_capture()
        self.assertEqual(transient.state, "error")
        self.assertTrue(transient.next_attempt_at)
        self.assertTrue(transient.attempt_ids.transient)
        # A failed call's spend is recorded, not hidden as 0.
        self.assertAlmostEqual(transient.total_cost, 0.004, places=6)
        self.assertEqual(transient.attempt_ids.input_tokens, 900)
        self.assertEqual(permanent.state, "error")
        self.assertFalse(permanent.next_attempt_at)

    def test_cron_retries_only_what_is_due_and_stops_after_the_last_delay(self):
        def busy(receipt):
            raise CaptureFailed("busy", transient=True)
        receipt = self._receipt(qr_raw=FISCAL_ID)
        with self._with(test_a=FakeImpl(capture=busy)):
            receipt.action_capture()
            for _attempt in range(5):
                receipt.next_attempt_at = fields.Datetime.now() - timedelta(minutes=1)
                self.env["cssk.receipt"]._cron_retry_transient()
                if not receipt.next_attempt_at:
                    break
        # One first try plus three scheduled retries, then it gives up.
        self.assertEqual(len(receipt.attempt_ids), 4)
        self.assertFalse(receipt.next_attempt_at)

    def test_a_retry_succeeding_clears_the_schedule(self):
        state = {"n": 0}
        def flaky(receipt):
            state["n"] += 1
            if state["n"] == 1:
                raise CaptureFailed("busy", transient=True)
            return fuel_vals()
        receipt = self._receipt(qr_raw=FISCAL_ID)
        with self._with(test_a=FakeImpl(capture=flaky)):
            receipt.action_capture()
            receipt.next_attempt_at = fields.Datetime.now() - timedelta(minutes=1)
            self.env["cssk.receipt"]._cron_retry_transient()
        self.assertEqual(receipt.state, "captured")
        self.assertFalse(receipt.next_attempt_at)

    def test_provider_is_chosen_afresh_not_taken_from_the_last_attempt(self):
        """After a photo reading failed, a scanned QR must go to the code reader."""
        receipt = self._receipt()
        receipt.provider_id = self.prov_b       # the previous, failed reader
        receipt.qr_raw = FISCAL_ID
        reader_a = FakeImpl(can=lambda r: bool(r.qr_raw), capture=lambda r: fuel_vals())
        reader_b = FakeImpl(capture=lambda r: fuel_vals())
        with self._with(test_a=reader_a, test_b=reader_b):
            receipt.action_capture()
        self.assertEqual(receipt.provider_id, self.prov_a)
        self.assertFalse(reader_b.calls)

    def test_a_duplicate_is_refused_with_its_name_not_a_database_error(self):
        first = self._receipt(qr_raw=FISCAL_ID)
        second = self._receipt(qr_raw=FISCAL_ID)
        with self._with(test_a=FakeImpl(capture=lambda r: fuel_vals(uid=FISCAL_ID))):
            first.action_capture()
            second.action_capture()
        self.assertEqual(first.state, "captured")
        self.assertEqual(second.state, "error")
        self.assertIn(first.display_name, second.review_reason)

    def test_nothing_can_read_it_is_an_error_with_a_reason(self):
        receipt = self._receipt()
        with self._with():
            receipt.action_capture()
        self.assertEqual(receipt.state, "error")
        self.assertIn("neither a photograph nor a QR", receipt.review_reason)

    def test_failure_is_never_raised_out_of_the_loop(self):
        """One bad receipt in a batch must not abort the others."""
        def boom(receipt):
            raise UserError("unreadable")
        good, bad = self._receipt(qr_raw=FISCAL_ID), self._receipt(qr_raw="x")
        with self._with(test_a=FakeImpl(
                capture=lambda r: boom(r) if r.qr_raw == "x" else fuel_vals())):
            (bad | good).action_capture()
        self.assertEqual(bad.state, "error")
        self.assertEqual(good.state, "captured")

    # ------------------------------------------------------------------
    # time
    # ------------------------------------------------------------------
    def test_printed_local_time_is_stored_in_utc(self):
        receipt = self._receipt(qr_raw=FISCAL_ID)
        with self._with(test_a=FakeImpl(capture=lambda r: fuel_vals(
                issued=datetime(2026, 3, 20, 9, 36, 36)))):
            receipt.action_capture()
        # 20 March is winter time in Bratislava: UTC+1.
        self.assertEqual(receipt.issue_date, datetime(2026, 3, 20, 8, 36, 36))
        self.assertEqual(receipt.issue_tz, "Europe/Bratislava")

    def test_a_receipt_printed_after_midnight_keeps_its_date(self):
        """00:30 on 1 September is 22:30 UTC on 31 August."""
        receipt = self._receipt(qr_raw=FISCAL_ID)
        with self._with(test_a=FakeImpl(capture=lambda r: fuel_vals(
                issued=datetime(2026, 9, 1, 0, 30, 0)))):
            receipt.action_capture()
        self.assertEqual(receipt.issue_date, datetime(2026, 8, 31, 22, 30, 0))
        self.assertEqual(receipt._issue_local_date(), fields.Date.to_date("2026-09-01"))
        receipt.action_create_partner()
        move = receipt.action_create_bill()
        self.assertEqual(move.invoice_date, fields.Date.to_date("2026-09-01"))
        self.assertIn("2026-09-01", receipt.name)

    # ------------------------------------------------------------------
    # chatter
    # ------------------------------------------------------------------
    def test_review_reasons_are_a_real_list_not_escaped_markup(self):
        receipt = self._receipt(qr_raw=FISCAL_ID)
        with self._with(test_a=FakeImpl(capture=lambda r: fuel_vals(total=60.0))):
            receipt.action_capture()
        self.assertEqual(receipt.state, "review")
        body = receipt.message_ids.sorted("id")[-1].body
        self.assertIn("<li>", body)
        self.assertNotIn("&lt;li&gt;", body)

    # ------------------------------------------------------------------
    # the simplified-invoice limit
    # ------------------------------------------------------------------
    def _limit_receipt(self, total, vat, currency="EUR", seller_vat="SK7199000006"):
        cur = self.env["res.currency"].with_context(active_test=False).search(
            [("name", "=", currency)], limit=1)
        cur.active = True  # a document in an inactive currency cannot be posted
        base = round(total - vat, 2)
        return self._receipt(
            currency_id=cur.id, amount_total=total, seller_vat=seller_vat,
            seller_name="Vzorový predajca",
            line_ids=[fields.Command.create({
                "name": "Tovar", "quantity": 1, "vat_rate": 23.0,
                "amount_total": total})],
            tax_summary_ids=[fields.Command.create({
                "vat_rate": 23.0, "amount_untaxed": base, "amount_tax": vat})])

    def test_sk_receipt_above_400_eur_is_booked_with_its_vat_as_cost(self):
        """The receipt is a valid document at any amount; only the deduction
        stops. It is NOT parked: it posts at its gross, with no VAT claimed."""
        receipt = self._limit_receipt(401.25, 75.03)
        self.assertFalse(receipt._check_reconciliation())
        self.assertFalse(receipt.vat_deductible)
        self.assertIn("§ 74 ods. 3 písm. b)", receipt.vat_deductible_note)
        self.assertIn("§ 51 ods. 1 písm. a)", receipt.vat_deductible_note)
        receipt.state = "captured"
        receipt.action_create_partner()
        move = receipt.action_create_bill()
        self.assertAlmostEqual(move.amount_total, 401.25, places=2)
        self.assertAlmostEqual(move.amount_tax, 0.0, places=2)
        self.assertFalse(move.invoice_line_ids.tax_ids)

    def test_a_full_invoice_in_hand_restores_the_deduction(self):
        receipt = self._limit_receipt(401.25, 75.03)
        receipt.vat_full_invoice = True
        self.assertTrue(receipt.vat_deductible)
        receipt.state = "captured"
        receipt.action_create_partner()
        move = receipt.action_create_bill()
        self.assertAlmostEqual(move.amount_tax, 75.03, places=2)
        self.assertAlmostEqual(move.amount_total, 401.25, places=2)

    def test_the_full_invoice_override_survives_a_recompute(self):
        """Editing a dependency used to recompute the flag and drop the
        accountant's decision without a word."""
        receipt = self._limit_receipt(401.25, 75.03)
        receipt.vat_full_invoice = True
        receipt.issue_date = "2026-10-03 10:00:00"
        receipt.seller_vat = "SK2099000002"
        self.assertTrue(receipt.vat_deductible)

    def test_posting_refuses_vat_a_receipt_does_not_allow(self):
        """The draft is checked at creation, then edited by a person; this is
        the check that holds when it is posted."""
        receipt = self._limit_receipt(401.25, 75.03)
        receipt.state = "captured"
        receipt.action_create_partner()
        move = receipt.action_create_bill()
        move.invoice_line_ids[:1].tax_ids = self.tax_23
        with self.assertRaisesRegex(UserError, "not deductible"):
            move.action_post()
        move.invoice_line_ids.tax_ids = False
        move.action_post()
        self.assertEqual(move.state, "posted")

    def test_sk_receipt_at_400_eur_is_deductible(self):
        receipt = self._limit_receipt(400.00, 74.80)
        self.assertTrue(receipt.vat_deductible)
        self.assertFalse(receipt.vat_deductible_note)

    def test_cz_receipt_above_10000_czk_is_not_deductible(self):
        receipt = self._limit_receipt(10001.00, 1870.11, currency="CZK",
                                      seller_vat="CZ12345678")
        self.assertFalse(receipt.vat_deductible)
        self.assertIn("§ 30 odst. 1", receipt.vat_deductible_note)

    def test_no_vat_means_no_limit_question(self):
        receipt = self._limit_receipt(500.00, 0.0)
        receipt.tax_summary_ids.write({"vat_rate": 0.0, "amount_untaxed": 500.0})
        receipt.line_ids.vat_rate = 0.0
        self.assertTrue(receipt.vat_deductible)

    # ------------------------------------------------------------------
    # identifiers printed on the paper
    # ------------------------------------------------------------------
    def test_printed_identifiers_are_confirmed_by_the_other_provider(self):
        """The QR would not decode; the text beside it is looked up instead."""
        def photo(receipt):
            vals = fuel_vals(total=57.85)
            vals["seller_name"] = "As read off the paper"
            vals["printed_identifiers"] = json.dumps({"uid": "0-ABC"})
            return vals
        def lookup(receipt):
            assert receipt.qr_raw == FISCAL_ID, receipt.qr_raw
            vals = fuel_vals(uid=FISCAL_ID)
            vals["seller_name"] = "As registered"
            return vals
        receipt = self._receipt(attachment_id=self._image([]).id)
        reader = FakeImpl(can=lambda r: bool(r.qr_raw), capture=lookup,
                          printed=lambda ids: [FISCAL_ID])
        with self._with(test_a=reader, test_b=FakeImpl(capture=photo)):
            receipt.action_capture()
        self.assertEqual(receipt.state, "captured", receipt.review_reason)
        self.assertEqual(receipt.seller_name, "As registered")
        self.assertEqual(receipt.qr_source, "printed")
        self.assertEqual(receipt.receipt_uid, FISCAL_ID)
        self.assertEqual(receipt.provider_id, self.prov_a)

    def test_a_registered_receipt_with_another_total_is_not_taken(self):
        """If a key ever found a DIFFERENT receipt, its total gives it away."""
        def photo(receipt):
            vals = fuel_vals()
            vals["printed_identifiers"] = json.dumps({"uid": "O-ZZZ"})
            return vals
        def lookup(receipt):
            return fuel_vals(uid=FISCAL_ID, total=999.00)
        receipt = self._receipt(attachment_id=self._image([]).id)
        reader = FakeImpl(can=lambda r: bool(r.qr_raw), capture=lookup,
                          printed=lambda ids: [FISCAL_ID])
        with self._with(test_a=reader, test_b=FakeImpl(capture=photo)):
            receipt.action_capture()
        self.assertEqual(receipt.state, "review")
        self.assertEqual(receipt.amount_total, 57.85)
        self.assertFalse(receipt.receipt_uid)
        self.assertIn("999.00", " ".join(m for m in receipt.attempt_ids.mapped("message") if m))

    def test_printed_identifiers_that_match_nothing_park_the_reading(self):
        def photo(receipt):
            vals = fuel_vals()
            vals["printed_identifiers"] = json.dumps({"uid": "O-ZZZ"})
            return vals
        def not_found(receipt):
            raise CaptureFailed("no such receipt")
        receipt = self._receipt(attachment_id=self._image([]).id)
        reader = FakeImpl(can=lambda r: bool(r.qr_raw), capture=not_found,
                          printed=lambda ids: [FISCAL_ID])
        with self._with(test_a=reader, test_b=FakeImpl(capture=photo)):
            receipt.action_capture()
        self.assertEqual(receipt.state, "review")
        self.assertIn("did not match a registered receipt", receipt.review_reason)
        self.assertFalse(receipt.qr_raw)

    # ------------------------------------------------------------------
    # the photograph's QR codes
    # ------------------------------------------------------------------
    def _image(self, codes):
        return self.env["ir.attachment"].create({
            "name": "receipt.jpg", "mimetype": "image/jpeg",
            "datas": base64.b64encode(receipt_image(codes)),
        })

    @skipUnless(qr_available(), "zxing-cpp is not installed")
    def test_the_fiscal_code_is_picked_out_from_under_a_loyalty_link(self):
        receipt = self._receipt(attachment_id=self._image(
            [LOYALTY_LINK, FISCAL_ID]).id)
        reader = FakeImpl(can=lambda r: bool(r.qr_raw),
                          accepts=lambda p: p.startswith("O-"),
                          capture=lambda r: fuel_vals(uid=r.qr_raw))
        with self._with(test_a=reader):
            receipt.action_capture()
        self.assertEqual(receipt.qr_raw, FISCAL_ID)
        self.assertEqual(receipt.qr_source, "decoded")
        self.assertIn("Ignored", receipt.qr_detected)
        self.assertIn(LOYALTY_LINK, receipt.qr_detected)
        self.assertEqual(receipt.state, "captured", receipt.review_reason)

    @skipUnless(qr_available(), "zxing-cpp is not installed")
    def test_no_code_on_the_photograph_is_said_so(self):
        receipt = self._receipt(attachment_id=self._image([]).id)
        with self._with(test_a=FakeImpl(can=lambda r: bool(r.qr_raw))):
            receipt.action_capture()
        self.assertEqual(receipt.state, "error")
        self.assertIn("No QR code found", receipt.review_reason)

    def test_without_a_decoder_the_reason_names_the_package(self):
        receipt = self._receipt(attachment_id=self._image([]).id)
        with patch("odoo.addons.l10n_cssk_receipt_capture.models.cssk_receipt."
                   "decoder_available", return_value=False), \
                self._with(test_a=FakeImpl(can=lambda r: bool(r.qr_raw))):
            receipt.action_capture()
        self.assertIn("zxing-cpp", receipt.review_reason)

    # ------------------------------------------------------------------
    # camera scan
    # ------------------------------------------------------------------
    def test_scanning_a_loyalty_link_asks_for_the_right_code(self):
        with self._with(test_a=FakeImpl(accepts=lambda p: p.startswith("O-"),
                                        hint="Scan the one at the bottom.")):
            result = self.env["cssk.receipt"].action_capture_from_scan(LOYALTY_LINK)
        self.assertTrue(result["retry"])
        self.assertIn("not a receipt verification code", result["message"])
        self.assertIn("Scan the one at the bottom.", result["message"])

    def test_scanning_the_fiscal_code_captures_and_opens_it(self):
        reader = FakeImpl(can=lambda r: bool(r.qr_raw),
                          accepts=lambda p: p.startswith("O-"),
                          capture=lambda r: fuel_vals(uid=r.qr_raw))
        with self._with(test_a=reader):
            result = self.env["cssk.receipt"].action_capture_from_scan(FISCAL_ID)
            again = self.env["cssk.receipt"].action_capture_from_scan(FISCAL_ID)
        self.assertFalse(result["retry"])
        receipt = self.env["cssk.receipt"].browse(result["action"]["res_id"])
        self.assertEqual(receipt.qr_source, "scanned")
        self.assertEqual(receipt.state, "captured")
        # Scanning the same code again opens the same receipt, not a second one.
        self.assertEqual(again["action"]["res_id"], receipt.id)
        self.assertEqual(len(reader.calls), 1)
