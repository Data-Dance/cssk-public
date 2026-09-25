# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Generate the historical Slovak VAT rates for companies already set up.

    post_init_hook only runs on **install**. Every company that already had
    this module — which is every existing deployment, and both spike companies
    — would otherwise be upgraded to a version that knows about historical
    rates and given none of them, silently. The generator is idempotent, so
    running it here is safe whether or not the hook has already fired.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([("chart_template", "=", "sk")])
    if not companies:
        return
    taxes = companies._cssk_create_historic_vat_taxes()
    _logger.info(
        "l10n_sk_vat_return: %s historical VAT rate(s) available across %s company/companies",
        len(taxes), len(companies),
    )
