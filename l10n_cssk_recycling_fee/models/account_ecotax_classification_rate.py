# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountEcotaxClassificationRate(models.Model):
    """One entry of a collective scheme's price list, valid for a period.

    Schemes (ASEKOL, REMA, ELEKTROWIN, EKOLAMP, SEWA, Natur-Pack, ...) change
    their tariffs, usually on 1 January. An invoice must carry the rate that
    applied when it was issued, and a reissued or corrected document for an old
    period must still find the old rate, so a single amount on the
    classification (which is all OCA ``account_ecotax`` has) is not enough:
    the rates are kept as dated rows and chosen by the document date.
    """

    _name = "account.ecotax.classification.rate"
    _description = "Recycling Fee Rate"
    _order = "classification_id, date_from desc"

    classification_id = fields.Many2one(
        "account.ecotax.classification",
        required=True,
        index=True,
        ondelete="cascade",
    )
    date_from = fields.Date(string="Valid From", required=True)
    date_to = fields.Date(
        string="Valid To",
        help="Last day the rate applies. Leave empty for the rate in force.",
    )
    amount = fields.Float(
        string="Rate",
        digits="Ecotax",
        required=True,
        help="Fee per piece, or per kilogram for a weight-based "
        "classification, in the classification's currency and without VAT.",
    )
    currency_id = fields.Many2one(related="classification_id.currency_id")
    ecotax_type = fields.Selection(related="classification_id.ecotax_type")

    @api.constrains("date_from", "date_to", "classification_id")
    def _check_dates(self):
        """Two rates valid on the same day would make the invoice amount
        depend on record order, so overlaps are refused outright."""
        for rate in self:
            if rate.date_to and rate.date_to < rate.date_from:
                raise ValidationError(
                    self.env._(
                        "The rate of %(classification)s ends before it starts.",
                        classification=rate.classification_id.display_name,
                    )
                )
            for other in rate.classification_id.rate_ids - rate:
                starts_before_other_ends = (
                    not other.date_to or rate.date_from <= other.date_to
                )
                ends_after_other_starts = (
                    not rate.date_to or rate.date_to >= other.date_from
                )
                if starts_before_other_ends and ends_after_other_starts:
                    raise ValidationError(
                        self.env._(
                            "Two rates of %(classification)s overlap: "
                            "%(first)s and %(second)s.",
                            classification=rate.classification_id.display_name,
                            first=rate.date_from,
                            second=other.date_from,
                        )
                    )
