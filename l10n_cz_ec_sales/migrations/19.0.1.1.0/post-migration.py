# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Carry the re-dated EC sales list version into existing databases.

The record is ``noupdate="1"``, so an ordinary upgrade leaves its
``valid_from`` alone and every period before 2025 keeps resolving to no
version at all — which is not a wrong figure but no figure, and the statement
simply refuses to compute.

Clearing ``ir_model_data.noupdate`` does NOT help: the gate in
``convert.py`` reads the FILE's attribute and returns before the database row
is consulted. Only ``valid_from`` moves here, so it is written directly rather
than re-applying the file — no children to delete, no risk of a doubled grid.
"""
import logging

_logger = logging.getLogger(__name__)

NEW_VALID_FROM = "2010-01-01"


def migrate(cr, version):
    cr.execute(
        """
        UPDATE cssk_ec_summary_statement_version v
           SET valid_from = %s
          FROM ir_model_data d
         WHERE d.model = 'cssk.ec.summary.statement.version'
           AND d.module = %s
           AND d.res_id = v.id
           AND v.valid_from > %s
        """,
        (NEW_VALID_FROM, "l10n_cz_ec_sales", NEW_VALID_FROM),
    )
    if cr.rowcount:
        _logger.info(
            "l10n_cz_ec_sales: %s EC sales list version(s) re-dated from %s — periods "
            "before 2025 had no version and could not be computed at all",
            cr.rowcount, NEW_VALID_FROM,
        )
