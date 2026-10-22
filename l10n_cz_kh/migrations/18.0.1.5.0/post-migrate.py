# Copyright 2026 Data Dance s.r.o.
"""Widen the CZ kontrolní hlášení version to the periods it can actually file.

The version record is declared under ``noupdate="1"``, so editing valid_from
in the data file reaches a FRESH install and never an existing one — Odoo's
convert.py gates on the file's noupdate attribute before it consults
ir_model_data. Without this migration the change is invisible on every
database that already has the record, which is every database that matters.

The value moves 2025-01-01 -> 2016-01-01. Czech EPO publishes one structure
and requires the current one for every period, so a version dated from 2025
was refusing periods it could file: 66 of 85 filed KH on the Money agenda.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute("""
        UPDATE cssk_control_statement_version v
           SET valid_from = DATE '2016-01-01'
          FROM ir_model_data d
         WHERE d.module = 'l10n_cz_kh'
           AND d.name = 'cz_kh_version_2025'
           AND d.model = 'cssk.control.statement.version'
           AND d.res_id = v.id
           AND v.valid_from > DATE '2016-01-01'
    """)
    if cr.rowcount:
        _logger.info("CZ KH version widened to 2016-01-01 (%s row)", cr.rowcount)
