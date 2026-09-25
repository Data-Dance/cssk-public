# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""ř43/ř44 reached no line of the DPHDP3, in every period, for every company.

`l10n_cz` tags only the DECLARATION of a self-assessed purchase: a reverse
charge or intra-EU acquisition carries its ř3/ř5/ř10/ř12 tags on the base and
+100 legs and leaves the **-100 leg bare**, so the deduction the taxpayer is
entitled to is computed by Odoo and reported nowhere. The chart defines no
`VAT 43`/`VAT 44` tag at all -- its list runs 40, 41, 42 and jumps to 47 -- so
the two line definitions were `kind='manual'` in consequence.

Measured against 59 filed Řádné returns of a real Czech company, 2021-07 ..
2026-05: ř43 and ř44 computed 0.00 in EVERY period against filed figures
totalling 94.5M of base and 14 534 001.54 of tax, while the output side of the
same returns agreed to within 0.03 %.

Two things this migration must do, because the version record is `noupdate="1"`
and the repartition lives on company data:

* re-point the four line definitions at their tags -- targeted, one field each,
  so there is nothing to delete and no risk of a doubled grid;
* tag the repartition of every existing Czech company's self-assessed purchase
  taxes, which a data file cannot reach at all.

Statements already computed keep their stored values -- they are what was filed.
Recompute a return deliberately to pick up the corrected lines.
"""
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

LINES = {
    "nar_zdp23": "VAT 43 Base", "od_zdp23": "VAT 43 Total",
    "nar_zdp5": "VAT 44 Base", "od_zdp5": "VAT 44 Total",
}


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for code, formula in LINES.items():
        cr.execute(
            """
            UPDATE cssk_vat_return_line_def d
               SET kind = 'tags', tag_formula = %s
              FROM cssk_vat_return_version v
             WHERE d.version_id = v.id
               AND d.code = %s
               AND d.kind = 'manual'
               AND v.country_id = (SELECT id FROM res_country WHERE code = 'CZ')
            """,
            (formula, code),
        )
        if cr.rowcount:
            _logger.info(
                "l10n_cz_vat_return: %s now collects %s", code, formula)

    companies = env["res.company"].search([("chart_template", "=", "cz")])
    if companies:
        touched = companies._cz_tag_selfassessed_deduction()
        _logger.info(
            "l10n_cz_vat_return: %s deduction repartition tag(s) added across "
            "%s Czech company(ies) -- ř43/ř44 reported nothing before this",
            touched, len(companies),
        )
