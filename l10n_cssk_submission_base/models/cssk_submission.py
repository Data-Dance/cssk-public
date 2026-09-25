# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""One delivery attempt-set of one statutory payload through one channel.

This is the *delivery* half of filing. The *retention* half already exists:
``cssk.statutory.submission.mixin`` (l10n_cssk_core) freezes the exported XML as
the filed copy, stamps date and reference, and keeps every filed copy in
``filed_history_ids``. Nothing here duplicates that — a submission POINTS AT the
statement's attachment rather than taking its own copy.

What this model adds is everything that happens after "we produced the XML":
which channel carried it, whether it arrived, what the authority said back, and
what to do when it did not arrive.

Two states people conflate, kept apart deliberately:

``delivered``
    The CHANNEL confirmed it took the payload — a PFS potvrdenka recorded, an
    SkTalk ``ReceiveResult=0``. It says the transport worked.
``accepted``
    The AUTHORITY accepted the filing — an eDesk doručenka, an FS potvrdenie.
    It says the filing counts.

A channel that cannot observe acceptance stops at ``delivered`` and reports so
via ``_channel_observes_acceptance``, rather than pretending. Telling an
accountant a filing is "accepted" when only the gateway acknowledged it is the
kind of thing that surfaces during a daňová kontrola, which is far too late.
"""

import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class CsskSubmissionRetryable(Exception):
    """Transport failed in a way that may succeed later (5xx, timeout, 429).

    Raised by ``_channel_send``. The submission goes back to ``queued`` with a
    backed-off ``next_retry`` until the channel's attempt limit is reached.
    """


class CsskSubmissionFatal(Exception):
    """The payload or configuration is wrong; retrying cannot help.

    Raised by ``_channel_send`` or ``_channel_validate``. The submission goes to
    ``failed`` immediately and raises an activity on the responsible user.
    """


# Backoff in minutes, indexed by attempt number. Deliberately short at the start
# (a gateway hiccup usually clears in seconds) and capped well inside a filing
# day, because a submission that keeps retrying past the deadline is worse than
# one that fails loudly in time for a human to file by hand.
RETRY_BACKOFF_MINUTES = [1, 5, 15, 60, 180]


class CsskSubmission(models.Model):
    _name = "cssk.submission"
    _description = "Statutory Submission"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"
    _rec_name = "name"

    name = fields.Char(
        required=True, copy=False, readonly=True, default=lambda s: _("New"),
    )
    company_id = fields.Many2one(
        "res.company", required=True, index=True,
        default=lambda s: s.env.company,
    )

    # -- what is being filed ------------------------------------------------
    # res_model/res_id rather than a Reference field: the statement models live
    # in modules this one does not depend on, and a Reference selection would
    # have to enumerate them.
    res_model = fields.Char(
        string="Statement model", required=True, readonly=True, index=True,
    )
    res_id = fields.Many2oneReference(
        string="Statement", model_field="res_model", required=True,
        readonly=True, index=True,
    )
    statement_display = fields.Char(
        compute="_compute_statement_display", string="Filing",
    )
    payload_attachment_id = fields.Many2one(
        "ir.attachment", string="Filed payload", readonly=True, copy=False,
        help="The XML that was filed. Points at the statement's own filed copy "
             "rather than duplicating it.",
    )
    sealed_attachment_id = fields.Many2one(
        "ir.attachment", string="Sealed payload", readonly=True, copy=False,
        help="Signed/sealed container (ASiC-E), where the channel requires one.",
    )

    # -- how ----------------------------------------------------------------
    channel = fields.Selection(
        selection="_selection_channel", required=True, tracking=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("queued", "Queued"),
            ("sending", "Sending"),
            ("delivered", "Delivered"),
            ("accepted", "Accepted"),
            ("rejected", "Rejected"),
            ("failed", "Failed"),
            ("cancelled", "Cancelled"),
        ],
        default="draft", required=True, tracking=True, index=True,
    )

    # -- correlation --------------------------------------------------------
    message_id = fields.Char(
        copy=False, index=True,
        help="Our identifier for this message, as sent to the channel.",
    )
    correlation_id = fields.Char(
        copy=False, index=True,
        help="Key the authority's later receipt is matched on.",
    )
    external_ref = fields.Char(
        string="Authority reference", copy=False, tracking=True,
        help="Podacie číslo / message reference assigned by the authority.",
    )

    sent_date = fields.Datetime(readonly=True, copy=False, tracking=True)
    delivered_date = fields.Datetime(readonly=True, copy=False, tracking=True)
    accepted_date = fields.Datetime(readonly=True, copy=False, tracking=True)

    # -- retry --------------------------------------------------------------
    attempt_count = fields.Integer(default=0, readonly=True, copy=False)
    last_error = fields.Text(readonly=True, copy=False)
    next_retry = fields.Datetime(readonly=True, copy=False, index=True)

    # -- what came back -----------------------------------------------------
    receipt_attachment_ids = fields.Many2many(
        "ir.attachment", "cssk_submission_receipt_rel",
        "submission_id", "attachment_id",
        string="Receipts", copy=False,
        help="Potvrdenky and doručenky. These are the proof the filing was made "
             "and accepted, so they are kept here rather than left with the "
             "channel provider.",
    )
    evidence_user_id = fields.Many2one(
        "res.users", string="Attested by", readonly=True, copy=False,
        help="Who confirmed a manual filing actually took place.",
    )

    _check_res = models.Constraint(
        "CHECK (res_id > 0)",
        "A submission must point at a statement.",
    )

    # ------------------------------------------------------------------
    # channels
    # ------------------------------------------------------------------

    @api.model
    def _get_channels(self):
        """Channels this database can file through.

        Transport modules extend this. Keep the codes stable — they are stored
        on every historical submission.
        """
        return [("pfs_manual", _("PFS portal — filed by hand"))]

    @api.model
    def _selection_channel(self):
        return self._get_channels()

    def _channel_method(self, verb):
        """Resolve ``_channel_<verb>_<channel>``, or None if unimplemented.

        Same dispatch shape as the section resolver in l10n_cssk_kv_kh_base.
        """
        self.ensure_one()
        return getattr(self, f"_channel_{verb}_{self.channel}", None)

    def _channel_observes_acceptance(self):
        """Whether this channel can ever reach ``accepted``.

        A channel that only knows the payload was taken must stop at
        ``delivered``; the UI reads this to avoid promising more than it knows.
        """
        self.ensure_one()
        return bool(self._channel_method("poll"))

    # ------------------------------------------------------------------
    # lifecycle
    # ------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "cssk.submission"
                ) or _("New")
        return super().create(vals_list)

    def _compute_statement_display(self):
        for rec in self:
            rec.statement_display = False
            if not rec.res_model or not rec.res_id:
                continue
            if rec.res_model not in self.env:
                rec.statement_display = f"{rec.res_model},{rec.res_id}"
                continue
            statement = self.env[rec.res_model].browse(rec.res_id).exists()
            rec.statement_display = statement.display_name if statement else False

    def statement(self):
        """The source statement, or an empty recordset if it is gone."""
        self.ensure_one()
        if not self.res_model or self.res_model not in self.env:
            return self.env["cssk.submission"].browse()
        return self.env[self.res_model].browse(self.res_id).exists()

    def action_validate(self):
        """Preflight. Raises rather than returning a verdict, so the UI shows why."""
        for rec in self:
            if not rec.payload_attachment_id:
                raise UserError(_(
                    "%(name)s has no filed payload. Export and submit the "
                    "statement first — a submission carries the statement's "
                    "filed copy, it does not produce one.", name=rec.display_name,
                ))
            method = rec._channel_method("validate")
            if method:
                method()
        return True

    def action_queue(self):
        """Hand the submission to the sender."""
        self.action_validate()
        for rec in self:
            if rec.state not in ("draft", "failed"):
                raise UserError(_(
                    "%(name)s is %(state)s and cannot be queued.",
                    name=rec.display_name,
                    state=dict(rec._fields["state"].selection).get(rec.state),
                ))
            rec.write({"state": "queued", "next_retry": fields.Datetime.now(),
                       "last_error": False})
            rec.message_post(body=_("Queued for %(channel)s.", channel=rec.channel))
        return True

    def action_send(self):
        """Attempt delivery now. Safe to call repeatedly; the cron uses it."""
        for rec in self:
            if rec.state not in ("queued", "sending"):
                continue
            rec._attempt_send()
        return True

    def _attempt_send(self):
        self.ensure_one()
        method = self._channel_method("send")
        if not method:
            raise UserError(_(
                "Channel %(channel)s has no sender installed.",
                channel=self.channel,
            ))
        self.write({"state": "sending",
                    "attempt_count": self.attempt_count + 1})
        try:
            method()
        except CsskSubmissionRetryable as exc:
            self._reschedule(str(exc))
        except CsskSubmissionFatal as exc:
            self._fail(str(exc))
        except Exception as exc:  # noqa: BLE001 - an unclassified error is retryable
            _logger.exception("cssk.submission %s: unclassified send error", self.id)
            self._reschedule(str(exc))

    def _reschedule(self, error):
        """Back off, or give up once the channel's attempts are exhausted."""
        self.ensure_one()
        # attempt_count is 1 after the first failure, so the last usable
        # backoff step is reached when it equals len(); giving up at >= would
        # discard the final step and retry one time fewer than configured.
        if self.attempt_count > len(RETRY_BACKOFF_MINUTES):
            return self._fail(_(
                "Giving up after %(n)s attempts. Last error: %(err)s",
                n=self.attempt_count, err=error,
            ))
        delay = RETRY_BACKOFF_MINUTES[self.attempt_count - 1]
        self.write({
            "state": "queued",
            "last_error": error,
            "next_retry": fields.Datetime.now() + timedelta(minutes=delay),
        })
        self.message_post(body=_(
            "Attempt %(n)s failed, retrying in %(delay)s min: %(err)s",
            n=self.attempt_count, delay=delay, err=error,
        ))

    def _fail(self, error):
        self.ensure_one()
        self.write({"state": "failed", "last_error": error, "next_retry": False})
        self.message_post(body=_("Failed: %(err)s", err=error))
        self._raise_activity(_(
            "Filing %(name)s could not be sent: %(err)s",
            name=self.display_name, err=error,
        ))

    def _raise_activity(self, note):
        """Put a failed filing in front of a person, not only in a log."""
        self.ensure_one()
        statement = self.statement()
        target = statement if statement and hasattr(statement, "activity_schedule") else self
        user = self.create_uid or self.env.user
        target.activity_schedule(
            "mail.mail_activity_data_todo", user_id=user.id, note=note,
        )

    def _mark_delivered(self, external_ref=None, receipts=None):
        """Called by a channel once the transport has confirmed receipt."""
        self.ensure_one()
        vals = {"state": "delivered", "delivered_date": fields.Datetime.now(),
                "last_error": False, "next_retry": False}
        if not self.sent_date:
            vals["sent_date"] = fields.Datetime.now()
        if external_ref:
            vals["external_ref"] = external_ref
        self.write(vals)
        if receipts:
            self.receipt_attachment_ids = [(4, a.id) for a in receipts]
        self.message_post(body=_("Delivered to the channel."))

    def _mark_accepted(self, external_ref=None, receipts=None):
        """Called once the AUTHORITY has accepted — not merely received."""
        self.ensure_one()
        vals = {"state": "accepted", "accepted_date": fields.Datetime.now()}
        if external_ref:
            vals["external_ref"] = external_ref
        if not self.delivered_date:
            vals["delivered_date"] = fields.Datetime.now()
        self.write(vals)
        if receipts:
            self.receipt_attachment_ids = [(4, a.id) for a in receipts]
        self.message_post(body=_("Accepted by the authority."))

    def action_cancel(self):
        for rec in self:
            if rec.state in ("accepted", "delivered"):
                raise UserError(_(
                    "%(name)s has already reached the authority and cannot be "
                    "cancelled. File a correction instead.", name=rec.display_name,
                ))
            rec.write({"state": "cancelled", "next_retry": False})
            rec.message_post(body=_("Cancelled."))
        return True

    # ------------------------------------------------------------------
    # cron
    # ------------------------------------------------------------------

    @api.model
    def _cron_send_queued(self, limit=50):
        """Send what is due. The fallback when queue_job is not installed."""
        due = self.search([
            ("state", "=", "queued"),
            ("next_retry", "<=", fields.Datetime.now()),
        ], limit=limit, order="next_retry asc")
        for submission in due:
            # A savepoint rather than a commit: one bad filing must not poison
            # the batch, but committing mid-cron is forbidden under test and
            # buys little here. Protection against a double-send after a hard
            # crash belongs to the channel, keyed on message_id — a commit
            # would not provide it either.
            try:
                with self.env.cr.savepoint():
                    submission._attempt_send()
            except Exception:  # noqa: BLE001
                _logger.exception(
                    "cssk.submission %s: send aborted", submission.id
                )
        return True

    @api.model
    def _cron_poll_delivered(self, limit=50):
        """Advance delivered → accepted for channels that can observe it."""
        pending = self.search([("state", "=", "delivered")], limit=limit)
        for submission in pending:
            method = submission._channel_method("poll")
            if not method:
                continue
            try:
                with self.env.cr.savepoint():
                    method()
            except Exception:  # noqa: BLE001
                _logger.exception(
                    "cssk.submission %s: poll failed", submission.id
                )
        return True

    # ------------------------------------------------------------------
    # channel: pfs_manual
    # ------------------------------------------------------------------
    # The accountant files on the portal themselves and attests it here. There
    # is no transport to fail, so this channel never queues — but it does record
    # WHO filed and WHEN, and it holds the potvrdenka they downloaded. That is
    # the whole point: without it the evidence lives in somebody's inbox.

    def _channel_validate_pfs_manual(self):
        self.ensure_one()
        return True

    def _channel_send_pfs_manual(self):
        self.ensure_one()
        raise CsskSubmissionFatal(_(
            "A filing on the PFS portal is made by a person, not by this "
            "server. Use 'Attest filing' once it has been submitted."
        ))

    def action_attest_manual(self):
        """Record that a human filed this on the portal, and by whom."""
        for rec in self:
            if rec.channel != "pfs_manual":
                raise UserError(_(
                    "%(name)s is not a manual filing.", name=rec.display_name,
                ))
            if rec.state in ("delivered", "accepted"):
                raise UserError(_(
                    "%(name)s is already attested.", name=rec.display_name,
                ))
            rec.evidence_user_id = self.env.user
            rec._mark_delivered()
            rec.message_post(body=_(
                "Attested as filed on the PFS portal by %(user)s.",
                user=self.env.user.display_name,
            ))
        return True

    @api.constrains("res_model")
    def _check_res_model(self):
        for rec in self:
            if rec.res_model and rec.res_model not in self.env:
                raise ValidationError(_(
                    "Unknown model %(model)s.", model=rec.res_model,
                ))
