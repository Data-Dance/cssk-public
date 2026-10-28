# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from contextlib import closing
from unittest.mock import patch

from odoo import SUPERUSER_ID, api
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestConcurrentSend(TransactionCase):
    """"Send now" and the scheduled sender in two transactions file once.

    Each ran in its own transaction, read the row as ``queued`` and went on to
    call the channel, so a click on *Send now* while the cron was sending the
    same submission filed the return twice. These tests use real, separate
    cursors on a committed row, because a single test transaction cannot show
    a race between two.
    """

    def setUp(self):
        super().setUp()
        self.sent = []
        sent = self.sent

        def fake_send(rec):
            sent.append(rec.id)
            rec._mark_delivered(external_ref="REF-%s" % rec.id)

        model_class = type(self.env["cssk.submission"])
        # pfs_manual refuses automated sending; give it a sender for the test.
        patcher = patch.object(
            model_class, "_channel_send_pfs_manual", fake_send, create=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.sub_id = self._committed_submission()

    def _committed_submission(self):
        with self.registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {"lang": "en_US"})
            company = env.company
            attachment = env["ir.attachment"].create({
                "name": "dph.xml", "datas": base64.b64encode(b"<DPH/>")})
            sub = env["cssk.submission"].create({
                "company_id": company.id,
                "res_model": "res.company",
                "res_id": company.id,
                "channel": "pfs_manual",
                "payload_attachment_id": attachment.id,
            })
            sub.write({"state": "queued", "next_retry": "2000-01-01 00:00:00"})
            sub_id, attachment_id = sub.id, attachment.id
        self.addCleanup(self._drop, sub_id, attachment_id)
        return sub_id

    def _drop(self, sub_id, attachment_id):
        with self.registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            env["cssk.submission"].browse(sub_id).exists().unlink()
            env["ir.attachment"].browse(attachment_id).exists().unlink()

    def _env(self, cr):
        return api.Environment(cr, SUPERUSER_ID, {"lang": "en_US"})

    def test_a_submission_being_sent_is_not_sent_again(self):
        with closing(self.registry.cursor()) as cr_cron, \
                closing(self.registry.cursor()) as cr_user:
            sub_cron = self._env(cr_cron)["cssk.submission"].browse(self.sub_id)
            # The cron has the row and is talking to the authority...
            self.assertTrue(sub_cron._lock_for_send())
            # ...when the user clicks Send now: refused, nothing filed.
            sub_user = self._env(cr_user)["cssk.submission"].browse(self.sub_id)
            self.assertEqual(sub_user.state, "queued")
            with self.assertRaisesRegex(UserError, "being sent right now"):
                sub_user.action_send()
            # A second cron run in that window skips it as well.
            self._env(cr_user)["cssk.submission"]._cron_send_queued()
            self.assertEqual(self.sent, [])
            # The holder finishes its send.
            sub_cron._attempt_send()
            cr_cron.commit()
            cr_user.rollback()
        self.assertEqual(self.sent, [self.sub_id])

    def test_a_submission_sent_meanwhile_is_not_sent_again(self):
        with closing(self.registry.cursor()) as cr_cron, \
                closing(self.registry.cursor()) as cr_user:
            # The cron read the row as queued (its snapshot)...
            due = self._env(cr_cron)["cssk.submission"].search(
                [("id", "=", self.sub_id), ("state", "=", "queued")])
            self.assertEqual(due.ids, [self.sub_id])
            # ...the user sends and commits first...
            self._env(cr_user)["cssk.submission"].browse(
                self.sub_id).action_send()
            cr_user.commit()
            self.assertEqual(self.sent, [self.sub_id])
            # ...and the cron, still seeing `queued`, must not file it again.
            self._env(cr_cron)["cssk.submission"]._cron_send_queued()
            cr_cron.rollback()
        self.assertEqual(self.sent, [self.sub_id])
        with closing(self.registry.cursor()) as cr:
            sub = self._env(cr)["cssk.submission"].browse(self.sub_id)
            self.assertEqual(sub.state, "delivered")

    def test_send_now_on_a_batch_skips_the_one_being_sent(self):
        """Raising for the locked one would roll back the record of the
        filings already made in the same click; it is skipped instead."""
        other_id = self._committed_submission()
        with closing(self.registry.cursor()) as cr_cron, \
                closing(self.registry.cursor()) as cr_user:
            self.assertTrue(self._env(cr_cron)["cssk.submission"].browse(
                self.sub_id)._lock_for_send())
            self._env(cr_user)["cssk.submission"].browse(
                [other_id, self.sub_id]).action_send()
            self.assertEqual(self.sent, [other_id])
            cr_user.rollback()
            cr_cron.rollback()
