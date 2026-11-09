# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Tables A and B become return lines; r130/r150/r250 are derived from them.

New in 1.5.0. The version records and their line definitions are
``noupdate="1"``, so on an existing database the upgrade only CREATES what is
missing — the new ``a01``… / ``b01``… lines arrive by themselves — and leaves
two things as they were, which this script does:

* r130, r150 and r250 still carry their old kind (``manual`` /
  ``asset_diff``). They are switched to the ``aggregate`` formula the data
  file now gives them, read from the file rather than repeated here.
* The generic two-digit lines (``dppo_ld_r01_2017`` …) of the 2013–2022 vzory
  are still there. Each fed row N of EVERY table and section of the XML at
  once; they are removed. Odoo does not remove an orphaned noupdate record.

Returns are not touched. An override on r130/r150/r250 is kept by code on the
next computation, exactly as before. An overridden two-digit row on a stored
return cannot be mapped to one table, so it is only logged; it disappears on
that return's next computation.

Idempotent: a definition already switched, or already gone, is skipped.
"""
import logging
import os
import re

_logger = logging.getLogger(__name__)

_LINE = re.compile(
    r'<record id="(dppo_ld_(r130|r150|r250)_(\d+))"[^>]*>(.*?)</record>', re.S)
_FORMULA = re.compile(r'<field name="aggregate_formula">([^<]*)</field>')


def _derived_from_data_files():
    """``{xmlid: formula}`` for r130/r150/r250 of every vzor."""
    module = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    data = os.path.join(module, "data")
    out = {}
    for fname in sorted(os.listdir(data)):
        if not (fname.startswith("dppo_version") and fname.endswith(".xml")):
            continue
        with open(os.path.join(data, fname), encoding="utf-8") as fh:
            source = fh.read()
        for match in _LINE.finditer(source):
            formula = _FORMULA.search(match.group(4))
            if formula:
                out[match.group(1)] = formula.group(1)
    return out


def migrate(cr, version):
    from odoo import SUPERUSER_ID, api

    env = api.Environment(cr, SUPERUSER_ID, {})
    switched = 0
    for xmlid, formula in _derived_from_data_files().items():
        ldef = env.ref("l10n_sk_dppo.%s" % xmlid, raise_if_not_found=False)
        if not ldef or (ldef.kind == "aggregate"
                        and ldef.aggregate_formula == formula):
            continue
        ldef.write({"kind": "aggregate", "aggregate_formula": formula,
                    "account_formula": False})
        switched += 1

    stale = env["ir.model.data"].search([
        ("module", "=", "l10n_sk_dppo"),
        ("model", "=", "cssk.income.tax.line.def"),
        ("name", "=like", "dppo_ld_r%"),
    ]).filtered(lambda imd: re.fullmatch(r"dppo_ld_r\d\d_\d+", imd.name))
    ldefs = env["cssk.income.tax.line.def"].browse(stale.mapped("res_id")).exists()
    by_version = {}
    for ldef in ldefs:
        by_version.setdefault(ldef.version_id.id, set()).add(ldef.code)
    for version_id, codes in by_version.items():
        kept = env["cssk.income.tax.return.line"].search([
            ("return_id.version_id", "=", version_id),
            ("code", "in", sorted(codes)),
            ("is_overridden", "=", True),
        ])
        for line in kept:
            _logger.warning(
                "l10n_sk_dppo 1.5.0: return %s (id %s) has an override on the "
                "retired row %s (%.2f). That row fed every table of the XML at "
                "once and cannot be mapped to one; enter the figure on the "
                "Table A/B line it belongs to (a01…, b01…).",
                line.return_id.display_name, line.return_id.id, line.code,
                line.manual_value)
    removed = len(ldefs)
    ldefs.unlink()
    stale.exists().unlink()
    _logger.info(
        "l10n_sk_dppo 1.5.0: %d row definition(s) switched to the tables, "
        "%d generic table row definition(s) removed.", switched, removed)
