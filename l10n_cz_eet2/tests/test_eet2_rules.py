# -*- coding: utf-8 -*-
"""Rules from Act 180/2026 Sb. and the item methodology: 48 h continuation,
UTC parsing, CZK conversion, validation, verification-mode test, re-queueing."""
import base64
from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.addons.account.tests.common import AccountTestInvoicingCommon

from ..lib import eet2_client
from ..models import eet2_transaction as tx_model
from .test_eet2_client import _throwaway_p12


def _result(**kw):
    return eet2_client.SendResult(eet2_client.Odpoved(**kw), b"<r/>", "xgtid")


class TestEet2Rules(TransactionCase):
    _PATCH = "odoo.addons.l10n_cz_eet2.lib.eet2_client.send"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        p12, pw = _throwaway_p12(b"pw")
        cls.p12_b64 = base64.b64encode(p12)
        cls.cert = cls.env["l10n.cz.eet2.certificate"].create({
            "name": "test", "company_id": cls.company.id,
            "environment": "playground",
            "p12_file": cls.p12_b64, "password": "pw",
        })
        cls.company.write({
            "l10n_cz_eet2_enabled": True,
            "l10n_cz_eet2_environment": "playground",
            "l10n_cz_eet2_eic_popl": "CZ00000019",
            "l10n_cz_eet2_id_jednotky": 303,
            "l10n_cz_eet2_certificate_id": cls.cert.id,
            "l10n_cz_eet2_max_attempts": 3,
        })
        cls.czk = cls.env.ref("base.CZK")
        cls.eur = cls.env.ref("base.EUR")
        cls.eur.active = True

    def _new_tx(self, **kw):
        vals = dict(id_pokl="P1", porad_cis="1",
                    dat_trzby=fields.Datetime.now(), celk_trzba=100.0)
        vals.update(kw)
        return self.env["l10n.cz.eet2.transaction"].create_from_values(
            self.company, **vals)

    # --- § 20: never give up -------------------------------------------
    def test_retry_continues_past_warn_threshold(self):
        tx = self._new_tx()
        with patch(self._PATCH, side_effect=ConnectionError("down")):
            for _ in range(6):
                tx.next_attempt = fields.Datetime.now()
                tx._send()
        self.assertEqual(tx.state, "retry", "an unsent sale stays in the queue")
        self.assertEqual(tx.attempt_count, 6)   # past max_attempts=3, still going
        self.assertTrue(tx.next_attempt)
        self.assertFalse(tx.is_overdue)

    def test_backoff_never_sleeps_past_48h(self):
        tx = self._new_tx(dat_trzby=fields.Datetime.now() - timedelta(hours=47, minutes=50))
        tx.attempt_count = 10                   # backoff would be 60 min
        delay = tx._backoff_delay()
        self.assertLessEqual(delay, timedelta(minutes=10, seconds=1))

    def test_overdue_flag_and_activity_once(self):
        tx = self._new_tx(dat_trzby=fields.Datetime.now() - timedelta(hours=49))
        with patch(self._PATCH, side_effect=ConnectionError("down")):
            tx._send()
            self.assertTrue(tx.is_overdue)
            self.assertEqual(tx.state, "retry")
            # still scheduled, never more than an hour away
            self.assertLessEqual(tx.next_attempt,
                                fields.Datetime.now() + timedelta(minutes=61))
            n_act = len(tx.activity_ids)
            self.assertEqual(n_act, 1)
            tx.next_attempt = fields.Datetime.now()
            tx._send()
            self.assertEqual(len(tx.activity_ids), 1, "one activity, not one per attempt")
        with patch(self._PATCH, return_value=_result(pok="b3a09b52-7c87-4014-a496-4c7a53cf9125-ff", test=True)):
            tx._send()
        self.assertEqual(tx.state, "accepted")
        self.assertFalse(tx.activity_ids, "acceptance closes the warning")

    def test_build_error_is_retried_hourly_and_flagged(self):
        """A build failure parks nothing: hourly retry, overdue flag past 48 h."""
        self.company.l10n_cz_eet2_certificate_id = False
        tx = self._new_tx(dat_trzby=fields.Datetime.now() - timedelta(hours=49))
        tx._send()
        self.assertEqual(tx.state, "error")
        self.assertTrue(tx.next_attempt)
        self.assertTrue(tx.is_overdue)
        self.assertEqual(len(tx.activity_ids), 1)
        # the cron picks error records up once they are due
        tx.next_attempt = fields.Datetime.now()
        self.company.l10n_cz_eet2_certificate_id = self.cert   # requeues -> to_send
        with patch(self._PATCH, return_value=_result(pok="b3a09b52-7c87-4014-a496-4c7a53cf9125-ff", test=True)):
            self.env["l10n.cz.eet2.transaction"]._cron_send_pending()
        self.assertEqual(tx.state, "accepted")

    def test_cron_survives_internal_crash(self):
        tx = self._new_tx()
        tx._enqueue()
        with patch(self._PATCH, side_effect=KeyError("parser bug")):
            self.env["l10n.cz.eet2.transaction"]._cron_send_pending()
        # KeyError is caught inside _send as a transport failure -> retry;
        # here we force a crash in _apply_response instead.
        tx.action_requeue() if tx.state in ("error", "rejected") else None
        tx.write({"state": "to_send", "next_attempt": fields.Datetime.now()})
        with patch(self._PATCH, return_value=_result(pok="b3a09b52-7c87-4014-a496-4c7a53cf9125-ff", test=True)), \
             patch.object(type(tx), "_apply_response", side_effect=RuntimeError("boom")):
            self.env["l10n.cz.eet2.transaction"]._cron_send_pending()
        self.assertEqual(tx.state, "retry")
        self.assertIn("boom", tx.chyba_text)
        self.assertGreater(tx.next_attempt, fields.Datetime.now())

    def test_requeue_button_and_cert_change(self):
        tx = self._new_tx()
        with patch(self._PATCH, return_value=_result(chyba_kod=4, chyba_text="bad sig")):
            tx._send()
        self.assertEqual(tx.state, "rejected")
        tx.action_requeue()
        self.assertEqual(tx.state, "to_send")
        # build error (no certificate) -> error; selecting a certificate requeues
        self.company.l10n_cz_eet2_certificate_id = False
        tx2 = self._new_tx()
        tx2._send()
        self.assertEqual(tx2.state, "error")
        self.company.l10n_cz_eet2_certificate_id = self.cert
        self.assertEqual(tx2.state, "to_send")
        # re-uploading the p12 requeues too
        tx2.write({"state": "error"})
        self.cert.write({"p12_file": self.p12_b64})
        self.assertEqual(tx2.state, "to_send")

    # --- timestamps ------------------------------------------------------
    def test_parse_dt_is_utc_whatever_the_host_zone(self):
        f = self.env["l10n.cz.eet2.transaction"]._parse_dt
        self.assertEqual(f("2027-03-04T18:25:21+01:00"), "2027-03-04 17:25:21")
        self.assertEqual(f("2027-07-04T18:25:21+02:00"), "2027-07-04 16:25:21")
        self.assertEqual(f("2027-03-04T18:25:21Z"), "2027-03-04 18:25:21")
        self.assertFalse(f(None))

    # --- § 17(1)(f): CZK --------------------------------------------------
    def test_eur_amounts_are_converted_to_czk(self):
        self.env["res.currency.rate"].create({
            "currency_id": self.eur.id, "company_id": self.company.id,
            "name": "2027-01-01", "rate": 0.04})            # 1 CZK = 0.04 EUR -> 25 CZK/EUR
        tx = self._new_tx(celk_trzba=10.0, cerp_zuct=4.0, currency_id=self.eur.id,
                        dat_trzby=fields.Datetime.to_datetime("2027-01-05 10:00:00"))
        self.assertEqual(tx.currency_id, self.czk)
        self.assertAlmostEqual(tx.celk_trzba, 250.0, places=2)
        self.assertAlmostEqual(tx.cerp_zuct, 100.0, places=2)
        self.assertEqual(tx.source_currency_id, self.eur)
        self.assertAlmostEqual(tx.source_amount, 10.0, places=2)
        self.assertEqual(tx._prepare_trzba().celk_trzba, "250.00")

    def test_czk_amounts_untouched(self):
        tx = self._new_tx(celk_trzba=99.5, currency_id=self.czk.id)
        self.assertAlmostEqual(tx.celk_trzba, 99.5)
        self.assertFalse(tx.source_currency_id)

    # --- validation -------------------------------------------------------
    def test_eic_validation_and_default(self):
        with self.assertRaises(ValidationError):
            self.company.l10n_cz_eet2_eic_popl = "CZ1234"
        self.company.l10n_cz_eet2_eic_popl = "CZ1234567890"
        other = self.env["res.company"].create({"name": "Other", "vat": "CZ 25596641"})
        self.assertEqual(other.l10n_cz_eet2_eic_popl, "CZ25596641")
        other2 = self.env["res.company"].create({"name": "Other2", "vat": "SK2020000001"})
        self.assertFalse(other2.l10n_cz_eet2_eic_popl)

    def test_id_jednotky_shape(self):
        for bad in (5, 10, 125, 1000000000):
            with self.subTest(bad=bad), self.assertRaises(ValidationError):
                self.company.l10n_cz_eet2_id_jednotky = bad
        for good in (11, 243, 999999994):
            self.company.l10n_cz_eet2_id_jednotky = good
        journal = self.env["account.journal"].create({
            "name": "EET misc", "code": "EETM", "type": "general",
            "company_id": self.company.id})
        with self.assertRaises(ValidationError):
            journal.l10n_cz_eet2_id_jednotky = 7
        journal.l10n_cz_eet2_id_jednotky = 31

    def test_response_timeout_minimum(self):
        with self.assertRaises(ValidationError):
            self.company.l10n_cz_eet2_response_timeout = 1.5
        self.company.l10n_cz_eet2_response_timeout = 2.0

    def test_sync_send_uses_company_timeout(self):
        self.company.l10n_cz_eet2_response_timeout = 3.0
        tx = self._new_tx()
        with patch(self._PATCH, return_value=_result(pok="b3a09b52-7c87-4014-a496-4c7a53cf9125-ff", test=True)) as send:
            tx._send(sync=True)
            self.assertEqual(send.call_args.kwargs["timeout"], 3.0)
            tx2 = self._new_tx()
            tx2._send()
            self.assertEqual(send.call_args.kwargs["timeout"], tx_model.ASYNC_TIMEOUT)

    # --- verification mode -----------------------------------------------
    def test_certificate_verification_action(self):
        with patch(self._PATCH, return_value=_result(chyba_kod=0, chyba_text="ok", test=True)) as send:
            action = self.cert.action_test_verification()
        self.assertEqual(action["params"]["type"], "success")
        tx = self.env["l10n.cz.eet2.transaction"].search(
            [("certificate_id", "=", self.cert.id), ("overeni", "=", True)])
        self.assertEqual(len(tx), 1)
        self.assertEqual(tx.state, "verified")
        self.assertIn(b'overeni="true"', send.call_args.args[0])
        with patch(self._PATCH, return_value=_result(chyba_kod=4, chyba_text="Neplatny podpis")):
            action = self.cert.action_test_verification()
        self.assertEqual(action["params"]["type"], "danger")
        self.assertIn("Neplatny podpis", action["params"]["message"])

    # --- certificate expiry ---------------------------------------------
    def test_expiry_cron_warns_once_per_threshold(self):
        Cert = self.env["l10n.cz.eet2.certificate"]
        self.cert.valid_to = fields.Datetime.now() + timedelta(days=20)
        Cert._cron_check_expiry()
        self.assertEqual(len(self.cert.activity_ids), 1)
        self.assertEqual(self.cert.expiry_warned_days, 30)
        Cert._cron_check_expiry()
        self.assertEqual(len(self.cert.activity_ids), 1)
        self.cert.valid_to = fields.Datetime.now() + timedelta(days=5)
        Cert._cron_check_expiry()
        self.assertEqual(len(self.cert.activity_ids), 2)
        self.assertEqual(self.cert.expiry_warned_days, 7)


