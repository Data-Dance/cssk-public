# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountChartTemplate(models.AbstractModel):
    """Generate the historical VAT rates as soon as a chart is loaded.

    Without this, the rates would exist only for companies that already had
    their chart when the module was installed — and a migration project's
    companies are typically created *after* the modules are in place, which is
    exactly the case that would have been missed.

    Deliberately after ``super()``: the rates are cloned from the chart's own
    taxes, so there is nothing to clone until the chart is in.
    """

    _inherit = "account.chart.template"

    def _load(self, template_code, company, install_demo, force_create=True):
        result = super()._load(
            template_code, company, install_demo, force_create=force_create
        )
        # A country module that declares no historical rates for this chart
        # makes the call a no-op, so no country check belongs here.
        company._cssk_create_historic_vat_taxes()
        return result
