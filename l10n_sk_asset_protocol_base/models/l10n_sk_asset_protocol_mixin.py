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
    # § 10 ods. 1 písm. d) zákona 431/2002: every účtovný doklad carries the
    # date it was made out. Left empty, the protocol prints the day it is
    # printed — set it to keep a reprint identical.
    l10n_sk_commissioning_protocol_date = fields.Date(
        string="Commissioning protocol date",
        copy=False,
        help="Date the commissioning protocol was made out (dátum vyhotovenia "
             "účtovného dokladu, § 10 ods. 1 písm. d) zákona 431/2002). Empty: "
             "the protocol shows the day it is printed.",
    )
    l10n_sk_disposal_protocol_date = fields.Date(
        string="Disposal protocol date",
        copy=False,
        help="Date the disposal protocol was made out (dátum vyhotovenia "
             "účtovného dokladu, § 10 ods. 1 písm. d) zákona 431/2002). Empty: "
             "the protocol shows the day it is printed.",
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

        The three amounts must foot — ``purchase_value - depreciated ==
        residual`` — and they are the asset's own book figures: ``depreciated``
        is the accumulated depreciation (oprávky) only, never the residual
        written off on disposal, and ``residual`` is the net book value
        (zostatková cena), salvage value included.

        ``commissioning_number`` / ``disposal_number`` are the číselné
        označenie and ``*_doc_date`` the dátum vyhotovenia of § 10 ods. 1
        písm. a) and d) zákona 431/2002, filled in by
        :meth:`_l10n_sk_protocol_document_values` once a bridge has set the
        inventory number.
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

    def _l10n_sk_protocol_document_values(self):
        """The § 10 ods. 1 písm. a) and d) particulars of the two protocols.

        One asset has one zaradenie and one vyradenie, so its inventory
        number (or the register's own identifier the bridge falls back to)
        numbers both documents; the prefix tells them apart.
        """
        self.ensure_one()
        values = self._l10n_sk_protocol_values()
        ident = values.get("inventory_number") or str(self.id)
        today = fields.Date.context_today(self)
        values.update({
            "commissioning_number": "ZP-%s" % ident,
            "disposal_number": "VP-%s" % ident,
            "commissioning_doc_date": (
                self.l10n_sk_commissioning_protocol_date or today),
            "disposal_doc_date": self.l10n_sk_disposal_protocol_date or today,
        })
        return values
