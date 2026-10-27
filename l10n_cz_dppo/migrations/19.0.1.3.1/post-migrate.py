# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Dary on ř.260, VaV / odborné vzdělávání on ř.242 / ř.243, on existing DBs.

The DPPDP9 version shipped one row ``r240`` for "§ 34 odečty and § 20 odst. 8
dary" and filed it as ř.240, while on the form (25 5404 vzor č. 36) ř.240 is
the § 34 odečet in its wording to 31. 12. 2004, VaV and odborné vzdělávání are
ř.242 / ř.243 and dary are ř.260, deducted after ř.250 and before the
rounding on ř.270.

The version is ``noupdate`` data, so an upgrade would not rewrite it. Rows are
changed only where they still hold exactly what this module shipped, so an
accountant's own edit is left alone. Amounts already entered on r240 are NOT
moved: the old row mixed three things and only the accountant knows which one
an amount was. Recomputing a return rebuilds its lines from the version.
"""
from odoo import SUPERUSER_ID, api

OLD_R240 = ("ř.240 Odečty (§ 34 — VaV, odborné vzdělávání) a dary "
            "(§ 20 odst. 8)")
NEW_R240 = "ř.240 Odečet podle § 34 odst. 3 až 10 a 12 ve znění do 31. 12. 2004"
FORMULAS = {
    # code: (shipped before, now, new name)
    "r250": ("max(r200 - r230 - r240, 0.0)",
             "max(r200 - r230 - r240 - r242 - r243, 0.0)",
             "ř.250 Základ daně snížený o položky podle § 34"),
    "r270": ("int(r250 / 1000) * 1000",
             "int(max(r250 - r260, 0.0) / 1000) * 1000",
             "ř.270 Základ daně snížený o položky podle § 34 a § 20 odst. 8, "
             "zaokrouhlený na celé tisíce Kč dolů"),
}
NEW_ROWS = [
    {"code": "r242", "sequence": 62, "kind": "manual",
     "name": "ř.242 Odečet na podporu výzkumu a vývoje (§ 34 odst. 4, "
             "§ 34a až 34e)"},
    {"code": "r243", "sequence": 64, "kind": "manual",
     "name": "ř.243 Odečet na podporu odborného vzdělávání (§ 34 odst. 4, "
             "§ 34f až 34h)"},
    {"code": "r260", "sequence": 75, "kind": "manual",
     "name": "ř.260 Odečet bezúplatných plnění (§ 20 odst. 8)"},
]


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    ver = env.ref("l10n_cz_dppo.cz_dppo_version_2025", raise_if_not_found=False)
    if not ver:
        return
    defs = {d.code: d for d in ver.line_def_ids}
    if "r240" in defs and defs["r240"].name == OLD_R240:
        defs["r240"].name = NEW_R240
    for code, (old, new, name) in FORMULAS.items():
        ldef = defs.get(code)
        if ldef and (ldef.aggregate_formula or "").strip() == old:
            ldef.write({"aggregate_formula": new, "name": name})
    for row in NEW_ROWS:
        if row["code"] not in defs:
            env["cssk.income.tax.line.def"].create(
                dict(row, version_id=ver.id))
