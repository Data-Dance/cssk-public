# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Read v01 (čistý obrat) of the UZPODv14 version off the ledger.

It was transcribed as a ``manual`` row, which the generator skipped, so the
screen showed 0 while the filed XML read r01 off 601/602/604/606/607. (s113
had the same defect; 19.0.1.5.0 fixed it.) The data file is ``noupdate``, so
an existing database keeps the manual row unless it is written here.

Only a row still ``manual`` is touched: one somebody has since given a
formula of their own is left alone. A statement already computed keeps its
stored lines until it is recomputed; a figure typed into the row stays, as an
override.
"""

import logging

_logger = logging.getLogger(__name__)

ROWS = {
    "v01": "-601,-602,-604,-606,-607",
}


def migrate(cr, version):
    if not version:
        return
    cr.execute("""
        SELECT res_id FROM ir_model_data
         WHERE module = 'l10n_sk_fs' AND name = 'uzpod_v14'
           AND model = 'cssk.fs.statement.version'
    """)
    row = cr.fetchone()
    if not row:
        return
    for code, formula in ROWS.items():
        cr.execute("""
            UPDATE cssk_fs_statement_line_def
               SET kind = 'accounts', account_formula = %s
             WHERE version_id = %s AND code = %s AND kind = 'manual'
        """, [formula, row[0], code])
        if cr.rowcount:
            _logger.info(
                "l10n_sk_fs 19.0.1.6.0: UZPODv14 row %s now reads %s",
                code, formula)
