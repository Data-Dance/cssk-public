from odoo import _, fields, models
from odoo.exceptions import UserError

from ..models.account_move import PEPPOL_RESPONSE_CODES


class PeppolInvoiceResponseWizard(models.TransientModel):
    _name = "edi.peppol.invoice.response.wizard"
    _description = "Send a Peppol Invoice Response"

    move_id = fields.Many2one(
        "account.move",
        required=True,
        ondelete="cascade",
    )
    response_code = fields.Selection(
        PEPPOL_RESPONSE_CODES,
        string="Response",
        required=True,
        default="RE",
        help="The business decision to communicate to the supplier: Rejected, "
        "Under query (dispute), Conditionally accepted, Accepted, …",
    )
    reason_ids = fields.Many2many(
        "edi.peppol.clarification",
        "peppol_ir_wizard_reason_rel",
        string="Reasons",
        domain=[("list_identifier", "=", "OPStatusReason")],
        help="Coded reason(s) for the response — required when rejecting, "
        "querying or conditionally accepting.",
    )
    action_ids = fields.Many2many(
        "edi.peppol.clarification",
        "peppol_ir_wizard_action_rel",
        string="Requested actions",
        domain=[("list_identifier", "=", "OPStatusAction")],
        help="Action(s) suggested to the supplier so the document can be "
        "accepted when re-sent (e.g. issue a credit note).",
    )
    note = fields.Text(
        string="Note",
        help="Free-text clarification sent to the supplier.",
    )

    def action_send(self):
        self.ensure_one()
        if self.response_code in ("RE", "UQ", "CA") and not (
            self.reason_ids or self.note
        ):
            raise UserError(
                _(
                    "A reason (coded or free text) is required when the "
                    "response is Rejected, Under query or Conditionally "
                    "accepted."
                )
            )
        self.move_id._peppol_emit_invoice_response(
            self.response_code,
            reason_clarifications=self.reason_ids | self.action_ids,
            note=self.note,
        )
        return {"type": "ir.actions.act_window_close"}
