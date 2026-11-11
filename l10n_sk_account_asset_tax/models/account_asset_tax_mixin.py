# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountAssetTaxMixin(models.AbstractModel):
    _inherit = "account.asset.tax.mixin"

    def _tax_entry_value_excluded(self):
        """The VAT § 85n leaves undeducted on a passenger vehicle.

        § 52zzzk ZDP (from 1. 1. 2026): VAT the payer has no right to deduct
        under § 85n of the VAT Act is not a tax expense, and on tangible
        assets "táto nie je súčasťou vstupnej ceny". The books still
        capitalise it — the accounting acquisition cost includes it — so it
        comes off the entry value the tax board proposes, and the difference
        reaches the return through the book-versus-tax comparison.

        Read from the asset's bill lines: the undeducted legs of taxes
        flagged ``l10n_sk_par85n`` (``l10n_sk_vehicle_expense``) that were
        booked on the line's own account. A share of a line — an asset
        created per unit — takes the same share of its VAT."""
        excluded = super()._tax_entry_value_excluded()
        Tax = self.env["account.tax"]
        if (self._tax_get_country_code() != "SK"
                or "l10n_sk_par85n" not in Tax._fields):
            return excluded
        lines = self._tax_source_move_lines()
        taxes = lines.tax_ids.filtered("l10n_sk_par85n")
        if not taxes:
            return excluded
        vat = sum(lines._tax_capitalised_tax_by_line(taxes=taxes).values())
        if not vat:
            return excluded
        base = sum(lines.mapped("balance"))
        capitalised = sum(lines._tax_capitalised_tax_by_line().values())
        full = base + capitalised
        if not full:
            # Lines that net to nothing say nothing about this asset's share.
            return excluded
        value = self._tax_get_entry_value()
        share = min(max(value / full, 0.0), 1.0)
        return excluded + self.company_id.currency_id.round(vat * share)