@tagged("post_install", "-at_install")
class TestEet2PaymentFlag(AccountTestInvoicingCommon):
    """Needs a chart of accounts: a payment cannot post without one, and on a
    fresh install the company gets its chart (and its bank journal) only once
    every module is loaded, so this class runs post-install."""
    _PATCH = "odoo.addons.l10n_cz_eet2.lib.eet2_client.send"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        # A missing bank journal would surface as "journal_id NULL" on the
        # payment INSERT, far from the cause; say it here instead.
        assert cls.company_data["default_journal_bank"], "the test chart has no bank journal"
        p12, pw = _throwaway_p12(b"pw")
        cls.cert = cls.env["l10n.cz.eet2.certificate"].sudo().create({
            "name": "payment-test", "company_id": cls.company.id,
            "environment": "playground",
            "p12_file": base64.b64encode(p12), "password": "pw",
        })
        cls.company.write({
            "l10n_cz_eet2_enabled": True,
            "l10n_cz_eet2_environment": "playground",
            "l10n_cz_eet2_eic_popl": "CZ00000019",
            "l10n_cz_eet2_id_jednotky": 303,
            "l10n_cz_eet2_certificate_id": cls.cert.id,
        })

    def test_payment_contact_flag_defaults_from_journal(self):
        journal = self.company_data["default_journal_bank"]
        journal.l10n_cz_eet2_contact = False
        pay = self.env["account.payment"].create({
            "payment_type": "inbound", "partner_type": "customer",
            "partner_id": self.partner_a.id, "journal_id": journal.id, "amount": 10.0})
        self.assertFalse(pay.l10n_cz_eet2_contact)
        self.assertFalse(pay.l10n_cz_eet2_needed)
        pay.l10n_cz_eet2_contact = True       # QR scanned at the counter
        self.assertTrue(pay.l10n_cz_eet2_needed)
        pay.action_post()
        self.assertTrue(pay.l10n_cz_eet2_transaction_id)
        self.assertEqual(pay.l10n_cz_eet2_transaction_id.state, "to_send")
        # the journal default is picked up by a fresh payment
        journal.l10n_cz_eet2_contact = True
        pay2 = self.env["account.payment"].create({
            "payment_type": "inbound", "partner_type": "customer",
            "partner_id": self.partner_a.id, "journal_id": journal.id, "amount": 5.0})
        self.assertTrue(pay2.l10n_cz_eet2_contact)

    def _contact_payment(self, journal, amount=10.0, payment_type="inbound",
                        partner_type="customer"):
        pay = self.env["account.payment"].create({
            "payment_type": payment_type, "partner_type": partner_type,
            "partner_id": self.partner_a.id, "journal_id": journal.id,
            "amount": amount})
        pay.l10n_cz_eet2_contact = True
        return pay

    def test_reset_to_draft_sends_a_storno_and_repost_a_new_sale(self):
        """§ 8 ZoET: a reversed sale is evidenced again as a negative one."""
        journal = self.company_data["default_journal_bank"]
        pay = self._contact_payment(journal, 250.0)
        pay.action_post()
        sale = pay.l10n_cz_eet2_transaction_id
        self.assertEqual(sale.payment_id, pay)
        with patch(self._PATCH, return_value=_result(pok="a" * 36 + "-ff", test=True)):
            sale.sudo()._send()
        self.assertEqual(sale.state, "accepted")

        pay.action_draft()
        storno = pay.l10n_cz_eet2_transaction_ids - sale
        self.assertEqual(len(storno), 1)
        self.assertEqual(storno.storno_of_id, sale)
        self.assertEqual(sale.reversed_by_id, storno)
        self.assertAlmostEqual(storno.celk_trzba, -sale.celk_trzba, places=2)
        self.assertEqual((storno.id_pokl, storno.porad_cis), (sale.id_pokl, sale.porad_cis))
        self.assertEqual(storno.state, "to_send")
        self.assertGreaterEqual(storno.dat_trzby, sale.dat_trzby)
        # the payment still shows the sale it registered
        self.assertEqual(pay.l10n_cz_eet2_transaction_id, sale)
        # a second reset does not storno twice
        pay.action_post()
        new_sale = pay.l10n_cz_eet2_transaction_id
        self.assertNotEqual(new_sale, sale, "re-posting is a new sale")
        self.assertFalse(new_sale.storno_of_id)
        self.assertAlmostEqual(new_sale.celk_trzba, 250.0, places=2)
        self.assertEqual(len(pay.l10n_cz_eet2_transaction_ids), 3)
        self.assertEqual(pay.l10n_cz_eet2_transaction_count, 3)

    def test_cancel_sends_a_storno_even_while_the_sale_is_still_queued(self):
        """A queued sale will be sent (§ 20), so its reversal needs the storno
        just the same; a rejected one was never evidenced and gets none."""
        journal = self.company_data["default_journal_bank"]
        pay = self._contact_payment(journal, 40.0)
        pay.action_post()
        sale = pay.l10n_cz_eet2_transaction_id
        self.assertEqual(sale.state, "to_send")
        pay.action_cancel()
        self.assertTrue(sale.reversed_by_id)
        self.assertAlmostEqual(sale.reversed_by_id.celk_trzba, -40.0, places=2)

        pay2 = self._contact_payment(journal, 41.0)
        pay2.action_post()
        sale2 = pay2.l10n_cz_eet2_transaction_id
        sale2.sudo().write({"state": "rejected", "next_attempt": False})
        pay2.action_cancel()
        self.assertFalse(sale2.reversed_by_id)
        self.assertEqual(len(pay2.l10n_cz_eet2_transaction_ids), 1)

    def test_customer_refund_is_negative_and_supplier_money_is_no_sale(self):
        journal = self.company_data["default_journal_bank"]
        refund = self._contact_payment(journal, 99.0, payment_type="outbound")
        self.assertTrue(refund.l10n_cz_eet2_needed)
        refund.action_post()
        self.assertAlmostEqual(refund.l10n_cz_eet2_transaction_id.celk_trzba, -99.0, places=2)

        supplier = self._contact_payment(journal, 99.0, payment_type="outbound",
                                        partner_type="supplier")
        self.assertFalse(supplier.l10n_cz_eet2_needed, "cash paid to a supplier is not a tržba")
        supplier.action_post()
        self.assertFalse(supplier.l10n_cz_eet2_transaction_id)

    def test_manual_send_reuses_the_message(self):
        """A second record for the same sale would be a second sale."""
        journal = self.company_data["default_journal_bank"]
        pay = self._contact_payment(journal, 12.0)
        pay.action_post()
        tx = pay.l10n_cz_eet2_transaction_id
        with patch(self._PATCH, return_value=_result(pok="b" * 36 + "-ff", test=True)):
            pay.sudo().l10n_cz_eet2_action_send()
        self.assertEqual(pay.l10n_cz_eet2_transaction_id, tx)
        self.assertEqual(len(pay.l10n_cz_eet2_transaction_ids), 1)
        self.assertEqual(tx.state, "accepted")

    def test_storno_follows_the_sale_environment_and_is_unique(self):
        journal = self.company_data["default_journal_bank"]
        pay = self._contact_payment(journal, 30.0)
        pay.action_post()
        sale = pay.l10n_cz_eet2_transaction_id
        self.assertEqual(sale.environment, "playground")
        self.company.l10n_cz_eet2_environment = "production"
        pay.action_draft()
        storno = sale.reversed_by_id
        self.assertEqual(storno.environment, "playground", "a storno goes where the sale went")
        self.assertEqual(storno.certificate_id, sale.certificate_id)
        # the database refuses a second storno of the same sale
        with self.assertRaises(Exception), self.env.cr.savepoint():
            sale.sudo()._create_storno()
