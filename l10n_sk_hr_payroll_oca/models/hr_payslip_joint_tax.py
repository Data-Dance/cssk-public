# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Several employee records of one person taxed together, on this engine.

The rules and their reasons are in ``l10n_sk_hr_payroll_base``
(``l10n.sk.payslip.joint.tax.mixin``); here is what only the engine knows.
"""

from odoo import models


class HrPayslip(models.Model):
    _inherit = ["hr.payslip", "l10n.sk.payslip.joint.tax.mixin"]

    def _l10n_sk_joint_tax_applies(self):
        self.ensure_one()
        return self._l10n_sk_is_slovak()

    def _l10n_sk_joint_tax_is_confirmed(self):
        self.ensure_one()
        return self.state == "done"

    def _l10n_sk_joint_tax_is_set_aside(self):
        """A refund is a credit note; the payslip it refunds points at it."""
        self.ensure_one()
        return bool(
            self.credit_note
            or (self.refunded_id and self.refunded_id.state != "cancel")
        )

    def compute_sheet(self):
        """Compute the payslips that tax a month for others after the others.

        The principal's payslip reads the bases the linked payslips move to
        it, so in one batch the linked ones are computed first.
        """
        principals = self.filtered(
            lambda slip: slip._l10n_sk_joint_tax_applies()
            and slip.employee_id.sudo().l10n_sk_tax_linked_ids
        )
        others = self - principals
        if not principals:
            others._l10n_sk_check_joint_tax_before_compute()
            result = super().compute_sheet()
            others._l10n_sk_check_joint_tax_after_compute()
            return result
        result = True
        if others:
            others._l10n_sk_check_joint_tax_before_compute()
            result = super(HrPayslip, others).compute_sheet()
            others._l10n_sk_check_joint_tax_after_compute()
        principals._l10n_sk_check_joint_tax_before_compute()
        result = super(HrPayslip, principals).compute_sheet()
        return result

    def action_payslip_done(self):
        result = super().action_payslip_done()
        # After the engine's own work, which may compute the payslip again:
        # an error here undoes the confirmation with the rest of the request.
        self._l10n_sk_check_joint_tax_before_confirm()
        return result

    def action_payslip_cancel(self):
        self._l10n_sk_check_joint_tax_before_withdrawal()
        return super().action_payslip_cancel()

    def refund_sheet(self):
        self._l10n_sk_check_joint_tax_before_withdrawal()
        return super().refund_sheet()
