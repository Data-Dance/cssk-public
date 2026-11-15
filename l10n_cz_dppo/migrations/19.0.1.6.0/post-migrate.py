# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Bring ř. 10 of an installed DPPDP9 version up to 19.0.1.6.0.

ř. 10 read ``5,6,-59``: every account of skupina 59 left out. That is right
for the income tax (591, 592, 593, 595, 599) and for the převod podílu
společníkům (596), which the Výkaz zisku a ztráty puts below "** Výsledek
hospodaření před zdaněním" — and wrong for 597 and 598, the převodové účty
of costs, which are part of that result (their counterparts 697 and 698 were
counted, so a company using them had ř. 10 overstated by the amount).

The version is ``noupdate`` data, so the upgrade does not rewrite it; the
formula is changed only where it still holds exactly what this module
shipped, so an accountant's own edit is left alone. Returns already computed
keep their figures until they are recomputed.
"""
from odoo import SUPERUSER_ID, api

OLD = "5,6,-59"
NEW = "5,6,-591,-592,-593,-595,-596,-599"


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    ver = env.ref("l10n_cz_dppo.cz_dppo_version_2025", raise_if_not_found=False)
    if not ver:
        return
    for r10 in ver.line_def_ids.filtered(lambda d: d.code == "r10"):
        if "".join((r10.account_formula or "").split()) == OLD:
            r10.account_formula = NEW
