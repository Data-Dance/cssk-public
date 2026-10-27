# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Employee-level inputs to the garnishment calculation.

The number of maintained persons and the pensioner flag are properties of the
*person*, not of a contract, so they live on ``hr.employee``. Both payroll
engines already carry a per-contract/per-version dependants field for the
older single-claim rule; the bridges prefer this one and fall back to theirs.
"""

from odoo import _, api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    l10n_cssk_garnishment_dependents = fields.Integer(
        "Maintained Persons",
        groups="hr.group_hr_user",
        tracking=True,
        help="Number of persons the employee is legally obliged to maintain. "
        "Each one raises the non-attachable amount — by a quarter of the "
        "debtor's amount in the Czech Republic (NV 595/2006 § 1), by 25 % "
        "(50 % for a pensioner) in Slovakia (NV 268/2006 § 1 ods. 2).",
    )
    l10n_cssk_garnishment_is_pensioner = fields.Boolean(
        "Pension Recipient",
        groups="hr.group_hr_user",
        tracking=True,
        help="Slovakia: poberateľ dôchodkových dávok — the per-dependant "
        "protection doubles to 50 %. Czech Republic: the employee has proved "
        "an old-age pension, a disability pension of the 2nd or 3rd degree "
        "or an orphan's pension (§ 279 odst. 5 písm. a) o. s. ř.), which "
        "lifts the two-thirds rule for four or more executions while one "
        "third stays below the insolvency trustee's monthly amount.",
    )
    l10n_cssk_garnishment_ids = fields.One2many(
        "hr.wage.garnishment", "employee_id", groups="hr.group_hr_user"
    )
    l10n_cssk_garnishment_count = fields.Integer(
        compute="_compute_l10n_cssk_garnishment_count", groups="hr.group_hr_user"
    )

    @api.depends("l10n_cssk_garnishment_ids.state")
    def _compute_l10n_cssk_garnishment_count(self):
        for employee in self:
            employee.l10n_cssk_garnishment_count = len(
                employee.l10n_cssk_garnishment_ids.filtered(
                    lambda order: order.state == "running"
                )
            )

    def action_open_garnishments(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Wage Garnishments"),
            "res_model": "hr.wage.garnishment",
            "view_mode": "list,form",
            "domain": [("employee_id", "=", self.id)],
            "context": {"default_employee_id": self.id},
        }
