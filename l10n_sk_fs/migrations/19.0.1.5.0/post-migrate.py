# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Carry the corrected UZPODv14 row formulas to an existing database.

19.0.1.5.0 fixes the Súvaha mapping against the l10n_sk chart: 16 codes the
chart does not have, 34 balance-sheet accounts that reached no row, two
korekcia accounts carried with the wrong sign, and s113 (vydané dlhopisy)
turned from a manual row into an accounts row as the filed export always had
it. The version record lives in a ``noupdate="1"`` file, so an upgrade does
not touch it; the formulas are written here, read from that same data file so
there is one source for them (see 19.0.1.2.0 for why the file is not simply
reloaded).

The filed export reads ``models/uzpod14_rows.py`` directly and needs nothing.
A statement already computed keeps its stored lines; recompute it.
"""

import ast
import logging
import os

from lxml import etree

_logger = logging.getLogger(__name__)

DATA = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "cssk_uzpod_v14_version_data.xml",
)
FIELDS = ("kind", "account_formula", "account_formula_correction")


def _shipped_rows():
    root = etree.parse(DATA)
    node = root.find(".//record[@id='uzpod_v14']/field[@name='line_def_ids']")
    if node is None or not node.get("eval"):
        return {}
    return {vals["code"]: vals for _c, _i, vals in ast.literal_eval(node.get("eval"))}


def migrate(cr, version):
    if not version:
        return
    cr.execute("""
        SELECT res_id FROM ir_model_data
         WHERE module = 'l10n_sk_fs' AND name = 'uzpod_v14'
           AND model = 'cssk.fs.statement.version'
    """)
    found = cr.fetchone()
    if not found:
        return
    rows = _shipped_rows()
    if not rows:
        _logger.warning("l10n_sk_fs 19.0.1.5.0: no UZPODv14 rows found in %s; "
                        "row definitions left as they are", DATA)
        return
    changed = 0
    for code, vals in rows.items():
        cr.execute("""
            UPDATE cssk_fs_statement_line_def
               SET kind = %s, account_formula = %s,
                   account_formula_correction = %s
             WHERE version_id = %s AND code = %s
               AND (kind IS DISTINCT FROM %s
                    OR account_formula IS DISTINCT FROM %s
                    OR account_formula_correction IS DISTINCT FROM %s)
        """, (*(vals.get(f) or None for f in FIELDS), found[0], code,
              *(vals.get(f) or None for f in FIELDS)))
        changed += cr.rowcount
    _logger.info("l10n_sk_fs 19.0.1.5.0: %s UZPODv14 row definition(s) corrected",
                 changed)
