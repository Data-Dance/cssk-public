# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class L10nSkAssetProtocolMixin(models.AbstractModel):
    _name = "l10n.sk.asset.protocol.mixin"
    _description = "Slovak asset protocols — data and the engine-neutral view"

    # An AbstractModel, so the SK data lives in a base that touches NEITHER
    # asset engine. The two engines both declare `account.asset` — OCA
    # `account_asset_management` even carries `excludes: ["account_asset"]` —
    # so exactly one of them is ever installed, and a module that hard-depended
    # on either could not serve the other edition.
    l10n_sk_inventory_number = fields.Char(
        string="Inventory number",
        help="Identifier in the asset register (inventárne číslo) — usually "
             "different from the internal code.",
    )
    l10n_sk_location = fields.Char(string="Location")
    l10n_sk_responsible_person_id = fields.Many2one(
        "res.partner", string="Responsible person"
    )
    l10n_sk_commissioning_note = fields.Text(
        string="Commissioning note",
        help="E.g. technical condition, accessories, documents forming an annex.",
    )
    l10n_sk_disposal_reason = fields.Text(string="Disposal reason")
    l10n_sk_disposal_method = fields.Selection(
        [
            ("sale", "Sale"),
            ("liquidation", "Liquidation"),
            ("donation", "Donation"),
            ("shortage", "Shortage or damage"),
            ("contribution", "Contribution to another company"),
            ("other", "Other"),
        ],
        string="Disposal method",
    )

    def _l10n_sk_protocol_values(self):
        """Figures the protocols print, under engine-neutral keys.

        The two asset engines name the same things differently — OCA has
        `purchase_value` / `value_depreciated` / `profile_id`, Enterprise has
        `original_value` / (derived) / `model_id` — so each bridge maps its own
        fields here and ONE set of QWeb templates serves both.
        """
        self.ensure_one()
        return {
            "name": self.display_name,
            "inventory_number": self.l10n_sk_inventory_number,
            "acquisition_date": False,
            "purchase_value": 0.0,
            "depreciated": 0.0,
            "residual": 0.0,
            "plan": "",
            "disposal_date": False,
            "currency": self.env.company.currency_id,
        }
