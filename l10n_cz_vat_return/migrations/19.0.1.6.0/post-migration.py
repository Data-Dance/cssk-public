# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Import of goods was charged to the supplier, not self-assessed.

`l10n_cz` gives ř. 7/8 (*Dovoz zboží*) a single tax leg where every other
self-assessed row gets two. Self-assessed VAT is not charged by the supplier --
you owe the state, not the vendor -- so the legs must cancel on the document.
Measured on the shipped Czech chart with a 1 000 CZK vendor bill:

    21% EU G   untaxed 1000.00  tax   0.00  TOTAL 1000.00
    21% EX G   untaxed 1000.00  tax 210.00  TOTAL 1210.00

The second asks the user to pay 1 210 against a 1 000 invoice. It also leaves
the move unbalanced, whereupon Odoo adds an automatic balancing line and posts
it anyway -- on a seven-year Czech import that put 912.87 onto 261000 *Peníze
na cestě*, an account the document never touched, and it was found only by
comparing account by account against the source's own trial balance.

ř. 9 (*pořízení nového dopravního prostředku*) is deliberately NOT repaired:
the deduction there is not automatic, so its single leg may be intended.

Already-posted moves are NOT rewritten, for the reason 19.0.1.5.0 gives: they
carry the repartition that was configured when they posted, and correcting
them is a reload rather than a migration step.
"""
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([("chart_template", "=", "cz")])
    if not companies:
        return
    touched = companies._cz_tag_selfassessed_deduction()
    _logger.info(
        "l10n_cz_vat_return: %s repartition item(s) adjusted across %s Czech "
        "company(ies) for the ř. 7/8 deduction", touched, len(companies),
    )
