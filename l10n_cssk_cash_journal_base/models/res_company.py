# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    """Which set of books this company keeps.

    The regime is recorded on the company because it decides what the year has
    to produce, not how a document is posted: the books are double-entry in
    every regime. ``pu`` is the default, so installing this module changes
    nothing until someone says otherwise.

    ``ju`` (jednoduché účtovníctvo) is **Slovak only**. The Czech Republic
    closed it to sole traders — § 1f zákona 563/1991 Sb. leaves it to small
    non-profits — so offering it to a Czech company would invite a filing that
    does not exist.
    """

    _inherit = "res.company"

    cssk_bookkeeping_regime = fields.Selection(
        [
            ("pu", "Double-entry (podvojné účtovníctvo / účetnictví)"),
            ("de", "Tax records (daňová evidencia / daňová evidence)"),
            ("ju", "Single-entry accounting (jednoduché účtovníctvo, SK only)"),
            ("pausal", "Flat-rate expenses (paušálne výdavky / paušální výdaje)"),
        ],
        string="Bookkeeping Regime",
        default="pu", required=True,
    )
    cssk_cash_journal_start = fields.Date(
        string="Cash Journal Starts",
        help="First date the denník covers. Earlier payments are left alone, "
             "which is what a mid-year migration needs.",
    )

    @api.constrains("cssk_bookkeeping_regime", "country_id")
    def _check_cssk_bookkeeping_regime(self):
        for company in self:
            if company.cssk_bookkeeping_regime != "ju":
                continue
            if company.country_id.code == "CZ":
                raise ValidationError(_(
                    "Jednoduché účetnictví is not open to a Czech sole trader "
                    "(§ 1f zákona 563/1991 Sb. leaves it to small "
                    "non-profits). Use tax records (daňová evidence) instead.",
                ))
