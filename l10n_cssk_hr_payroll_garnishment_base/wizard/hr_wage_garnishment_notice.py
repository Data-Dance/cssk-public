# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The employer's statutory paperwork around wage garnishments.

Deducting the money is only half of what the law asks of a payer of wages.
Czech ``§ 294`` and ``§ 295 o. s. ř.`` oblige the employer to *tell* the court
or the bailiff when a debtor joins or leaves, to answer enquiries about the
rank and size of the claims, and to render an account of what was deducted.
Slovak ``§ 71 a nasl. Exekučného poriadku`` imposes the mirror duties.

This wizard assembles those documents from the register, so the payroll
officer prints rather than retypes.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError

NOTICE_TYPES = [
    (
        "employment_start",
        "Notice of employment start (§ 294/1 o. s. ř.)",
    ),
    (
        "employment_end",
        "Notice of employment end (§ 294/1 o. s. ř.)",
    ),
    (
        "enquiry",
        "Answer to an enquiry — rank and amount of claims (§ 294/2, § 295 o. s. ř.)",
    ),
    (
        "settlement",
        "Account of deductions (vyúčtování srážek)",
    ),
]


class HrWageGarnishmentNotice(models.TransientModel):
    _name = "hr.wage.garnishment.notice"
    _description = "Wage Garnishment Statutory Notice"

    notice_type = fields.Selection(
        NOTICE_TYPES, required=True, default="settlement"
    )
    employee_id = fields.Many2one("hr.employee", required=True)
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    garnishment_ids = fields.Many2many(
        "hr.wage.garnishment",
        string="Orders",
        help="Leave empty to cover every order on file for the employee.",
    )
    recipient_partner_id = fields.Many2one(
        "res.partner",
        "Addressee",
        help="Court or bailiff the notice is addressed to. Defaults to the "
        "payee of the selected order.",
    )
    date_from = fields.Date(
        default=lambda self: fields.Date.context_today(self).replace(month=1, day=1)
    )
    date_to = fields.Date(default=fields.Date.context_today)
    event_date = fields.Date(
        "Event Date",
        default=fields.Date.context_today,
        help="Day the employment started or ended.",
    )
    note = fields.Text()

    # --- reporting helpers used by the QWeb templates ---------------------
    def _orders(self):
        self.ensure_one()
        if self.garnishment_ids:
            return self.garnishment_ids
        return self.env["hr.wage.garnishment"].search(
            [
                ("employee_id", "=", self.employee_id.id),
                ("state", "!=", "cancel"),
            ],
            order="date_delivered, sequence, id",
        )

    def _lines(self):
        """Deductions in the reporting window, oldest first."""
        self.ensure_one()
        domain = [
            ("garnishment_id", "in", self._orders().ids),
        ]
        if self.date_from:
            domain.append(("date_to", ">=", self.date_from))
        if self.date_to:
            domain.append(("date_to", "<=", self.date_to))
        return self.env["hr.wage.garnishment.line"].search(
            domain, order="date_to, garnishment_id"
        )

    @api.onchange("garnishment_ids")
    def _onchange_garnishment_ids(self):
        if self.garnishment_ids and not self.recipient_partner_id:
            self.recipient_partner_id = self.garnishment_ids[0].payee_partner_id

    def action_print(self):
        self.ensure_one()
        if not self._orders():
            raise UserError(
                _(
                    "%s has no garnishment orders on file, so there is nothing "
                    "to report.",
                    self.employee_id.display_name,
                )
            )
        if self.notice_type == "settlement":
            return self.env.ref(
                "l10n_cssk_hr_payroll_garnishment_base."
                "action_report_garnishment_settlement"
            ).report_action(self)
        return self.env.ref(
            "l10n_cssk_hr_payroll_garnishment_base.action_report_garnishment_notice"
        ).report_action(self)
