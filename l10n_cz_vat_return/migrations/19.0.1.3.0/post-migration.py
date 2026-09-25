# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""ř43/ř44's tax is the NEGATIVE of what the deduction leg posts.

19.0.1.2.0 tagged the deduction and the base then matched the filed returns in
42 of 49 and 38 of 44 periods. The tax came out exactly inverted: -8 956 925.28
against a filed 8 688 149.60.

A self-assessed tax deducts on a **-100** repartition leg, so its balance is a
credit and reads negative; an ordinary purchase tax deducts on **+100** and
reads positive. ř40/ř41 collect the second and need no sign, ř43/ř44 collect
the first and do. Same shape as the SK r24 correction, and the fourth place in
one session where one sign was applied to two things stored with opposite
signs.
"""
import logging

_logger = logging.getLogger(__name__)

LINES = {"od_zdp23": "-VAT 43 Total", "od_zdp5": "-VAT 44 Total"}


def migrate(cr, version):
    for code, formula in LINES.items():
        cr.execute(
            """
            UPDATE cssk_vat_return_line_def d
               SET tag_formula = %s
              FROM cssk_vat_return_version v
             WHERE d.version_id = v.id
               AND d.code = %s
               AND d.tag_formula = %s
               AND v.country_id = (SELECT id FROM res_country WHERE code = 'CZ')
            """,
            (formula, code, formula.lstrip("-")),
        )
        if cr.rowcount:
            _logger.info(
                "l10n_cz_vat_return: %s now negates — a self-assessed "
                "deduction posts on the -100 leg", code)
