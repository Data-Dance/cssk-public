from odoo import fields, models


class AccountAssetProfile(models.Model):
    """Tax-depreciation defaults carried by the OCA asset profile.

    Assets created from a profile inherit these (see the create override on
    ``account.asset``), so the tax group/method need not be set asset by asset.
    """

    _inherit = "account.asset.profile"

    tax_depreciation_enabled = fields.Boolean(string="Track Tax Depreciation")
    tax_class_id = fields.Many2one(
        "account.asset.tax.class", string="Tax Depreciation Group")
    tax_method = fields.Selection(
        [
            ("linear", "Straight-line"),
            ("accelerated", "Accelerated"),
            ("extraordinary", "Extraordinary (CZ §30a)"),
        ],
        string="Tax Method", default="linear",
    )
    tax_increased_first_year = fields.Selection(
        [("0", "None"), ("10", "+10 %"), ("15", "+15 %"), ("20", "+20 %")],
        string="Increased First-Year Rate", default="0",
    )
