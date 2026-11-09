# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrLeaveAccrualPlan(models.Model):
    _inherit = "hr.leave.accrual.plan"

    # Core Odoo defines hr.leave.accrual.plan.name as a plain, NON-translatable
    # Char. Our statutory Czech dovolená plans ship a clean English source name
    # and a Czech (cs) translation, so redefine the field as translatable — the
    # existing English name becomes the en_US source term. Same low-risk
    # core-field override technique used for hr.leave.type.country_id.
    name = fields.Char(translate=True)
