# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.l10n_cssk_submission_base.models.cssk_submission import (
    RETRY_BACKOFF_MINUTES,
    CsskSubmissionFatal,
    CsskSubmissionRetryable,
)


class TestSubmissionBase(TransactionCase):
    """Smoke: the framework loads and the manual channel is registered."""

    def test_models_load(self):
        for model in ("cssk.submission", "cssk.submittable.mixin"):
            self.assertIn(model, self.env)

    def test_pfs_manual_channel_registered(self):
        channels = dict(self.env["cssk.submission"]._get_channels())
        self.assertIn("pfs_manual", channels)


@tagged("post_install", "-at_install")
class TestSubmissionLifecycle(TransactionCase):
    """The delivery state machine, its retry behaviour and its guards."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.attachment = cls.env["ir.attachment"].create({
            "name": "dph.xml",
            "datas": base64.b64encode(b"<DPH/>"),
        })

    def _submission(self, channel="pfs_manual", **vals):
        # res_model/res_id point at a real record so the constraint and the
        # display compute have something to resolve; the company itself is a
        # convenient stand-in for a statement in framework-level tests.
        return self.env["cssk.submission"].create({
            "company_id": self.company.id,
            "res_model": "res.company",
            "res_id": self.company.id,
            "channel": channel,
            "payload_attachment_id": self.attachment.id,
            **vals,
        })

    # -- naming and validation -------------------------------------------

    def test_sequence_assigns_name(self):
        sub = self._submission()
        self.assertNotEqual(sub.name, "New")
        self.assertTrue(sub.name.startswith("SUB/"))

    def test_validate_requires_payload(self):
        sub = self._submission()
        sub.payload_attachment_id = False
        with self.assertRaises(UserError):
            sub.action_validate()

    def test_unknown_model_rejected(self):
        with self.assertRaises(Exception):
            self._submission(res_model="no.such.model")

    # -- the manual channel ----------------------------------------------

    def test_manual_attest_records_who_and_when(self):
        sub = self._submission()
        sub.action_attest_manual()
        self.assertEqual(sub.state, "delivered")
        self.assertEqual(sub.evidence_user_id, self.env.user)
        self.assertTrue(sub.delivered_date)
        # It stops at delivered: nobody observed the authority accepting it.
        self.assertFalse(sub.accepted_date)

    def test_manual_attest_is_not_repeatable(self):
        sub = self._submission()
        sub.action_attest_manual()
        with self.assertRaises(UserError):
            sub.action_attest_manual()

    def test_manual_channel_refuses_automated_send(self):
        """A person files on the portal; the server must not claim it did."""
        sub = self._submission()
        sub.write({"state": "queued"})
        sub._attempt_send()
        self.assertEqual(sub.state, "failed")
        self.assertIn("by a person", sub.last_error)

    def test_manual_channel_does_not_observe_acceptance(self):
        self.assertFalse(self._submission()._channel_observes_acceptance())

    # -- retry ------------------------------------------------------------

    def test_retryable_backs_off_then_gives_up(self):
        sub = self._submission()

        def boom(self_):
            raise CsskSubmissionRetryable("gateway 503")

        patched = type(sub)._channel_send_pfs_manual
        type(sub)._channel_send_pfs_manual = boom
        try:
            sub.write({"state": "queued"})
            for expected in RETRY_BACKOFF_MINUTES:
                before = fields.Datetime.now()
                sub._attempt_send()
                self.assertEqual(sub.state, "queued")
                self.assertGreaterEqual(
                    sub.next_retry, before + timedelta(minutes=expected - 1),
                )
            # One attempt past the last backoff step and it stops trying.
            sub._attempt_send()
            self.assertEqual(sub.state, "failed")
            self.assertFalse(sub.next_retry)
        finally:
            type(sub)._channel_send_pfs_manual = patched

    def test_fatal_fails_immediately(self):
        sub = self._submission()

        def boom(self_):
            raise CsskSubmissionFatal("malformed payload")

        patched = type(sub)._channel_send_pfs_manual
        type(sub)._channel_send_pfs_manual = boom
        try:
            sub.write({"state": "queued"})
            sub._attempt_send()
            self.assertEqual(sub.state, "failed")
            self.assertEqual(sub.attempt_count, 1)
            self.assertIn("malformed", sub.last_error)
        finally:
            type(sub)._channel_send_pfs_manual = patched

    def test_unclassified_error_is_treated_as_retryable(self):
        """An unexpected exception must not burn the filing on attempt one."""
        sub = self._submission()

        def boom(self_):
            raise ValueError("something nobody anticipated")

        patched = type(sub)._channel_send_pfs_manual
        type(sub)._channel_send_pfs_manual = boom
        try:
            sub.write({"state": "queued"})
            sub._attempt_send()
            self.assertEqual(sub.state, "queued")
        finally:
            type(sub)._channel_send_pfs_manual = patched

    def test_failure_raises_an_activity(self):
        sub = self._submission()
        sub.write({"state": "queued"})
        sub._attempt_send()
        self.assertEqual(sub.state, "failed")
        activities = self.env["mail.activity"].search([
            ("res_model", "=", "cssk.submission"), ("res_id", "=", sub.id),
        ])
        self.assertTrue(activities, "a failed filing must reach a person")

    # -- delivered vs accepted -------------------------------------------

    def test_delivered_is_not_accepted(self):
        sub = self._submission()
        sub._mark_delivered(external_ref="PFS-123")
        self.assertEqual(sub.state, "delivered")
        self.assertEqual(sub.external_ref, "PFS-123")
        self.assertFalse(sub.accepted_date)

    def test_accepted_backfills_delivery(self):
        """A channel may learn of acceptance without having seen delivery."""
        sub = self._submission()
        sub._mark_accepted(external_ref="FS-9")
        self.assertEqual(sub.state, "accepted")
        self.assertTrue(sub.delivered_date)
        self.assertTrue(sub.accepted_date)

    def test_receipts_are_retained(self):
        sub = self._submission()
        receipt = self.env["ir.attachment"].create({
            "name": "potvrdenka.pdf",
            "datas": base64.b64encode(b"%PDF"),
        })
        sub._mark_accepted(receipts=receipt)
        self.assertIn(receipt, sub.receipt_attachment_ids)

    # -- guards -----------------------------------------------------------

    def test_cannot_cancel_once_it_reached_the_authority(self):
        for state in ("delivered", "accepted"):
            sub = self._submission()
            sub.write({"state": state})
            with self.assertRaises(UserError):
                sub.action_cancel()

    def test_cancel_before_delivery_is_allowed(self):
        sub = self._submission()
        sub.action_cancel()
        self.assertEqual(sub.state, "cancelled")

    def test_queue_rejects_a_delivered_submission(self):
        sub = self._submission()
        sub.write({"state": "delivered"})
        with self.assertRaises(UserError):
            sub.action_queue()

    # -- cron -------------------------------------------------------------

    def test_cron_only_picks_due_rows(self):
        due = self._submission()
        due.write({"state": "queued",
                   "next_retry": fields.Datetime.now() - timedelta(minutes=1)})
        later = self._submission()
        later.write({"state": "queued",
                     "next_retry": fields.Datetime.now() + timedelta(hours=2)})
        self.env["cssk.submission"]._cron_send_queued()
        # The due one was attempted (and failed, being a manual channel);
        # the future one was left alone.
        self.assertEqual(due.state, "failed")
        self.assertEqual(later.state, "queued")
        self.assertEqual(later.attempt_count, 0)


@tagged("post_install", "-at_install")
class TestSubmittableContract(TransactionCase):
    """Every model that inherits the mixin has to satisfy its contract.

    POST_INSTALL, and it has to be. A module's tests run immediately after that
    module loads, and everything inheriting this mixin depends on it — so those
    models do not exist in the registry yet. At `at_install` the sweep finds
    nothing and passes vacuously, which is the failure this test exists to
    prevent.

    Written as a sweep rather than five near-identical tests: it covers whatever
    is installed, and it catches the next statement someone wires in without
    reading the mixin. A statement that fails here would raise only when an
    accountant pressed the button, which is the worst place to find out.
    """

    def _submittables(self):
        """Installed models carrying the mixin, found by its own field.

        Reading `_inherit` misses models that pick the mixin up indirectly, and
        the field is what the mixin actually contributes — so this is both
        simpler and harder to fool.
        """
        out = []
        for name in self.env.registry:
            model = self.env[name]
            if model._abstract:
                continue          # the mixin itself carries the field too
            field = model._fields.get("submission_ids")
            if field is not None and field.comodel_name == "cssk.submission":
                out.append(name)
        return out

    def test_at_least_one_statement_is_wired(self):
        # Guards against the sweep silently passing because it found nothing.
        self.assertTrue(self._submittables(),
                        "no model inherits cssk.submittable.mixin — the sweep "
                        "below would pass vacuously")

    def test_every_submittable_can_be_filed(self):
        for name in self._submittables():
            model = self.env[name]
            with self.subTest(model=name):
                self.assertIn("company_id", model._fields,
                              "a submission is created with company_id")
                self.assertTrue(
                    hasattr(model, "_submission_payload_attachment"),
                    "must be able to say which attachment gets filed")
                if "state" in model._fields:
                    selection = model._fields["state"].selection
                    states = set(dict(selection or []))
                    ready = set(model.new({})._submission_ready_states())
                    self.assertTrue(
                        ready & states,
                        "%s gates filing on state in %s, none of which exists "
                        "in its own selection %s — the button would never "
                        "become available" % (name, sorted(ready), sorted(states)))

    def test_channels_resolve_for_every_submittable(self):
        for name in self._submittables():
            with self.subTest(model=name):
                # An in-memory record: _submission_channels ensures one, and a
                # statement may legitimately narrow the list per record.
                channels = dict(self.env[name].new({})._submission_channels())
                self.assertIn("pfs_manual", channels,
                              "the manual channel must always be offered — it "
                              "is what makes retention true before any "
                              "automated channel exists")
