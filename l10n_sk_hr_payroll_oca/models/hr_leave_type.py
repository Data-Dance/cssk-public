# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# Maps a time-off type to a stable Slovak payroll code. The payroll engine's
# ``hr.payslip._compute_leave_days`` groups leaves by their type and keys the
# resulting worked-day line by this code, so the salary rules can tell holiday
# (dovolenka), sickness (PN), family care (OČR), unpaid leave (neplatené voľno)
# and a paid work obstacle (prekážka, e.g. lekár/doprovod) apart and decide
# paid/unpaid + rate per code. This mirrors the unified ``hr.work.entry.type``
# ``code`` that Odoo master uses as its "Time Type" (see
# docs/master_work_entry_analysis.md), so the taxonomy ports 1:1.

from odoo import fields, models


class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    l10n_sk_payroll_code = fields.Selection(
        selection=[
            ("DOVOLENKA", "Holiday"),
            ("PN", "Sickness (PN)"),
            ("OCR", "Family care (OČR)"),
            ("NEPLATENE", "Unpaid leave"),
            ("OBSTACLE", "Paid work obstacle"),
            ("PREKAZKA_PRESTOJ", "Employer obstacle — prestoj (§ 142/1)"),
            ("PREKAZKA_POCASIE", "Employer obstacle — weather (§ 142/2)"),
            ("PREKAZKA_INE", "Employer obstacle — other (§ 142/3)"),
            ("PREKAZKA_VAZNE", "Employer obstacle — serious operational (§ 142/4)"),
            ("MATERSKA", "Maternity leave (§ 166/1)"),
            ("RODICOVSKA", "Parental leave (§ 166/2)"),
            ("OTCOVSKA", "Paternity leave (§ 166/3)"),
        ],
        string="Slovak Payroll Code",
        help="Stable payroll code used by the Slovak salary rules to classify "
        "this absence: holiday and paid obstacle are paid at average earnings "
        "(insurable + taxable); sickness drives the employer sick-pay compensation; "
        "family care and unpaid leave only cut worked days (no pay). The four "
        "§ 142 employer-side obstacles are each paid at their own statutory "
        "percentage of average earnings, which is why they are separate codes "
        "rather than one bucket.",
    )
