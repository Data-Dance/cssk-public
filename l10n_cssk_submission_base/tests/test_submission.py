# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from datetime import timedelta
from unittest.mock import patch

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
        # Messages are asserted in English; a database with Slovak or Czech
        # loaded would otherwise hand them back translated.
        cls.env = cls.env(context=dict(cls.env.context, lang="en_US"))
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

    def test_unclassified_error_is_not_retried_by_default(self):
        """An unexpected exception can come from the code recording the
        authority's answer AFTER the filing was made; retrying it would file
        twice. It fails and puts the question in front of a person."""
        sub = self._submission()

        def boom(self_):
            raise ValueError("something nobody anticipated")

        patched = type(sub)._channel_send_pfs_manual
        type(sub)._channel_send_pfs_manual = boom
        try:
            sub.write({"state": "queued"})
            sub._attempt_send()
            self.assertEqual(sub.state, "failed")
            self.assertIn("outcome is unknown", sub.last_error)
            self.assertFalse(sub.next_retry)
        finally:
            type(sub)._channel_send_pfs_manual = patched

    def test_channel_may_declare_unclassified_errors_retryable(self):
        sub = self._submission()

        def boom(self_):
            raise ValueError("before anything left the server")

        cls = type(sub)
        patched = cls._channel_send_pfs_manual
        cls._channel_send_pfs_manual = boom
        cls._channel_retry_unclassified_pfs_manual = lambda self_: True
        try:
            sub.write({"state": "queued"})
            sub._attempt_send()
            self.assertEqual(sub.state, "queued")
        finally:
            cls._channel_send_pfs_manual = patched
            del cls._channel_retry_unclassified_pfs_manual

    def test_database_error_in_the_channel_leaves_a_usable_cursor(self):
        """A database error after the authority answered used to abort the
        whole transaction; the row went back to `queued` and was sent again."""
        sub = self._submission()

        def boom(self_):
            self_.env.cr.execute("SELECT no_such_column FROM res_company")

        patched = type(sub)._channel_send_pfs_manual
        type(sub)._channel_send_pfs_manual = boom
        try:
            sub.write({"state": "queued"})
            with self.assertLogs(level="ERROR"):
                sub._attempt_send()
            self.assertEqual(sub.state, "failed")
            self.assertIn("no_such_column", sub.last_error)
        finally:
            type(sub)._channel_send_pfs_manual = patched

    def test_cron_fails_an_aborted_send_instead_of_resending(self):
        sub = self._submission()
        sub.write({"state": "queued",
                   "next_retry": fields.Datetime.now() - timedelta(minutes=1)})

        def explode(self_):
            raise RuntimeError("worker died mid-send")

        with patch.object(type(sub), "_attempt_send", explode), \
                self.assertLogs(level="ERROR"):
            self.env["cssk.submission"]._cron_send_queued()
        self.assertEqual(sub.state, "failed")
        self.assertIn("worker died", sub.last_error)

    def test_manual_acceptance_needs_the_confirmation(self):
        sub = self._submission()
        sub.action_attest_manual()
        with self.assertRaises(UserError):
            sub.action_attest_accepted_manual()
        sub.receipt_attachment_ids = [(4, self.env["ir.attachment"].create({
            "name": "potvrdenie.pdf", "datas": base64.b64encode(b"%PDF")}).id)]
        sub.action_attest_accepted_manual()
        self.assertEqual(sub.state, "accepted")
        self.assertTrue(sub.accepted_date)

    def test_manual_acceptance_only_after_attesting_the_filing(self):
        sub = self._submission()
        with self.assertRaises(UserError):
            sub.action_attest_accepted_manual()

    def test_manual_channel_label_is_country_neutral(self):
        label = dict(self.env["cssk.submission"]._get_channels())["pfs_manual"]
        self.assertNotIn("PFS", label)

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

    def _companies_to_try(self):
        """The default company, plus a Czech and a Slovak one (created once)."""
        if not getattr(self, "_sweep_companies", None):
            companies = [self.env.company]
            for code in ("cz", "sk"):
                company = self.env["res.company"].create({
                    "name": "Submittable %s" % code.upper(),
                    "country_id": self.env.ref("base.%s" % code).id,
                })
                self.env.user.company_ids |= company
                companies.append(company)
            self._sweep_companies = companies
        return self._sweep_companies

    def _new_in_a_company_it_accepts(self, name):
        """An in-memory record of *name*, opened in a company it accepts.

        Payroll declarations refuse to open outside a company of their own
        country, so a sweep run from a company of another country tries a
        Czech and a Slovak company too.
        """
        for company in self._companies_to_try():
            try:
                record = self.env[name].with_company(company).new({})
                # Defaults are computed lazily; read one so a refusal raises here.
                record.company_id  # noqa: B018
                return record
            except UserError:
                continue
        self.fail("%s opens in no CZ, SK or default company" % name)

    def test_channels_resolve_for_every_submittable(self):
        for name in self._submittables():
            with self.subTest(model=name):
                # An in-memory record: _submission_channels ensures one, and a
                # statement may legitimately narrow the list per record.
                record = self._new_in_a_company_it_accepts(name)
                channels = dict(record._submission_channels())
                self.assertIn("pfs_manual", channels,
                              "the manual channel must always be offered — it "
                              "is what makes retention true before any "
                              "automated channel exists")


