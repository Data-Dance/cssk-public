# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    def _load(self, template_code, company, install_demo, force_create=True):
        """Tag the ř43/ř44 deduction as soon as a Czech chart exists.

        The base module's own override generates the historical rates here; the
        deduction tagging belongs beside it for the same reason — a company that
        loads the Czech chart AFTER this module was installed would otherwise
        have 45 self-assessed purchase taxes whose deduction reaches no line of
        the return, and nothing would say so.
        """
        result = super()._load(template_code, company, install_demo, force_create)
        if template_code == "cz":
            companies = company or self.env.company
            companies._cz_tag_selfassessed_deduction()
            companies._cz_fix_refund_repartition_accounts()
        return result
