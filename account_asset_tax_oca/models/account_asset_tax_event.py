from odoo import fields, models


class AccountAssetTaxEvent(models.Model):
    """Add the asset relation that the core leaves to the bridge."""

    _inherit = "account.asset.tax.event"

    asset_id = fields.Many2one(
        "account.asset", string="Asset", required=True,
        ondelete="cascade", index=True,
    )
