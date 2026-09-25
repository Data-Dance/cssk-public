# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrPayslipInput(models.Model):
    _inherit = "hr.payslip.input"

    employee_id = fields.Many2one(
        "hr.employee",
        related="payslip_id.employee_id",
        store=True,
        index=True,
        string="Employee",
    )
    date_from = fields.Date(
        related="payslip_id.date_from",
        store=True,
        index=True,
        string="Period Start",
    )
    date_to = fields.Date(
        related="payslip_id.date_to",
        store=True,
        string="Period End",
    )
