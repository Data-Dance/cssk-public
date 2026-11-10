# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields


class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    kiosk_visible = fields.Boolean(
        string="Show in Attendance Kiosk",
        help="Offer this reason when an employee checks out at the attendance kiosk.\n"
             "Kiosk reason types should normally not require an allocation, otherwise "
             "the generated time off is skipped when the employee has no allocation.")
    kiosk_sequence = fields.Integer(
        string="Kiosk Order", default=10,
        help="Order of the reason buttons on the kiosk check-out screen.")
