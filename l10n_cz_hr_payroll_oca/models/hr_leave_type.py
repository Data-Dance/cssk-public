# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# The OCA payroll engine derives worked-day lines from hr.leave via the resource
# calendar (hr.payslip._compute_leave_days). It keys each leave line by
# holiday_status_id.work_entry_type_id.code, but the OCA payroll stack has no
# hr.work.entry.type, so we attach a stable Czech payroll code to the leave type
# itself and re-key the worked-day lines from it (see hr_payslip.py).

from odoo import fields, models


class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    l10n_cz_payroll_code = fields.Selection(
        selection=[
            ("CZHOLIDAY", "Holiday"),
            ("CZSICK", "Sickness"),
            ("CZOCR", "Family Care"),
            ("CZUNPAID", "Unpaid Leave"),
            ("CZOBSTACLE", "Paid Obstacle"),
            ("CZPROSTOJ", "Employer obstacle — prostoj (§ 207 a)"),
            ("CZPOVETRNOST", "Employer obstacle — weather (§ 207 b)"),
            ("CZJINEPREKAZKY", "Employer obstacle — other (§ 208)"),
            ("CZCASTECNA", "Employer obstacle — short-time (§ 209)"),
            ("CZMATERSKA", "Maternity leave (§ 195)"),
            ("CZRODICOVSKA", "Parental leave (§ 196)"),
            ("CZOTCOVSKA", "Paternity leave"),
        ],
        string="Czech Payroll Code",
        help="Maps this leave type to a stable Czech payroll worked-day code so "
        "the salary rules can read absence hours per code and decide paid/unpaid "
        "and the compensation rate. Holiday and paid-obstacle time is compensated "
        "at the average hourly earnings; sickness drives the sickness compensation; OČR and unpaid "
        "leave get no employer pay (and unpaid leave prorates BASIC down).",
    )
