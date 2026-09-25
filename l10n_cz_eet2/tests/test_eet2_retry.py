# -*- coding: utf-8 -*-
"""Tests for the cron-based retry state machine (network `send` is mocked)."""
import base64
from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase

from ..lib import eet2_client
from .test_eet2_client import _throwaway_p12


def _ok_result():
    return eet2_client.SendResult(
        eet2_client.Odpoved(pok="b3a09b52-7c87-4014-a496-4c7a53cf9125-ff", test=True),
        b"<ok/>", "xgtid-1")


def _err_result(kod):
    return eet2_client.SendResult(
        eet2_client.Odpoved(chyba_kod=kod, chyba_text="err %s" % kod), b"<err/>", None)


class TestEet2Retry(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        p12, pw = _throwaway_p12(b"pw")
        cls.cert = cls.env["l10n.cz.eet2.certificate"].create({
            "name": "test", "company_id": cls.company.id,
            "environment": "playground",
            "p12_file": base64.b64encode(p12), "password": "pw",
        })
        cls.company.write({
            "l10n_cz_eet2_enabled": True,
            "l10n_cz_eet2_environment": "playground",
            "l10n_cz_eet2_eic_popl": "CZ00000019",
            "l10n_cz_eet2_id_jednotky": 303,
            "l10n_cz_eet2_certificate_id": cls.cert.id,
            "l10n_cz_eet2_max_attempts": 3,
        })

    def _new_tx(self):
        return self.env["l10n.cz.eet2.transaction"].create_from_values(
            self.company, id_pokl="P1", porad_cis="1",
            dat_trzby=fields.Datetime.now(), celk_trzba=100.0)

    _PATCH = "odoo.addons.l10n_cz_eet2.lib.eet2_client.send"

    def test_enqueue_then_cron_success(self):
        tx = self._new_tx()
        tx._enqueue()
        self.assertEqual(tx.state, "to_send")
        with patch(self._PATCH, return_value=_ok_result()):
            self.env["l10n.cz.eet2.transaction"]._cron_send_pending()
        self.assertEqual(tx.state, "accepted")
        self.assertTrue(tx.pok.endswith("-ff"))
        self.assertFalse(tx.next_attempt)

    def test_network_error_schedules_retry(self):
        tx = self._new_tx()
        with patch(self._PATCH, side_effect=ConnectionError("boom")):
            tx._send()
        self.assertEqual(tx.state, "retry")
        self.assertEqual(tx.attempt_count, 1)
        self.assertTrue(tx.next_attempt)
        # a retry is a resend -> prvni_zaslani must flip to False on the next try
        with patch(self._PATCH, return_value=_ok_result()):
            tx._send()
        self.assertFalse(tx.prvni_zaslani)
        self.assertEqual(tx.state, "accepted")

    def test_temporary_kod_retries_permanent_rejects(self):
        tx = self._new_tx()
        with patch(self._PATCH, return_value=_err_result(-1)):
            tx._send()
        self.assertEqual(tx.state, "retry")          # kod<0 is temporary

        tx2 = self._new_tx()
        with patch(self._PATCH, return_value=_err_result(4)):
            tx2._send()
        self.assertEqual(tx2.state, "rejected")       # kod=4 signature = permanent
        self.assertFalse(tx2.next_attempt)

    def test_gives_up_after_max_attempts(self):
        tx = self._new_tx()
        tx._enqueue()
        # Mimic the cron: only re-send while still queued/retrying.
        with patch(self._PATCH, side_effect=ConnectionError("down")):
            for _ in range(10):
                if tx.state not in ("to_send", "retry"):
                    break
                tx.next_attempt = fields.Datetime.now()   # make it due
                tx._send()
        self.assertEqual(tx.state, "error")
        self.assertEqual(tx.attempt_count, 3)         # max_attempts on the company
