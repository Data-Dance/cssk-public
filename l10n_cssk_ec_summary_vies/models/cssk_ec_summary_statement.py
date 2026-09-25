# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class CSSKEcSummaryStatement(models.Model):
    _inherit = "cssk.ec.summary.statement"

    vies_blocked = fields.Boolean(
        string="VIES Blocked",
        readonly=True,
        copy=False,
        help="The last VIES verification found INVALID VAT numbers on this "
        "statement; the export stays blocked until they are corrected and "
        "re-checked.",
    )

    # ------------------------------------------------------------------
    # Proof fetching (persisting) vs. validation (blocking)
    #
    # The consultation numbers VIES returns for VALID lines are the legal
    # proof of a qualified check and must never be thrown away. Raising a
    # UserError in the same transaction that wrote them would roll them
    # back (and force a VIES re-query on every retry), so the flow is
    # split:
    #   1. ``_vies_refresh_lines`` — fetch + persist, NEVER raises;
    #   2. the export override signals invalid lines with a sticky
    #      notification (transaction commits, proofs survive) instead of
    #      an exception, and only then lets the base export continue when
    #      everything is valid.
    # ------------------------------------------------------------------

    def _vies_refresh_lines(self):
        """Query VIES once per line and persist every obtained result.

        Pure fetch-and-store: never raises, so the consultation numbers
        obtained for valid lines survive even when other lines turn out to
        be invalid. Returns ``(invalid_descriptions, faulted_vats)``.
        """
        self.ensure_one()
        Partner = self.env["res.partner"]
        invalid = []
        faulted = []
        for line in self.line_ids:
            data = Partner._vies_query_direct(line.partner_vat, self.company_id.vat)
            if data is None:
                faulted.append(line.partner_vat or "—")
                line.write(
                    {
                        "vies_status": "fault",
                        "vies_check_date": fields.Datetime.now(),
                    }
                )
                continue
            valid = bool(data.get("valid"))
            line.write(
                {
                    "vies_valid": valid,
                    "vies_status": "valid" if valid else "invalid",
                    "vies_consultation_number": data.get("requestIdentifier") or "",
                    "vies_check_date": fields.Datetime.now(),
                }
            )
            if not valid:
                invalid.append(
                    "%s / %s"
                    % (line.partner_country_code or "??", line.partner_vat or "—")
                )
        self.vies_blocked = bool(invalid)
        return invalid, faulted

    def _vies_invalid_message(self, invalid):
        return _(
            "VIES reports these VAT numbers as INVALID — the EC sales "
            "list cannot be exported (a filing with an invalid VAT is "
            "penalised):\n%s"
        ) % "\n".join(invalid)

    def _vies_post_fault_note(self, faulted):
        # A transient VIES outage must not block a statutory deadline.
        msg = _(
            "VIES could not be reached for %(count)s line(s); they were "
            "exported without a fresh confirmation. Repeat the check when "
            "the service is available:\n%(vats)s"
        ) % {"count": len(faulted), "vats": "\n".join(faulted)}
        _logger.warning(msg)
        self.message_post(body=msg)

    def _check_vies(self):
        # Keep the base presence/format hard-block first (read-only: it can
        # safely raise because no proof has been written yet).
        super()._check_vies()
        if not self.company_id.vies_use_direct:
            return
        if self.env.context.get("cssk_vies_proofs_fresh"):
            # action_export_xml already queried VIES and persisted the
            # proofs in this request — validate the stored results only,
            # do not fire a second round of network calls.
            invalid = [
                "%s / %s"
                % (line.partner_country_code or "??", line.partner_vat or "—")
                for line in self.line_ids
                if line.vies_status == "invalid"
            ]
            faulted = [
                line.partner_vat or "—"
                for line in self.line_ids
                if line.vies_status == "fault"
            ]
        else:
            invalid, faulted = self._vies_refresh_lines()

        if invalid:
            raise UserError(self._vies_invalid_message(invalid))

        if faulted:
            self._vies_post_fault_note(faulted)

    def action_export_xml(self):
        self.ensure_one()
        if not self.company_id.vies_use_direct:
            return super().action_export_xml()

        # Re-run the read-only export gates BEFORE talking to VIES, so none
        # of their raises can roll back the proofs obtained below.
        self._ensure_not_submitted()
        if self.state == "draft":
            raise UserError(_("Compute the statement before exporting."))
        super()._check_vies()  # base presence/format gate (read-only)

        # Fetch + persist all proofs (never raises).
        invalid, faulted = self._vies_refresh_lines()
        if invalid:
            # Hard-block the export WITHOUT an exception: the transaction
            # commits normally, so the consultation numbers just obtained
            # for the valid lines are kept as legal proof.
            msg = self._vies_invalid_message(invalid)
            self.message_post(
                body=msg
                + "\n"
                + _(
                    "The VIES consultation numbers obtained for the valid "
                    "lines were kept."
                )
            )
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("EC sales list export blocked"),
                    "message": msg,
                    "type": "danger",
                    "sticky": True,
                },
            }
        # All lines valid (faults tolerated): proceed with the normal export.
        # The context flag makes _check_vies validate the freshly stored
        # results instead of re-querying VIES a second time.
        statement = self.with_context(cssk_vies_proofs_fresh=True)
        return super(CSSKEcSummaryStatement, statement).action_export_xml()


class CSSKEcSummaryStatementLine(models.Model):
    _inherit = "cssk.ec.summary.statement.line"

    vies_valid = fields.Boolean(string="VIES Valid", readonly=True, copy=False)
    vies_status = fields.Selection(
        [
            ("valid", "Valid"),
            ("invalid", "Invalid"),
            ("fault", "Service fault"),
        ],
        string="VIES Status",
        readonly=True,
        copy=False,
        help="Outcome of the last direct VIES check of this line: 'Service "
        "fault' means VIES was unreachable (tolerated at export so an "
        "outage cannot block a statutory deadline).",
    )
    vies_consultation_number = fields.Char(
        string="VIES Consultation No.", readonly=True, copy=False
    )
    vies_check_date = fields.Datetime(
        string="VIES Checked On", readonly=True, copy=False
    )
