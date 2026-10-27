# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Open the DPPDP9 version to every period the structure files (2021+).

The version shipped ``valid_from = 2025-01-01`` and a flat 21 % on ř.280, so
a 2024 or earlier period could not be entered at all, and the rate would have
been wrong for anything begun before 1. 1. 2024 (19 %, zákon č. 349/2023 Sb.,
čl. XVI bod 1). The version is ``noupdate`` data, so the upgrade does not
rewrite it; each value is changed only where it still holds exactly what
this module shipped, so an accountant's own edit is left alone.
"""
from odoo import SUPERUSER_ID, api

OLD_RATE = "21.0 if r270 > 0 else 0.0"
NEW_RATE = ("(21.0 if period_start_year >= 2024 else 19.0) "
            "if r270 > 0 else 0.0")


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    ver = env.ref("l10n_cz_dppo.cz_dppo_version_2025", raise_if_not_found=False)
    if not ver:
        return
    vals = {}
    if str(ver.valid_from) == "2025-01-01":
        vals["valid_from"] = "2021-01-01"
    if ver.name == "DPPDP9 2025":
        vals["name"] = "DPPDP9"
    if vals:
        ver.write(vals)
    r280 = ver.line_def_ids.filtered(lambda d: d.code == "r280")
    if r280 and (r280.aggregate_formula or "").strip() == OLD_RATE:
        r280.aggregate_formula = NEW_RATE
