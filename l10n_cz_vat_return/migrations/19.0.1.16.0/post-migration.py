# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""An intra-Community sale got two taxes, and a service kept Czech VAT.

`l10n_cz` names the domestic GOODS sale taxes as the originals of ``0% EU S``,
so under the Intra-Community position ``21% G`` became ``0% EU G`` and
``0% EU S`` at once, and ``21% S`` stayed ``21% S``.

Already-posted moves are NOT rewritten: they carry the taxes they were posted
with, and correcting them is a document-by-document decision.
"""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([("chart_template", "=", "cz")])
    if companies:
        companies._cz_map_intra_community_sale_service_taxes()
