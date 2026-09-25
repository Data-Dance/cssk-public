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
