# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    checkout_reason_id = fields.Many2one(
        'hr.leave.type', string="Departure Reason",
        domain="[('kiosk_visible', '=', True)]", index=True,
        help="Reason selected at the kiosk when checking out. "
             "Empty means a normal check-out (work ended).")
    checkout_leave_id = fields.Many2one(
        'hr.leave', string="Generated Time Off", readonly=True,
        help="Draft time off created from the kiosk departure reason.")
