# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Give the vehicle taxes their Slovak names in companies that lack them.

Up to 1.1.0 the install hook created the taxes with ``_load_data``, which
drops the template's ``name@sk``, so in a company whose chart predates the
module they were named in English only. The chart translations are loaded
again without overwriting: only a missing translation is filled in, so a
name a user changed is kept.
"""

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([("chart_template", "=", "sk")])
    if companies:
        env["account.chart.template"]._load_translations(companies=companies)
