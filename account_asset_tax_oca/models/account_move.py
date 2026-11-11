from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _prepare_asset_vals(self, aml):
        """The asset's purchase value includes the tax capitalised on its line.

        A non-deductible VAT leg with no account of its own is booked on the
        asset account next to the line (a passenger car's undeducted half
        under SK § 85n, VAT with no right to deduct). The OCA register takes
        the line's balance alone, so the asset came out lower than the asset
        account by that VAT and depreciated less than the books hold. Odoo
        Assets adds it (``non_deductible_tax_value``); this does the same for
        the tax that is really on the asset account."""
        vals = super()._prepare_asset_vals(aml)
        extra = aml._tax_capitalised_tax_by_line().get(aml.id, 0.0)
        if extra and "purchase_value" in vals:
            vals["purchase_value"] += extra
        return vals
