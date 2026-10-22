# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""An EU vendor bill kept the domestic VAT instead of self-assessing it.

`l10n_cz` ships ``21% EU G``, ``12% EU G``, ``21% EU S`` and ``12% EU S``
with no original tax, so the Intra-Community fiscal position maps nothing and
``21% G`` stays ``21% G``. Found on an inter-company bill from a Slovak seller:
30.00 of goods came out at 36.30 and could not be posted against the seller's
invoice.

Already-posted moves are NOT rewritten: they carry the taxes they were posted
with, and correcting them is a document-by-document decision.
"""
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([("chart_template", "=", "cz")])
    if companies:
        companies._cz_map_intra_community_purchase_taxes()
