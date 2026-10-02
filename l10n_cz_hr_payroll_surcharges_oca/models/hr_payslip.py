# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Mix the engine-neutral surcharge logic into the OCA engine's payslip."""

from odoo import models


class HrPayslip(models.Model):
    _name = "hr.payslip"
    _inherit = ["hr.payslip", "cz.surcharge.payslip.mixin"]

    def _l10n_cz_work100_is_gross(self):
        # payroll/models/hr_payslip.py::_compute_worked_days returns the FULL
        # days the calendar schedules and states outright that it "don't
        # substract leaves by default" — absences arrive as separate, negative
        # worked-day lines. So WORK100 here is gross and the absence hours have
        # to come back off it.
        return True
