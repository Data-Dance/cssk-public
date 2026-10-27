# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models

from .res_company import HEALTH_INSURER_CODES


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    l10n_sk_health_insurer_code = fields.Selection(
        HEALTH_INSURER_CODES,
        string="Health insurer (SK)",
        groups="hr.group_hr_user",
        tracking=True,
        help="The health insurance company the employee is insured with. "
        "Each insurer gets its own monthly dávka 514 listing only its "
        "insurees. Leave empty when the employee is insured with the "
        "company's default insurer.")

    def _l10n_sk_health_insurer(self):
        """The employee's insurer, falling back to the company default."""
        self.ensure_one()
        return (self.sudo().l10n_sk_health_insurer_code
                or self.company_id.l10n_sk_health_insurer_code)
