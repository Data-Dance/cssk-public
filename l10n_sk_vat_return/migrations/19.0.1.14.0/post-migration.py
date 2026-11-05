# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""r14 is § 43 goods only, and r13 is every exempt supply.

Two corrections from the poučenie, the same wording in every vzor since 2012
(DPHv25 bod 31; r15/r16 in the vzory to 2020):

* **r14** — "základ dane za dodané tovary oslobodené od dane podľa § 43 ods. 1
  a 4". Stock ``l10n_sk`` also tags 14 on ``vy_eu_s`` (a § 15 service, which is
  not exempt and belongs on no row) and ``vy_eu_t`` (the first buyer of a
  trojstranný obchod, excluded in so many words). Both taxes lose the tag, and
  so do the lines already posted with them, or every service invoice booked so
  far would stay on r14.
* **r13** (r15 before 2021) — "základ dane za všetky dodané tovary a služby
  oslobodené od dane podľa § 28 až § 43, § 46, § 47, § 48 ods. 8": the total,
  which includes what r14 and r15 itemise ("Riadok 13 nie je súčtom riadkov 14
  a 15" — it is more than their sum, not apart from it). Its formula read tag
  13 alone, so an intra-EU supply of goods or an export reached r14 / r15 and
  never r13. Stock Odoo's own report totals 13 + 14 + 15 the same way.

``noupdate="1"`` keeps the data pass from changing the line definitions, so
they are updated here, and only where they still hold the old formula.
"""
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

#: version xmlid -> the code of its "oslobodené celkom" row
TOTAL_ROWS = {
    "dph_version_2025": "r13",
    "dph_version_2024": "r13",
    "dph_version_2020": "r15",
    "dph_version_2018": "r15",
    "dph_version_2012": "r15",
}


def migrate(cr, version):
    if not version:
        return
    for name, code in TOTAL_ROWS.items():
        cr.execute(
            """
            UPDATE cssk_vat_return_line_def d
               SET tag_formula = '-13|14|15'
              FROM ir_model_data x
             WHERE x.module = 'l10n_sk_vat_return'
               AND x.model = 'cssk.vat.return.version'
               AND x.name = %s
               AND d.version_id = x.res_id
               AND d.code = %s
               AND d.tag_formula = '-13'
            """,
            (name, code),
        )
        if cr.rowcount:
            _logger.info(
                "l10n_sk_vat_return: %s %s now totals tags 13, 14 and 15",
                name, code)
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([("chart_template", "=", "sk")])
    retagged = env["account.chart.template"]._cssk_sk_drop_r14_tag(companies)
    _logger.info(
        "l10n_sk_vat_return 19.0.1.14.0: tag 14 off vy_eu_s / vy_eu_t for %s "
        "company/companies, %s posted line(s) retagged",
        len(companies), retagged)
