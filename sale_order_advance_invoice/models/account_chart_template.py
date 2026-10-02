"""Keep the advance journal's xmlid alive across a chart load.

Loading a chart onto a company with no accounting yet first deletes the
company's chart-template records, journals included (core
``account.chart.template._load``). On a fresh database where the chart and
this module are installed in one run, that removes the TDADV journal the
module had just made, and its xmlid is left pointing at nothing. After every
chart load the xmlid is re-adopted if it dangles; a live one is left alone.
"""

from odoo import models


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    def _post_load_data(self, template_code, company, template_data):
        res = super()._post_load_data(template_code, company, template_data)
        company = company or self.env.company
        self.env["res.company"].with_company(company)._advance_invoice_journal_ensure_xmlid()
        return res
