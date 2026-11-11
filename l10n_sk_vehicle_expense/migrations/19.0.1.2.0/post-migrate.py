# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The vehicle-purchase taxes, and the § 85n flag on the existing two.

1.2.0 adds ``vs_auto_23_asset`` / ``vs_auto_19_asset``, whose undeducted half
is capitalised on the asset account, and flags every § 85n tax so the tax
depreciation board leaves that half out of the entry value (§ 52zzzk ZDP).
Taxes created from the template are already flagged; the two that existed
before are flagged here by their xmlid, so a copy a user made by hand is left
for the user to flag.
"""

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([("chart_template", "=", "sk")])
    if not companies:
        return
    Chart = env["account.chart.template"]
    Chart._l10n_sk_vehicle_load_taxes(companies)
    for company in companies:
        for xmlid in ("vs_auto_23", "vs_auto_19"):
            tax = env.ref(f"account.{company.id}_{xmlid}", raise_if_not_found=False)
            if tax:
                tax.l10n_sk_par85n = True
