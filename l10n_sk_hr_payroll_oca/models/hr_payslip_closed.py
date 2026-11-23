# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def compute_sheet(self):
        """Compute a Slovak payslip only while it is a draft or waiting.

        The engine computes every payslip it is given and sets it to waiting,
        whatever its state; its form offers the button on a draft or waiting
        payslip only. A confirmed payslip is a wage accounted to the
        employee: the recorded fund bases, the daily base of sick pay and the
        average earnings are read from it, so it stays as confirmed. The same
        holds for a cancelled one. This is the outermost ``compute_sheet`` of
        the module, so nothing of it runs for a closed payslip.
        """
        closed = self.filtered(
            lambda slip: slip.state not in ("draft", "verify")
            and slip._l10n_sk_is_slovak()
        )
        if not closed:
            return super().compute_sheet()
        if self - closed:
            super(HrPayslip, self - closed).compute_sheet()
        return True
