# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The seam a statutory statement inherits to gain delivery tracking.

Deliberately thin, and deliberately NOT a replacement for
``cssk.statutory.submission.mixin`` in ``l10n_cssk_core``. The two are different
concerns and a statement wants both:

``cssk.statutory.submission.mixin``   retention — the filed copy is durable
``cssk.submittable.mixin``            delivery — did it arrive, and what came back

The retention mixin already owns ``submitted_attachment_id``, ``submitted_date``,
``submission_reference`` and ``filed_history_ids``. Nothing here duplicates any
of them; a submission points at the filed copy the retention mixin froze.
"""

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class CsskSubmittableMixin(models.AbstractModel):
    _name = "cssk.submittable.mixin"
    _description = "Statement that can be filed through a channel"

    submission_ids = fields.One2many(
        "cssk.submission", "res_id", string="Submissions",
        domain=lambda self: [("res_model", "=", self._name)],
    )
    active_submission_id = fields.Many2one(
        "cssk.submission", compute="_compute_active_submission",
        string="Current submission", store=True,
    )
    # STORED, and active_submission_id must be stored too. A stored related
    # whose path runs through an unstored compute cannot be turned into SQL —
    # Odoo raises "Cannot convert ... to SQL because it is not stored" on every
    # write to cssk.submission, not on the statement, so the error surfaces
    # nowhere near the mistake.
    submission_state = fields.Selection(
        related="active_submission_id.state", string="Delivery",
        store=True, index=True,
    )

    @api.depends("submission_ids.state")
    def _compute_active_submission(self):
        """The submission that speaks for this statement.

        An accepted one wins over anything else — once the authority has taken
        it, later attempts are noise. Otherwise the most recent non-cancelled
        attempt, so a retry chain reads as one thing rather than a list.
        """
        for rec in self:
            live = rec.submission_ids.filtered(lambda s: s.state != "cancelled")
            accepted = live.filtered(lambda s: s.state == "accepted")
            rec.active_submission_id = accepted[:1] or live[:1]

    def write(self, vals):
        """Open a delivery the moment a filing is marked submitted.

        Retention and delivery were parallel and unconnected: `action_submit`
        froze the filed copy, and nothing opened a submission. So the evidence
        trail depended on somebody also remembering an optional second click,
        which means the retained-receipts claim was not reliably true.

        The submission is created in `draft` and asserts nothing — it is a place
        for the potvrdenka to land, and an un-attested one is exactly the
        "filed, no receipt held" state an audit wants to be able to find.

        Hooked on write rather than on `action_submit` because the two families
        reach `submitted` through different methods, and this catches both
        without either having to know about it.
        """
        result = super().write(vals)
        if vals.get("state") == "submitted":
            self._ensure_submission()
        return result

    def _ensure_submission(self):
        """Make sure a filing has somewhere to hold its receipts.

        Never raises. A statement must not become unsavable because evidence
        tracking could not start — that would trade a missing receipt for a
        blocked close, which is the worse failure.

        Two things make that promise true rather than merely stated, and it
        was not true when this was written:

        * ``sudo`` — opening the delivery is the SYSTEM's bookkeeping, not
          something the filer asked for. Marking a filing submitted is an
          accounting right; holding the statutory-submission groups is a
          separate one, and plenty of users have the first without the second.
          Reading ``submission_ids`` as such a user raised ``AccessError`` out
          of ``write`` and the statement could not be saved at all.
        * the whole body inside ``try`` — the read above raised *outside* the
          guard, so "never raises" covered only the ``create``.
        """
        Submission = self.env["cssk.submission"].sudo()
        for rec in self:
            try:
                if rec.sudo().submission_ids.filtered(
                        lambda s: s.state != "cancelled"):
                    continue
                attachment = rec._submission_payload_attachment()
                if not attachment:
                    continue
                channels = dict(rec._submission_channels())
                channel = "pfs_manual" if "pfs_manual" in channels else (
                    next(iter(channels), None))
                if not channel:
                    continue
                Submission.create({
                    "company_id": rec.company_id.id,
                    "res_model": rec._name,
                    "res_id": rec.id,
                    "channel": channel,
                    "payload_attachment_id": attachment.id,
                })
            except Exception:            # noqa: BLE001 - see the docstring
                _logger.exception(
                    "could not open a submission for %s %s",
                    rec._name, rec.id)

    def _submission_ready_states(self):
        """States in which a filing may be opened.

        Overridable because the vocabulary is not shared: a statement says
        `exported` where a payroll declaration says `generated`, and both mean
        "the XML exists and is frozen". Hardcoding one tuple silently disabled
        the button for every model using the other word.
        """
        return ("exported", "submitted")

    def _submission_channels(self):
        """Channels valid for this statement. Override to narrow."""
        self.ensure_one()
        return self.env["cssk.submission"]._get_channels()

    def _submission_payload_attachment(self):
        """The attachment a submission should carry.

        The filed copy from the retention mixin, falling back to the exported
        XML for a statement that does not inherit it.
        """
        self.ensure_one()
        for fname in ("submitted_attachment_id", "xml_attachment_id"):
            if fname in self._fields and self[fname]:
                return self[fname]
        return self.env["ir.attachment"]

    def action_create_submission(self, channel=None):
        """Open a delivery for this statement.

        Gated on the statement having been submitted, because that is when the
        retention mixin freezes the filed copy — filing a payload that can still
        change would make the evidence trail meaningless.
        """
        self.ensure_one()
        ready = self._submission_ready_states()
        if "state" in self._fields and ready and self.state not in ready:
            raise UserError(_(
                "%(name)s is not exported yet. A submission carries the filed "
                "copy, so export and submit it first.", name=self.display_name,
            ))
        attachment = self._submission_payload_attachment()
        if not attachment:
            raise UserError(_(
                "%(name)s has no XML to file.", name=self.display_name,
            ))
        channels = dict(self._submission_channels())
        if channel and channel not in channels:
            raise UserError(_(
                "Channel %(channel)s is not available for this filing.",
                channel=channel,
            ))
        if not channel:
            if len(channels) != 1:
                return self._action_pick_channel(channels)
            channel = next(iter(channels))
        submission = self.env["cssk.submission"].create({
            "company_id": self.company_id.id,
            "res_model": self._name,
            "res_id": self.id,
            "channel": channel,
            "payload_attachment_id": attachment.id,
        })
        return {
            "type": "ir.actions.act_window",
            "res_model": "cssk.submission",
            "res_id": submission.id,
            "view_mode": "form",
        }

    def _action_pick_channel(self, channels):
        """More than one channel available — let the accountant choose.

        A list of this statement's submissions with the create dialog defaulted;
        a dedicated wizard would be a second way to say the same thing.
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("File %(name)s", name=self.display_name),
            "res_model": "cssk.submission",
            "view_mode": "list,form",
            "domain": [("res_model", "=", self._name), ("res_id", "=", self.id)],
            "context": {
                "default_res_model": self._name,
                "default_res_id": self.id,
                "default_company_id": self.company_id.id,
                "default_payload_attachment_id":
                    self._submission_payload_attachment().id,
            },
        }
