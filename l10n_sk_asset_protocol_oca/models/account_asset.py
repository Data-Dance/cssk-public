# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountAsset(models.Model):
    _inherit = ["account.asset", "l10n.sk.asset.protocol.mixin"]
    _name = "account.asset"

    def _l10n_sk_protocol_values(self):
        """Map the OCA register's field names onto the neutral keys."""
        values = super()._l10n_sk_protocol_values()
        values.update(
            {
                "inventory_number": self.l10n_sk_inventory_number or self.code,
                "acquisition_date": self.date_start,
                "purchase_value": self.purchase_value,
                "depreciated": self.value_depreciated,
                "residual": self.value_residual,
                "plan": self.profile_id.display_name or "",
                "disposal_date": self.date_remove,
                "currency": self.currency_id,
            }
        )
        return values
