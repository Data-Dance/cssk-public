from odoo import _, fields, models


class AccountAssetTaxCompute(models.TransientModel):
    """Batch (re)computation of tax-depreciation boards.

    Operates on the assets passed in the context (``active_ids`` for
    ``account.asset``) or, when launched with none, on every asset that tracks
    tax depreciation. Filed lines (whose fiscal year has been closed) are always
    preserved; only the open tail of each board is regenerated.

    The wizard does not declare a relational field to ``account.asset`` so that
    the core module stays independent of the EE / OCA asset implementation; it
    resolves the model at runtime (a bridge is always installed in practice).
    """

    _name = "account.asset.tax.compute"
    _description = "Compute Tax Depreciation Boards"

    only_enabled = fields.Boolean(
        string="Only assets tracking tax depreciation", default=True,
    )
    asset_count = fields.Integer(string="Selected assets", readonly=True)

    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self.env.context.get("active_ids") or []
        if self.env.context.get("active_model") == "account.asset":
            res["asset_count"] = len(active_ids)
        return res

    def _target_assets(self):
        Asset = self.env["account.asset"]
        active_ids = self.env.context.get("active_ids") or []
        if active_ids and self.env.context.get("active_model") == "account.asset":
            assets = Asset.browse(active_ids)
        else:
            assets = Asset.search([("tax_depreciation_enabled", "=", True)])
        if self.only_enabled:
            assets = assets.filtered("tax_depreciation_enabled")
        return assets

    def action_compute(self):
        self.ensure_one()
        assets = self._target_assets()
        assets.compute_tax_depreciation_board()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "title": _("Tax depreciation recomputed"),
                "message": _("%d asset(s) processed.", len(assets)),
                "sticky": False,
            },
        }
