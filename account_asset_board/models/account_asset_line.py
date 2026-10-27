# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AccountAssetLine(models.Model):
    _inherit = "account.asset.line"

    profile_id = fields.Many2one(
        related="asset_id.profile_id",
        string="Asset Profile",
        store=True,
        help="Stored asset profile, so that depreciation lines can be "
        "grouped by profile in the pivot/graph analysis.",
    )
    # OCA's remaining_value is a balance (what is left after the line), not a
    # movement: the pivot summed it over every line of a year, which is a
    # meaningless figure with monthly depreciation. Not a measure, then.
    remaining_value = fields.Monetary(aggregator=None)
