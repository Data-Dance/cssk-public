"""Wire the advance-invoice accounts and journal whenever the SK chart is loaded.

The post_init hook wires the companies that already have the chart when this
module is installed. A company whose chart is loaded later - a new company, or
a fresh database where the chart and this module go in in the same run, where
the hook runs before the chart exists - was never wired. The spec only fills
empty settings, so running it on every load of the chart is safe.
"""

from odoo import models


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    def _post_load_data(self, template_code, company, template_data):
        res = super()._post_load_data(template_code, company, template_data)
        if template_code == "sk":
            from .. import SK_SPEC

            company = company or self.env.company
            company.with_company(company)._apply_advance_invoice_setup(SK_SPEC)
        return res
