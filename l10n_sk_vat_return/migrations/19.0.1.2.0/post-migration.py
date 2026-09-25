# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Re-apply the historical-rate generator so the tag remap reaches the data.

    The remap (``{09b: 09, 10b: 10}``, see ``SK_HISTORIC_VAT_RATES``) is
    applied when a historical tax is created **or adopted**. Taxes generated
    before it existed carry the cloned tags and nothing re-applies the rule to
    them: the generator runs on install, on chart load, and from a version
    migration — none of which fires for a company that already has its rates.

    So the code was right and every 20 % reverse-charge tax still filed on
    ``r09b``, a line that did not exist while 20 % was in force. Confirmed on a
    populated company by the MRP extractor, which reloaded its whole import and
    saw no change at all — correctly, because a reload rewrites documents and
    not the tax records they point at.

    The generator is idempotent and the remap is a no-op where already applied.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([("chart_template", "=", "sk")])
    if not companies:
        return
    taxes = companies._cssk_create_historic_vat_taxes()
    _logger.info(
        "l10n_sk_vat_return: historical rates re-applied across %s company/"
        "companies (%s tax records)", len(companies), len(taxes),
    )
