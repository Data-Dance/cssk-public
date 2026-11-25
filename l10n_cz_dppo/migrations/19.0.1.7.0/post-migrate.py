# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Give an installed DPPDP9 version ř. 50 and ř. 150 (19.0.1.7.0).

The version and its rows are ``noupdate`` data and the rows have no xmlid of
their own, so an upgrade neither adds the new rows nor changes the old ones.
This script does, by row code:

* adds ``r50`` / ``r150`` (from the tax asset register) and the two typed
  rows ``r70_other`` / ``r170_other``;
* turns ``r70`` and ``r170`` from typed subtotals into ``other + ř. 50`` and
  ``other + ř. 150``, but only where they are still the typed rows this
  module shipped. A row somebody already rebuilt is left alone.

Returns keep their figures. On an open return the subtotal the accountant
typed on ř. 70 / ř. 170 is an override, and an override survives the next
computation by code: the tax base does not move. What changes there is that
ř. 50 or ř. 150 now carries a computed figure next to that typed subtotal,
and whether the subtotal already contains it only the accountant knows. Each
such return gets a note saying so. Filed returns are not touched at all.

Idempotent, row by row: a row that exists is not added again and a subtotal
that is no longer a typed row is not switched again, so a run interrupted
half way is completed by the next one.
"""
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

NEW_ROWS = [
    {"code": "r50", "kind": "asset_diff", "account_formula": "addback",
     "sequence": 14,
     "name": "ř.50 Rozdíl, o který odpisy hmotného a nehmotného majetku "
             "uplatněné v účetnictví převyšují odpisy podle § 26 až 33"},
    {"code": "r70_other", "kind": "manual", "sequence": 16,
     "name": "ř.20–63 bez ř.50: ostatní položky zvyšující výsledek "
             "hospodaření (zadává se ručně)"},
    {"code": "r150", "kind": "asset_diff", "account_formula": "deduction",
     "sequence": 24,
     "name": "ř.150 Rozdíl, o který odpisy hmotného a nehmotného majetku "
             "podle § 26 až 33 převyšují odpisy uplatněné v účetnictví"},
    {"code": "r170_other", "kind": "manual", "sequence": 26,
     "name": "ř.100–162 bez ř.150: ostatní položky snižující výsledek "
             "hospodaření (zadává se ručně)"},
]
SUBTOTALS = {"r70": "r70_other + r50", "r170": "r170_other + r150"}


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    ver = env.ref("l10n_cz_dppo.cz_dppo_version_2025", raise_if_not_found=False)
    if not ver:
        return
    codes = set(ver.line_def_ids.mapped("code"))
    LineDef = env["cssk.income.tax.line.def"]
    for row in NEW_ROWS:
        if row["code"] not in codes:
            LineDef.create(dict(row, version_id=ver.id))
    switched = []
    for ldef in ver.line_def_ids.filtered(lambda d: d.code in SUBTOTALS):
        if ldef.kind != "manual":
            _logger.info(
                "l10n_cz_dppo 1.7.0: %s is not a typed row (%s); left as "
                "it is.", ldef.code, ldef.kind)
            continue
        ldef.write({"kind": "aggregate",
                    "aggregate_formula": SUBTOTALS[ldef.code]})
        switched.append(ldef.code)
    if not switched:
        return
    typed = env["cssk.income.tax.return.line"].search([
        ("return_id.version_id", "=", ver.id),
        ("return_id.state", "in", ("draft", "preview")),
        ("code", "in", switched),
        ("is_overridden", "=", True),
    ])
    for ret in typed.mapped("return_id"):
        ret.message_post(body=(
            "Od verze 19.0.1.7.0 se ř. 50 / ř. 150 (rozdíl účetních a "
            "daňových odpisů) počítají z evidence daňových odpisů a ř. 70 / "
            "ř. 170 jsou součtem. Na tomto přiznání zůstává mezisoučet, který "
            "jste zadali ručně, takže se základ daně nemění. Zkontrolujte, "
            "zda ručně zadaný mezisoučet rozdíl odpisů už obsahuje. Chcete-li "
            "mezisoučet nechat počítat, zrušte na ř. 70 / ř. 170 ruční "
            "hodnotu, ostatní položky zadejte na řádek „ostatní položky“ a "
            "přiznání přepočítejte."))
    _logger.info(
        "l10n_cz_dppo 1.7.0: rows 50/150 added, %s switched to sums; %d open "
        "return(s) keep a typed subtotal and were given a note.",
        ", ".join(switched), len(typed.mapped("return_id")))