@tagged("post_install", "-at_install")
class TestSubmissionFollowsTheStatement(TransactionCase):
    """Payload and statement state kept in step, on a real statement.

    Needs a statement model carrying both mixins; ``cssk.vat.return``
    (l10n_cssk_vat_return_base) is the smallest one.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if "cssk.vat.return" not in cls.env:
            cls.skipTest(cls, "needs l10n_cssk_vat_return_base")
        cls.env = cls.env(context=dict(cls.env.context, lang="en_US"))
        cls.company = cls.env.company
        cls.company.vat = "SK2023456787"
        template = cls.env["ir.ui.view"].create({
            "name": "cssk submission follow test", "type": "qweb",
            "arch": "<t t-name='cssk_submission_follow_test'><DPH/></t>"})
        schema = (b'<?xml version="1.0" encoding="UTF-8"?>'
                  b'<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
                  b'<xs:element name="DPH"/></xs:schema>')
        cls.version = cls.env["cssk.vat.return.version"].create({
            "name": "FLW", "country_id": cls.env.ref("base.sk").id,
            "valid_from": "2025-01-01",
            "xml_template_ref_id": template.id, "xml_root_element": "DPH",
            "xml_schema_filename": "f.xsd",
            "xml_schema_data": base64.b64encode(schema),
            "statement_type_ids": [
                (0, 0, {"code": "R", "name": "Riadny", "fa_xml_value": "R"})],
        })

    def _exported_return(self):
        ret = self.env["cssk.vat.return"].create({
            "company_id": self.company.id, "version_id": self.version.id,
            "date_from": "2026-06-01", "date_to": "2026-06-30",
            "period_type": "month",
            "statement_type_id": self.version.statement_type_ids[0].id,
        })
        ret.action_compute_lines()
        ret.action_export_xml()
        return ret

    def _open(self, ret):
        action = ret.action_create_submission(channel="pfs_manual")
        return self.env["cssk.submission"].browse(action["res_id"])

    def _reexport(self, ret):
        ret.action_reset_to_draft()
        ret.action_compute_lines()
        ret.action_export_xml()

    def test_an_unsent_submission_follows_a_reexport(self):
        ret = self._exported_return()
        sub = self._open(ret)
        first = ret.xml_attachment_id
        self.assertEqual(sub.payload_attachment_id, first)
        self._reexport(ret)
        self.assertNotEqual(ret.xml_attachment_id, first)
        sub.action_attest_manual()
        self.assertEqual(sub.payload_attachment_id, ret.xml_attachment_id)

    def test_reexport_after_submit_files_the_new_xml(self):
        """submitted_attachment_id survives a reset on purpose, and was
        preferred — so the re-exported statement's submission carried the
        OLD filed XML."""
        ret = self._exported_return()
        ret.action_submit()
        sub = ret.submission_ids
        old = ret.submitted_attachment_id
        self._reexport(ret)
        sub.action_validate()
        self.assertEqual(sub.payload_attachment_id, ret.xml_attachment_id)
        self.assertNotEqual(sub.payload_attachment_id, old)

    def test_a_queued_payload_the_statement_dropped_is_not_sent(self):
        ret = self._exported_return()
        sub = self._open(ret)
        sub.write({"state": "queued"})
        self._reexport(ret)
        sub._attempt_send()
        self.assertEqual(sub.state, "failed")
        self.assertIn("exported again", sub.last_error)

    def test_filing_marks_the_statement_submitted(self):
        """A channel filing left the statement at `exported`: no filed copy
        frozen, no reference, still re-exportable."""
        ret = self._exported_return()
        sub = self._open(ret)
        sub._mark_delivered(external_ref="POD-123")
        self.assertEqual(ret.state, "submitted")
        self.assertEqual(ret.submitted_attachment_id, sub.payload_attachment_id)
        self.assertEqual(ret.submission_reference, "POD-123")
        self.assertEqual(len(ret.submission_ids), 1)

    def test_an_old_payload_does_not_stamp_a_new_export(self):
        ret = self._exported_return()
        sub = self._open(ret)
        sub.write({"state": "queued"})
        self._reexport(ret)
        sub._mark_delivered(external_ref="POD-OLD")
        self.assertEqual(ret.state, "exported")
        self.assertFalse(ret.submission_reference)
