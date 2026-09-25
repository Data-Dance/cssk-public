# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Remit a whole period's garnishment deductions in one go."""

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HrWageGarnishmentRemittance(models.TransientModel):
    _name = "hr.wage.garnishment.remittance"
    _description = "Remit Wage Garnishments"

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    date_to = fields.Date(
        "Up To",
        required=True,
        default=fields.Date.context_today,
        help="Every computed deduction for a period ending on or before this "
        "date is booked as payable to its bailiff.",
    )
    payee_partner_id = fields.Many2one(
        "res.partner",
        "Only This Payee",
        help="Leave empty to remit to every payee at once.",
    )
    line_ids = fields.Many2many(
        "hr.wage.garnishment.line", compute="_compute_line_ids"
    )
    line_count = fields.Integer(compute="_compute_line_ids")
    total_amount = fields.Monetary(compute="_compute_line_ids")
    currency_id = fields.Many2one("res.currency", related="company_id.currency_id")

    @api.depends("company_id", "date_to", "payee_partner_id")
    def _compute_line_ids(self):
        for wizard in self:
            lines = self.env["hr.wage.garnishment.line"]._open_for_remittance(
                wizard.company_id, wizard.date_to, wizard.payee_partner_id
            )
            wizard.line_ids = lines
            wizard.line_count = len(lines)
            wizard.total_amount = sum(lines.mapped("amount"))

    def action_remit(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(
                _("No unremitted deductions found up to %s.", self.date_to)
            )
        return self.line_ids.action_remit()
