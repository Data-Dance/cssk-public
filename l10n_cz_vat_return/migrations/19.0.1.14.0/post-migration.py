# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""ř. 47 — the asset-acquisition twins, for companies that already exist.

``l10n_cz`` declares ``VAT 47 Base`` and ``VAT 47 Total`` and ships no tax
carrying either, so *hodnota pořízeného majetku* filed 0.00 on every return
this module has ever produced. The twins are what give an accountant a way to
say "this purchase is a long-term asset"; see
``res_company._cz_create_asset_acquisition_taxes``.

Nothing already posted is touched. A twin is a NEW tax, so a bill that was
booked against the plain purchase tax keeps every tag it has and every figure
it reports — ř. 47 stays empty for past periods, which is the honest answer:
nothing in the database records which of those purchases were assets, and
guessing from an account code would file a number no document supports.
"""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([("chart_template", "=", "cz")])
    if not companies:
        return
    companies._cz_create_asset_acquisition_taxes()
    # The twins did not exist when the historical rates were generated, so
    # generate them again — the pass adopts rather than duplicates.
    companies._cssk_create_historic_vat_taxes()
