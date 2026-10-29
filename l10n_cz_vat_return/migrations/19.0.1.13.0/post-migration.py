# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Let the Extra-Community position tell goods from services.

``l10n_cz`` points BOTH extra-Community service taxes at the domestic
**goods** tax, so one line carrying the domestic 21 % was mapped onto three
taxes and the same purchase was declared on ř. 7, ř. 12 and ř. 42 while ř. 43
deducted twice the real tax. See
``res_company._cz_map_extra_community_service_taxes``.

Nothing posted is touched: a fiscal position is consulted when a document is
drafted, never afterwards. Documents already booked through the broken mapping
keep the taxes they were given, and their ř. 7 / ř. 12 / ř. 42 / ř. 43 figures
stay wrong until somebody re-tags or re-enters them — which is a decision
about a filed period, not something a migration may take.
"""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([("chart_template", "=", "cz")])
    if companies:
        companies._cz_map_extra_community_service_taxes()
