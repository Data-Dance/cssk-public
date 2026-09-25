# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""Sending a payment file to Fio, and surviving a lost answer.

Shared by ``account_payment_fio`` (OCA payment orders, Community) and
``account_payment_fio_batch`` (Enterprise batch payments), so the dangerous
part exists once.

The danger is not a rejected upload — that is visible and harmless. It is an
upload whose **answer was lost**: the bank may hold the batch, and a retry
would create a second one. If somebody then authorises both in internet
banking, every payment goes out twice. So a transport failure lands the record
in ``unknown`` and the only way out is a human saying what they saw in the
bank.
"""

import logging

from lxml import etree

from odoo import _, fields, models
from odoo.exceptions import UserError

from odoo.addons.account_fio_base.utils.client import (
    FioError,
    FioUploadUncertain,
    mask_token,
)
from odoo.addons.account_fio_base.utils.response import parse_import_response

_logger = logging.getLogger(__name__)

UPLOAD_STATES = [
    ("not_sent", "Not sent"),
    ("sent", "Sent to Fio"),
    ("unknown", "Unknown — check the bank"),
]


class FioUploadMixin(models.AbstractModel):
    _name = "fio.upload.mixin"
    _description = "Fio Payment Upload"

    fio_upload_state = fields.Selection(
        selection=UPLOAD_STATES,
        default="not_sent",
        readonly=True,
        copy=False,
        tracking=True,
        string="Fio Upload",
    )
    fio_id_instruction = fields.Char(
        string="Fio Batch Number",
        readonly=True,
        copy=False,
        help="The idInstruction Fio returned for the uploaded batch. It is the "
             "batch's number in internet banking, and is NOT the same number "
             "as the instruction id that later appears on statement lines.",
    )
    fio_uploaded_at = fields.Datetime(readonly=True, copy=False)
    fio_response = fields.Text(readonly=True, copy=False)

    # ------------------------------------------------------------------
    # to be provided by the concrete model
    # ------------------------------------------------------------------

    def _fio_journal(self):
        raise NotImplementedError

    def _fio_payload(self):
        """``(bytes, filename)`` of the file to upload."""
        raise NotImplementedError

    def _fio_can_upload(self):
        """Whether the record is in a state where sending makes sense."""
        return True

    # ------------------------------------------------------------------
    # transport
    # ------------------------------------------------------------------

    def _fio_checked_journal(self):
        """The bank journal whose Fio tokens this upload will use.

        The tokens live on the journal itself, so there is no separate
        connection record to be missing — only a journal that is not set, which
        is a different and much earlier mistake. A journal without a submit
        token is caught by ``_fio_token('write')``, which names the exact right
        to ask Fio for.
        """
        self.ensure_one()
        journal = self._fio_journal()
        if not journal:
            raise UserError(_(
                "This record has no bank journal, so there is nothing to tell "
                "Fio which account the money leaves."
            ))
        return journal

    @staticmethod
    def _fio_sniff_type(payload):
        """Pick the ``type`` parameter from the file itself.

        This is what lets one button serve every exporter: Fio also accepts the
        ABO file ``account_abo`` produces and the pain.001 the SEPA/ISO 20022
        exporters produce, so those become sendable without a line of new
        format code.
        """
        head = payload[:400].lstrip()
        if head.startswith(b"<"):
            try:
                root = etree.fromstring(payload, parser=etree.XMLParser(
                    resolve_entities=False, no_network=True, load_dtd=False,
                ))
            except etree.XMLSyntaxError:
                raise UserError(_("The payment file is not valid XML.")) from None
            namespace = etree.QName(root).namespace or ""
            if "pain.001" in namespace:
                return "pain001_xml"
            if "pain.008" in namespace:
                return "pain008_xml"
            if etree.QName(root).localname == "Import":
                return "xml"
            raise UserError(_(
                "Fio does not accept this file: its root element is <%(tag)s>. "
                "Expected Fio's own <Import>, a pain.001 or a pain.008.",
                tag=etree.QName(root).localname,
            ))
        if head[:4] == b"UHL1":
            return "abo"
        raise UserError(_(
            "Cannot tell what format the payment file is in, so Fio cannot be "
            "told either."
        ))

    def action_fio_upload(self):
        """Send the generated file to Fio."""
        self.ensure_one()
        if self.fio_upload_state == "sent":
            raise UserError(_(
                "This was already sent to Fio as batch %(batch)s. Sending it "
                "again would create a second batch, and authorising both in "
                "internet banking would pay everything twice.",
                batch=self.fio_id_instruction or "?",
            ))
        if self.fio_upload_state == "unknown":
            raise UserError(_(
                "The previous upload's answer was lost, so nobody knows whether "
                "Fio holds this batch. Check internet banking for an "
                "unauthorised batch and record what you found — there is a "
                "button for each answer — before sending anything."
            ))
        if not self._fio_can_upload():
            raise UserError(_("This record is not ready to be sent to Fio."))

        journal = self._fio_checked_journal()
        payload, filename = self._fio_payload()
        if not payload:
            raise UserError(_("There is no payment file to send."))
        order_type = self._fio_sniff_type(payload)

        # From here on, everything that happens is RECORDED rather than raised.
        # A ``UserError`` rolls the transaction back, which would throw away
        # the very state that says the batch might already be at the bank — so
        # the outcome is written, posted to the chatter, and handed back as a
        # notification. Only the pre-flight refusals above raise, and they
        # write nothing.
        try:
            raw = journal._fio_call(
                "import_orders", payload, order_type, filename,
                kind="write", interactive=True,
            )
        except FioUploadUncertain as exception:
            # Masked again here, though FioClient already masked it when it
            # built the exception. Belt and braces, because all three sinks
            # below are durable or public: ``fio_response`` is stored on the
            # record, the chatter is readable by every follower, and the
            # notification is on screen — and the guarantee otherwise rests on
            # this ``except`` clause staying narrower than ``Exception``, which
            # nothing enforces.
            #
            # Note ``import_orders`` posts the submit token in the request BODY
            # and its URL carries no token, so this is in fact the sink least
            # able to leak one. The read endpoints are the ones that put the
            # token in the URL path.
            safe = mask_token(str(exception), journal.sudo().fio_token_write)
            # Deliberately NOT "not_sent": the batch may exist.
            self.sudo().write({
                "fio_upload_state": "unknown",
                "fio_uploaded_at": fields.Datetime.now(),
                "fio_response": safe,
            })
            self._fio_log(_(
                "Upload to Fio ended without an answer: %(error)s<br/><br/>"
                "The batch may or may not exist in the bank. Check internet "
                "banking before sending again.", error=safe,
            ))
            return self._fio_alert("danger", safe)
        except FioError as exception:
            # Nothing left the process, so nothing to record — raising here is
            # safe and keeps the message in front of the user.
            raise UserError(
                mask_token(str(exception), journal.sudo().fio_token_write)
            ) from None

        result = parse_import_response(raw)
        self.sudo().write({
            "fio_response": raw.decode("utf-8", "replace"),
            "fio_uploaded_at": fields.Datetime.now(),
            "fio_upload_state": "sent" if result.accepted else "not_sent",
            "fio_id_instruction": result.id_instruction if result.accepted else False,
        })
        self._fio_log(self._fio_result_body(result))
        if not result.accepted:
            return self._fio_alert("danger", "\n".join(
                [result.summary] + self._fio_message_lines(result)
            ))
        return self._fio_notify(result)

    def _fio_alert(self, kind, message):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {"type": kind, "message": message, "sticky": True},
        }

    def _fio_message_lines(self, result):
        return [
            "%s%s%s" % (
                "#%s " % message.order if message.order else "",
                "[%s] " % message.status if message.status else "",
                message.text,
            )
            for message in result.messages if message.text
        ]

    def _fio_result_body(self, result):
        parts = [result.summary]
        parts.extend(self._fio_message_lines(result))
        return "<br/>".join(parts)

    def _fio_notify(self, result):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "warning" if result.messages else "success",
                "message": result.summary,
                "sticky": True,
            },
        }

    def _fio_log(self, body):
        if hasattr(self, "message_post"):
            self.message_post(body=body)
        else:
            _logger.info("Fio upload on %s: %s", self.display_name, body)

    # ------------------------------------------------------------------
    # resolving the unknown state — a human has looked in the bank
    # ------------------------------------------------------------------

    def action_fio_confirm_sent(self):
        """The operator found the batch in internet banking."""
        self.ensure_one()
        self.sudo().write({"fio_upload_state": "sent"})
        self._fio_log(_(
            "Confirmed by %(user)s: the batch IS in Fio internet banking and "
            "must not be sent again.", user=self.env.user.display_name,
        ))

    def action_fio_confirm_not_sent(self):
        """The operator did not find the batch; sending again is safe."""
        self.ensure_one()
        self.sudo().write({
            "fio_upload_state": "not_sent",
            "fio_id_instruction": False,
        })
        self._fio_log(_(
            "Confirmed by %(user)s: the batch is NOT in Fio internet banking, "
            "so it can be sent again.", user=self.env.user.display_name,
        ))
