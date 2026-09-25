# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# Core defines ``hr.leave.accrual.plan.name`` as a plain (non-translatable)
# Char. The Slovak localization ships several statutory accrual plans whose
# names are user-facing, so redefine the field as translatable — the English
# text in the data files becomes the ``en_US`` source and the Slovak wording
# is supplied via ``i18n/sk.po``. Same low-risk core-field override pattern
# already used for ``hr.leave.type.country_id``.

from odoo import fields, models


class HrLeaveAccrualPlan(models.Model):
    _inherit = "hr.leave.accrual.plan"

    name = fields.Char(translate=True)
