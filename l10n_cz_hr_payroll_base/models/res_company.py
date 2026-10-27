# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_cz_partial_unemployment_pct = fields.Float(
        "Short-time work compensation (%)",
        default=100.0,
        help="Wage compensation for částečná nezaměstnanost (§ 209 of the "
        "Labour Code), as a percentage of average earnings. Without an "
        "agreement with the trade union, or an internal regulation where "
        "there is no union, it is a jiná překážka na straně zaměstnavatele "
        "under § 208 and paid in full: leave 100 %. Enter the agreed rate "
        "only when such an agreement or regulation exists; payslips never "
        "pay less than the statutory minimum of 60 %.",
    )

    @api.constrains("l10n_cz_partial_unemployment_pct")
    def _check_l10n_cz_partial_unemployment_pct(self):
        for company in self:
            if not 0.0 <= company.l10n_cz_partial_unemployment_pct <= 100.0:
                raise ValidationError(self.env._(
                    "The short-time work compensation must be between 0 % "
                    "and 100 %."))
