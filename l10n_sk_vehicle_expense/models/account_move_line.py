# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    l10n_sk_fuel_split_done = fields.Boolean(
        string="Fuel split done",
        copy=False,
        help="Technical — marks both halves of a fuel line that has already "
             "been split, so a second run cannot compound the reclassification.",
    )
