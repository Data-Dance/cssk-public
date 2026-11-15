# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

# The ways a dlouhodobý majetek leaves the books, in the wording of Český
# účetní standard pro podnikatele č. 013, bod 5.4. Printed in Czech whatever
# the user's language: the protocol is a Czech document, and these are the
# standard's own terms, not interface labels.
DISPOSAL_METHOD_TERMS = {
    "sale": "prodej",
    "liquidation": "likvidace",
    "donation": "dar nebo jiný bezúplatný převod",
    "contribution": "vklad do jiné obchodní korporace",
    "legal_transfer": "převod na základě právních předpisů",
    "shortage": "škoda nebo manko",
    "personal_use": "převod z podnikání do osobního užívání",
    "other": "jiný",
}

# Způsob daňového odpisování, § 30 odst. 2 and § 30a zákona č. 586/1992 Sb.,
# keyed by the `tax_method` values of `account_asset_tax`.
TAX_METHOD_TERMS = {
    "linear": "rovnoměrné (§ 31)",
    "accelerated": "zrychlené (§ 32)",
    "extraordinary": "mimořádné (§ 30a)",
}


class L10nCzAssetProtocolMixin(models.AbstractModel):
    _name = "l10n.cz.asset.protocol.mixin"
    _description = "Czech asset protocols — data and the engine-neutral view"

    # An AbstractModel, so the CZ data lives in a base that touches NEITHER
    # asset engine. The two engines both declare `account.asset` — OCA
    # `account_asset_management` even carries `excludes: ["account_asset"]` —
    # so exactly one of them is ever installed, and a module that hard-depended
    # on either could not serve the other edition.
    l10n_cz_inventory_number = fields.Char(
        string="Inventory number",
        help="Identifier in the asset register (inventární číslo) — usually "
             "different from the internal code.",
    )
    l10n_cz_location = fields.Char(string="Location")
    l10n_cz_responsible_person_id = fields.Many2one(
        "res.partner", string="Responsible person"
    )
    l10n_cz_commissioning_note = fields.Text(
        string="Commissioning note",
        help="E.g. technical condition, accessories, documents forming an annex.",
    )
    # § 11 odst. 1 písm. d) zákona č. 563/1991 Sb.: every účetní doklad
    # carries the moment it was made out. Left empty, the protocol prints the
    # day it is printed — set it to keep a reprint identical.
    l10n_cz_commissioning_protocol_date = fields.Date(
        string="Commissioning protocol date",
        copy=False,
        help="Date the commissioning protocol was made out (okamžik vyhotovení "
             "účetního dokladu, § 11 odst. 1 písm. d) zákona č. 563/1991 Sb.). "
             "Empty: the protocol shows the day it is printed.",
    )
    l10n_cz_disposal_protocol_date = fields.Date(
        string="Disposal protocol date",
        copy=False,
        help="Date the disposal protocol was made out (okamžik vyhotovení "
             "účetního dokladu, § 11 odst. 1 písm. d) zákona č. 563/1991 Sb.). "
             "Empty: the protocol shows the day it is printed.",
    )
    l10n_cz_disposal_reason = fields.Text(string="Disposal reason")
    # The list of Český účetní standard pro podnikatele č. 013, bod 5.4.
    l10n_cz_disposal_method = fields.Selection(
        [
            ("sale", "Sale"),
            ("liquidation", "Liquidation"),
            ("donation", "Donation or other gratuitous transfer"),
            ("contribution", "Contribution to another business corporation"),
            ("legal_transfer", "Transfer under legal regulations"),
            ("shortage", "Damage or shortage"),
            ("personal_use", "Transfer from business to personal use"),
            ("other", "Other"),
        ],
        string="Disposal method",
    )

    def _l10n_cz_protocol_tax_values(self):
        """Odpisová skupina and způsob daňového odpisování, where known.

        Czech practice puts them on the zařazovací protokol, and the asset
        card is expected to hold "údaje o zvoleném postupu účetního a daňového
        odpisování" (ČÚS č. 013, bod 6.3). The data belongs to
        `account_asset_tax`, which this base must not depend on: it is read
        only when that module has put its fields on the register, and only
        for an asset in a Czech odpisová skupina (§ 30 odst. 1 zákona
        č. 586/1992 Sb.) with tax depreciation tracked.
        """
        self.ensure_one()
        empty = {"tax_group": "", "tax_method": ""}
        if not {"tax_depreciation_enabled", "tax_class_id", "tax_method"} <= set(
            self._fields
        ):
            return empty
        tax_class = self.tax_class_id
        if (
            not self.tax_depreciation_enabled
            or not tax_class
            or tax_class.country_code != "CZ"
        ):
            return empty
        return {
            "tax_group": str(tax_class.group_number),
            "tax_method": TAX_METHOD_TERMS.get(self.tax_method, ""),
        }

    def _l10n_cz_protocol_values(self):
        """Figures the protocols print, under engine-neutral keys.

        The two asset engines name the same things differently — OCA has
        `purchase_value` / `value_depreciated` / `profile_id`, Enterprise has
        `original_value` / (derived) / `model_id` — so each bridge maps its own
        fields here and ONE set of QWeb templates serves both.

        The three amounts must foot — ``purchase_value - depreciated ==
        residual`` — and they are the asset's own book figures: ``depreciated``
        is the accumulated depreciation (oprávky) only, never the residual
        written off on disposal, and ``residual`` is the net book value
        (zůstatková cena: ocenění less oprávky, ČÚS č. 013, bod 4.4), any
        expected residual value included.

        ``commissioning_number`` / ``disposal_number`` are the označení and
        ``*_doc_date`` the okamžik vyhotovení of § 11 odst. 1 písm. a) and d)
        zákona č. 563/1991 Sb., filled in by
        :meth:`_l10n_cz_protocol_document_values` once a bridge has set the
        inventory number.
        """
        self.ensure_one()
        values = {
            "name": self.display_name,
            "inventory_number": self.l10n_cz_inventory_number,
            "acquisition_date": False,
            "purchase_value": 0.0,
            "depreciated": 0.0,
            "residual": 0.0,
            "plan": "",
            "disposal_date": False,
            "disposal_method": DISPOSAL_METHOD_TERMS.get(
                self.l10n_cz_disposal_method, ""
            ),
            "currency": self.env.company.currency_id,
        }
        values.update(self._l10n_cz_protocol_tax_values())
        return values

    def _l10n_cz_protocol_document_values(self):
        """The § 11 odst. 1 písm. a) and d) particulars of the two protocols.

        One asset has one zařazení and one vyřazení, so its inventory
        number (or the register's own identifier the bridge falls back to)
        numbers both documents; the prefix tells them apart.
        """
        self.ensure_one()
        values = self._l10n_cz_protocol_values()
        ident = values.get("inventory_number") or str(self.id)
        today = fields.Date.context_today(self)
        values.update({
            "commissioning_number": "ZP-%s" % ident,
            "disposal_number": "VP-%s" % ident,
            "commissioning_doc_date": (
                self.l10n_cz_commissioning_protocol_date or today),
            "disposal_doc_date": self.l10n_cz_disposal_protocol_date or today,
        })
        return values
