# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class AccountChartTemplate(models.AbstractModel):
    """Map a freshly loaded chart onto the denník columns.

    Without this the mapping only happens for a chart that already exists when
    the module is installed — and the usual order is the other way round: a new
    database gets the module, then the accountant picks the country's chart. The
    first denník would then flag every row, which reads as a broken module
    rather than as unfinished configuration.

    Only ever fills empty fields, so re-loading or extending a chart cannot
    overwrite what the accountant chose.
    """

    _inherit = "account.chart.template"

    def _load(self, template_code, company, install_demo, force_create=True):
        result = super()._load(template_code, company, install_demo,
                               force_create=force_create)
        for target in company or self.env.company:
            touched = target._cssk_map_chart_categories()
            if touched:
                _logger.info(
                    "cash journal: mapped %s accounts of %s after loading "
                    "chart %s", touched, target.display_name, template_code)
        return result
