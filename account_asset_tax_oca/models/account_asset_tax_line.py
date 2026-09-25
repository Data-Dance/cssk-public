from odoo import fields, models


class AccountAssetTaxLine(models.Model):
    """Add the asset relation that the core leaves to the bridge."""

    _inherit = "account.asset.tax.line"
    _order = "asset_id, year_index, date_from"

    asset_id = fields.Many2one(
        "account.asset",
        string="Asset",
        required=True,
        ondelete="cascade",
        index=True,
    )
