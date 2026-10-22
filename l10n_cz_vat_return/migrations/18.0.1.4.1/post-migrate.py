# Copyright 2026 Data Dance s.r.o.
"""Rename the CZ VAT return version away from a year it does not mean.

Cosmetic only in effect, and misleading enough to be worth a migration: the
record is named "DPHDP3 2025" while covering every period from
2016 onward, which is exactly the per-year reading this structure does not
have. ``noupdate="1"`` keeps the data file from correcting it in place.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute("""
        UPDATE cssk_vat_return_version v
           SET name = 'DPHDP3 (aktuální struktura)'
          FROM ir_model_data d
         WHERE d.module = 'l10n_cz_vat_return'
           AND d.name = 'dphdp3_version_2025'
           AND d.model = 'cssk.vat.return.version'
           AND d.res_id = v.id
           AND v.name <> 'DPHDP3 (aktuální struktura)'
    """)
    if cr.rowcount:
        _logger.info("CZ DPHDP3 version renamed (%s row)", cr.rowcount)
