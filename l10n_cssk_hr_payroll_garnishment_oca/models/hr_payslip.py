# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Wire the garnishment register into the OCA ``payroll`` engine.

All of the logic lives in ``cssk.garnishment.payslip.mixin``; this module
only mixes it into this engine's ``hr.payslip`` and hooks the lifecycle.
"""

from odoo import models


class HrPayslip(models.Model):
    _name = "hr.payslip"
    _inherit = ["hr.payslip", "cssk.garnishment.payslip.mixin"]

    def action_payslip_done(self):
        res = super().action_payslip_done()
        self._cssk_garnishment_register()
        return res

    def action_payslip_cancel(self):
        res = super().action_payslip_cancel()
        self._cssk_garnishment_unregister()
        return res

    def action_payslip_draft(self):
        # Before the reset, not after: a payslip whose deduction is already
        # with the payee must not go back to draft at all.
        self._cssk_garnishment_check_resettable()
        res = super().action_payslip_draft()
        self._cssk_garnishment_unregister()
        return res
