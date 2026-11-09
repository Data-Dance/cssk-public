# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from ..hooks import _configure_cz_payroll_accounts


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    def _post_load_data(self, template_code, company, template_data):
        """Configure the Czech payroll accounts when a company loads the chart.

        The install hook only reaches the companies already on the Czech
        chart; a company that loaded it afterwards had unmapped salary rules,
        so its payslips posted nothing for them. Enterprise wires the same
        thing through hr_payroll_account; OCA payroll_account has no such hook.
        """
        super()._post_load_data(template_code, company, template_data)
        if template_code == "cz":
            _configure_cz_payroll_accounts(
                self.env, company or self.env.company
            )
