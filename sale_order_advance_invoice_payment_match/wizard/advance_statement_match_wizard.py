from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AdvanceStatementMatchWizard(models.TransientModel):
    _name = "advance.statement.match.wizard"
    _description = "Match Statement Line to Advance Invoice"

    statement_line_id = fields.Many2one(
        "account.bank.statement.line",
        string="Bank Transaction",
        required=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        related="statement_line_id.company_id", readonly=True
    )
    currency_id = fields.Many2one(
        related="statement_line_id.currency_id", readonly=True
    )
    amount = fields.Monetary(
        related="statement_line_id.amount", readonly=True
    )
    payment_ref = fields.Char(
        related="statement_line_id.payment_ref", readonly=True
    )
    order_id = fields.Many2one(
        "sale.order",
        string="Advance Invoice",
        required=True,
        domain="[('id', 'in', candidate_order_ids)]",
    )
    candidate_order_ids = fields.Many2many(
        "sale.order", compute="_compute_candidate_order_ids"
    )

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        if (
            self.env.context.get("active_model")
            == "account.bank.statement.line"
            and self.env.context.get("active_id")
        ):
            st_line = self.env["account.bank.statement.line"].browse(
                self.env.context["active_id"]
            )
            values.setdefault("statement_line_id", st_line.id)
            result = self.env[
                "sale.order"
            ]._cssk_find_advance_for_statement_line(st_line)
            if result:
                values.setdefault("order_id", result[0].id)
        return values

    @api.depends("statement_line_id")
    def _compute_candidate_order_ids(self):
        for wizard in self:
            wizard.candidate_order_ids = (
                self.env["sale.order"]._cssk_open_advances_for_statement_line(
                    wizard.statement_line_id
                )
                if wizard.statement_line_id
                else self.env["sale.order"]
            )

    def action_apply(self):
        self.ensure_one()
        if not self.order_id:
            raise UserError(_("Select an advance invoice to match."))
        payment = self.statement_line_id._cssk_apply_advance_order(
            self.order_id
        )
        return {
            "name": _("Payment"),
            "type": "ir.actions.act_window",
            "res_model": "account.payment",
            "context": {"create": False},
            "view_mode": "form",
            "res_id": payment.id,
        }
