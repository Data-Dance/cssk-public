# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""shvies_forma is R or N, never B / O / E.

The DPHSHV structure documents exactly two values — "R - souhrnné hlášení,
N - následné souhrnné hlášení" — and § 102 odst. 8 knows no opravné hlášení.
The types are ``noupdate``, so the XML value is corrected here. Statements
already exported keep their attachment: what was filed stays as filed.
"""
import logging

_logger = logging.getLogger(__name__)

MAPPING = {"dphshv_type_B": "R", "dphshv_type_O": "N", "dphshv_type_E": "N"}


def migrate(cr, version):
    if not version:
        return
    for xmlid, value in MAPPING.items():
        cr.execute("""
            UPDATE cssk_ec_summary_statement_type t
               SET fa_xml_value = %s
              FROM ir_model_data d
             WHERE d.model = 'cssk.ec.summary.statement.type'
               AND d.module = 'l10n_cz_ec_sales' AND d.name = %s
               AND d.res_id = t.id
               AND t.fa_xml_value IS DISTINCT FROM %s
        """, (value, xmlid, value))
        if cr.rowcount:
            _logger.info("l10n_cz_ec_sales: %s now exports shvies_forma=%s",
                         xmlid, value)
