# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""EPO as a submission channel: check, file, and follow a Czech filing.

Two actions, deliberately separate:

* **Check with EPO** (``action_epo_check``) signs the filed XML and sends it in
  EPO's test mode, which runs every check — the signature, the structure, the
  content — and files nothing. The answer, EPO's list of errors, is stored on
  the submission. It never changes the submission's state, and the test flag
  is passed literally in that one method: there is no path from it to a
  filing.
* **Filing** is the ordinary queue → send of the submission framework. It
  signs and sends without the test flag, which files, and is refused unless
  the company has switched *Allow filing through EPO* on. The potvrzení EPO
  returns is kept as the receipt; ``epo_stav`` is then polled until the tax
  office has accepted or rejected the filing.

EPO's own caveat is repeated to the user rather than softened: its checks are
a subset of the tax office's, so a clean test is not a guarantee of
acceptance.
"""

import base64

from markupsafe import Markup, escape

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_cssk_submission_base.models.cssk_submission import (
    CsskSubmissionFatal,
    CsskSubmissionRetryable,
)

from ..lib import epo

CHANNEL = "cz_epo"
_MANAGER = "l10n_cssk_submission_base.group_cssk_submission_manager"


class CsskSubmission(models.Model):
    _inherit = "cssk.submission"

    epo_password = fields.Char(
        string="EPO heslo", copy=False, readonly=True, groups=_MANAGER,
        help="Password EPO issued with the podací číslo; asks for the state.")
    epo_transfer_id = fields.Char(
        string="EPO ID předání", copy=False, readonly=True,
        help="Set when EPO took a large filing for off-line processing and "
        "has not issued the podací číslo yet.")
    epo_check_date = fields.Datetime(string="Checked with EPO", readonly=True, copy=False)
    epo_check_result = fields.Selection(
        [("clean", "No errors"), ("warnings", "Warnings only"),
         ("errors", "Errors")],
        string="EPO check", readonly=True, copy=False)
    epo_check_summary = fields.Text(readonly=True, copy=False)
    epo_check_attachment_id = fields.Many2one(
        "ir.attachment", string="EPO check answer", readonly=True, copy=False)

    @api.model
    def _get_channels(self):
        return super()._get_channels() + [
            (CHANNEL, _("EPO — Finanční správa (signed, direct)"))]

    # ------------------------------------------------------------------
    def _epo_certificate(self):
        self.ensure_one()
        cert = self.company_id.l10n_cz_epo_certificate_id
        if not cert:
            raise UserError(_(
                "%(company)s has no EPO signing certificate. Set one in "
                "Accounting → Configuration → EPO certificates.",
                company=self.company_id.display_name))
        cert._check_usable()
        return cert

    def _epo_signed_payload(self):
        self.ensure_one()
        if not self.payload_attachment_id:
            raise UserError(_(
                "%(name)s has no filed payload to sign.", name=self.display_name))
        xml = base64.b64decode(self.payload_attachment_id.datas)
        key, cert, chain = self._epo_certificate()._signing_material()
        return epo.sign(xml, key, cert, chain)

    def _epo_attach(self, name, data, mimetype):
        self.ensure_one()
        return self.env["ir.attachment"].create({
            "name": name, "raw": data, "mimetype": mimetype,
            "res_model": self._name, "res_id": self.id,
        })

    @staticmethod
    def _epo_error_lines(errors):
        return "\n".join(
            "[%s %s] %s%s" % (
                err["type"], err["code"], err["text"],
                (" (%s)" % ", ".join(filter(None, (
                    err["section"], err["field"], err["row"] and
                    _("line %s") % err["row"])))) if (
                        err["section"] or err["field"] or err["row"]) else "")
            for err in errors)

    # ------------------------------------------------------------------
    # Check (test mode) — never files
    # ------------------------------------------------------------------
    def action_epo_check(self):
        self._epo_check_rights()
        for rec in self:
            if rec.channel != CHANNEL:
                raise UserError(_(
                    "%(name)s is not an EPO submission.", name=rec.display_name))
            signed = rec._epo_signed_payload()
            try:
                answer = epo.submit(signed, test=True)
            except epo.EpoError as exc:
                raise UserError(str(exc)) from exc
            if answer["kind"] != "errors":
                # Test mode answers with an error list, always. Anything else
                # would mean the call was not a test, which must not pass
                # silently.
                raise UserError(_(
                    "EPO answered a check with %(kind)s instead of a check "
                    "result; nothing is recorded.", kind=answer["kind"]))
            real = [e for e in answer["errors"] if e["code"] != "TEST_REZIM"]
            result = ("clean" if answer["test_clean"]
                      else "errors" if answer["blocking"] else "warnings")
            attachment = rec._epo_attach(
                "EPO-check-%s.xml" % rec.name, answer["xml"], "application/xml")
            rec.write({
                "epo_check_date": fields.Datetime.now(),
                "epo_check_result": result,
                "epo_check_summary": rec._epo_error_lines(real) or False,
                "epo_check_attachment_id": attachment.id,
            })
            headline = {
                "clean": _("EPO found no errors."),
                "warnings": _("EPO found warnings only."),
                "errors": _("EPO found errors — the filing would be refused."),
            }[result]
            body = Markup("<p>%s</p><p><em>%s</em></p>") % (
                headline,
                _("EPO's checks are a subset of the tax office's; a clean "
                  "result is not a guarantee of acceptance."))
            if real:
                body += Markup("<pre>%s</pre>") % escape(rec._epo_error_lines(real))
            rec.message_post(body=body, attachment_ids=attachment.ids)
        return True

    # ------------------------------------------------------------------
    # Channel: validate / send / poll
    # ------------------------------------------------------------------
    def _epo_check_rights(self):
        """Only the group allowed to file may make EPO calls in the company's
        name — enforced here, not only by hiding buttons."""
        if not self.env.su and not self.env.user.has_group(_MANAGER):
            raise UserError(_(
                "Only users allowed to file statutory submissions may send "
                "them to EPO."))

    def _channel_validate_cz_epo(self):
        self.ensure_one()
        self._epo_check_rights()
        if self.company_id.account_fiscal_country_id.code != "CZ":
            raise UserError(_(
                "EPO files for Czech taxpayers; %(company)s does not file in "
                "Czechia.", company=self.company_id.display_name))
        self._epo_certificate()
        return True

    def _channel_send_cz_epo(self):
        self.ensure_one()
        if not self.company_id.l10n_cz_epo_allow_filing:
            raise CsskSubmissionFatal(_(
                "Filing through EPO is switched off for %(company)s: use "
                "'Check with EPO', or switch on 'Allow filing through EPO' "
                "on the company.", company=self.company_id.display_name))
        try:
            signed = self._epo_signed_payload()
        except UserError as exc:
            raise CsskSubmissionFatal(str(exc)) from exc
        self.sealed_attachment_id = self._epo_attach(
            "%s.p7s" % self.name, signed, "application/pkcs7-signature")
        try:
            answer = epo.submit(signed, test=False)
        except epo.EpoError as exc:
            if not exc.maybe_sent:
                raise CsskSubmissionRetryable(str(exc)) from exc
            # The request may have reached EPO and filed: sending it again
            # could file the return twice. Stop and let a person look.
            raise CsskSubmissionFatal(_(
                "The outcome of the filing is unknown (%(error)s). It may have "
                "been filed: check the filing in the EPO portal (MOJE daně) "
                "before sending it again.", error=exc)) from exc
        self.sent_date = fields.Datetime.now()
        kind = answer["kind"]
        if kind == "receipt":
            receipt = self._epo_attach(
                "potvrzeni-%s.p7s" % (answer["number"] or self.name),
                answer["raw"], "application/pkcs7-signature")
            self.sudo().epo_password = answer["password"]
            self._mark_delivered(external_ref=answer["number"], receipts=receipt)
            self.message_post(body=_(
                "Filed through EPO: podací číslo %(number)s, %(date)s.",
                number=answer["number"], date=answer["date"] or ""))
        elif kind == "offline":
            self.epo_transfer_id = answer["transfer_id"]
            self.sudo().epo_password = answer["password"]
            self._mark_delivered()
            self.message_post(body=_(
                "EPO took this large filing for off-line processing (ID "
                "předání %(id)s); the podací číslo follows.",
                id=answer["transfer_id"]))
        elif kind == "errors":
            attachment = self._epo_attach(
                "EPO-errors-%s.xml" % self.name, answer["xml"], "application/xml")
            self.message_post(attachment_ids=attachment.ids)
            raise CsskSubmissionFatal(_(
                "EPO refused the filing:\n%s",
                self._epo_error_lines(answer["errors"])))
        else:
            raise CsskSubmissionFatal(_(
                "EPO answered a filing with %s.", kind))

    def _channel_poll_cz_epo(self):
        self.ensure_one()
        password = self.sudo().epo_password
        if not password:
            return
        try:
            if self.epo_transfer_id and not self.external_ref:
                answer = epo.receipt(self.epo_transfer_id, password)
                if answer["kind"] == "receipt":
                    receipt = self._epo_attach(
                        "potvrzeni-%s.p7s" % answer["number"], answer["raw"],
                        "application/pkcs7-signature")
                    self.write({"external_ref": answer["number"],
                                "receipt_attachment_ids": [(4, receipt.id)]})
                    self.sudo().epo_password = answer["password"] or password
                return
            answer = epo.status(self.external_ref, password)
        except epo.EpoError:
            return  # try again on the next run
        if answer["kind"] != "status":
            return
        if answer["state"] == epo.STATE_ACCEPTED:
            self._mark_accepted()
        elif answer["state"] == epo.STATE_REJECTED:
            self.write({"state": "rejected", "next_retry": False})
            self.message_post(body=_(
                "The tax office rejected the filing (EPO state %s).",
                answer["state"]))
