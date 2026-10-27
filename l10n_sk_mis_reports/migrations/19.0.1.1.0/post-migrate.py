# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""Bring an installed SK P&L template up to 19.0.1.1.0.

The template is ``noupdate`` data: the upgrade creates the new rows
(predané nehnuteľnosti 507, prevod podielov 596, the hidden style) but does
not touch the existing ones. Each existing value is rewritten only where it
still holds exactly what this module shipped, so a user's edit stays.
"""
from odoo import SUPERUSER_ID, api

UPDATES = [
    # (xmlid, field, shipped, now)
    ("kpi_naklady_spolu", "expression",
     "predany_tovar + spotreba + sluzby + osobne + dane_poplatky + odpisy"
     " + ostatne_naklady",
     "predany_tovar + predane_nehnutelnosti + spotreba + sluzby + osobne"
     " + dane_poplatky + odpisy + ostatne_naklady"),
    ("kpi_expr_dan_z_prijmov", "name",
     "balp[591%,595%]", "balp[591%,592%,595%]"),
    ("kpi_vh_po_zdaneni", "expression",
     "vh_pred_zdanenim - dan_z_prijmov",
     "vh_pred_zdanenim - dan_z_prijmov - prevod_podielov"),
]


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    for xmlid, field, shipped, now in UPDATES:
        record = env.ref("l10n_sk_mis_reports.%s" % xmlid,
                         raise_if_not_found=False)
        if record and (record[field] or "").strip() == shipped:
            record[field] = now
    helper = env.ref("l10n_sk_mis_reports.kpi_trieda_54_55",
                     raise_if_not_found=False)
    hidden = env.ref("l10n_sk_mis_reports.style_hidden",
                     raise_if_not_found=False)
    if helper and hidden and not helper.style_id:
        helper.style_id = hidden
