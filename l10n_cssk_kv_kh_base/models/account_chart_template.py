# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountChartTemplate(models.AbstractModel):
    """Flag the reverse-charge taxes as soon as a chart is loaded.

    A ``post_init_hook`` alone covers only the companies that already existed
    when the module was installed. A migration project's companies are created
    **after** the modules are in place, so the hook missed exactly the
    companies the flag matters for — and the symptom is a control statement
    that computes, validates and files with no B.1 section at all, which
    nothing about the run reports as wrong.

    Found on the reference database: of two Slovak companies sharing one
    installation, the one whose chart was loaded first carried 10 flagged
    taxes and the one created later carried **none**.
    """

    _inherit = "account.chart.template"

    def _load(self, template_code, company, install_demo, force_create=True):
        result = super()._load(
            template_code, company, install_demo, force_create=force_create
        )
        # There is nothing to flag until the chart's taxes exist, and a
        # country module that declares no templates makes this a no-op.
        company._cssk_flag_reverse_charge_taxes()
        return result
