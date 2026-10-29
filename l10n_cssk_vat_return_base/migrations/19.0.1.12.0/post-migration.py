# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Re-point each vintage's tax replacements at its own vintage.

``original_tax_ids`` / ``replacing_tax_ids`` are one relation under two names
and ``copy()`` copies it, so every historical rate this module generated
arrived claiming the taxes in force TODAY as its replacements. On a Czech
chart the 2010 standard rate ended up replaced by seven taxes across three
vintages. See ``res_company._cssk_revintage_replacements``.

The repair is in the generator, which is idempotent, so running it is the
migration. Nothing posted is touched: a fiscal position is consulted when a
document is drafted, never afterwards.
"""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([])
    companies = companies.filtered(lambda c: c._cssk_historic_vat_rates())
    if companies:
        companies._cssk_create_historic_vat_taxes()
