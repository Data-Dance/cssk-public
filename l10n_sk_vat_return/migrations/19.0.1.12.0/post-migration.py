# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Give existing Slovak companies the received-EU-service taxes.

See ``account.chart.template._get_sk_vat_return_account_tax``. Only the taxes a
company lacks are loaded, so re-running is harmless and nothing an accountant
edited is rewritten.
"""
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([("chart_template", "=", "sk")])
    loaded = env["account.chart.template"]._cssk_load_sk_eu_service_taxes(
        companies)
    _logger.info("l10n_sk_vat_return 19.0.1.12.0: %s EU-service tax(es) "
                 "loaded across %s company/companies", loaded, len(companies))
