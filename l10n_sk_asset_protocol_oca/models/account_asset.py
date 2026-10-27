# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountAsset(models.Model):
    _inherit = ["account.asset", "l10n.sk.asset.protocol.mixin"]
    _name = "account.asset"

    def _l10n_sk_protocol_values(self):
        """Map the OCA register's field names onto the neutral keys.

        Not ``value_depreciated`` / ``value_residual``: OCA's residual is the
        depreciation base (purchase value less salvage value) less what is
        written off, so with a salvage value the three printed amounts did
        not foot; and its ``value_depreciated`` counts the ``remove`` line, so
        after removal the oprávky swallowed the residual written off and the
        disposal protocol showed a zostatková cena of nil. The oprávky are the
        posted depreciation lines; the residual is what they leave of the
        purchase value.
        """
        values = super()._l10n_sk_protocol_values()
        depreciated = sum(
            self.depreciation_line_ids.filtered(
                lambda line: line.type == "depreciate"
                and (line.init_entry or line.move_check)
            ).mapped("amount")
        )
        values.update(
            {
                "inventory_number": self.l10n_sk_inventory_number or self.code,
                "acquisition_date": self.date_start,
                "purchase_value": self.purchase_value,
                "depreciated": depreciated,
                "residual": self.purchase_value - depreciated,
                "plan": self.profile_id.display_name or "",
                "disposal_date": self.date_remove,
                "currency": self.currency_id,
            }
        )
        return values
