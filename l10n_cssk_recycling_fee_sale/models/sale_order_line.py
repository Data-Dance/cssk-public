# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    is_recycling_fee_line = fields.Boolean(
        copy=False,
        help="A separate recycling-fee line generated for the 'on top' "
        "presentation. Regenerated from the product lines, never edited.",
    )

    def _get_new_vals_list(self):
        """Same market filter and currency rule as on the invoice line — see
        ``account.move.line._get_new_vals_list`` in l10n_cssk_recycling_fee."""
        self.ensure_one()
        company = self.company_id or self.order_id.company_id or self.env.company
        commands = []
        for product_line in self.product_id.all_ecotax_line_product_ids:
            classification = product_line.classification_id
            if not classification._applies_to_company(company):
                continue
            if classification.country_id:
                vals = {
                    "classification_id": classification.id,
                    "product_force_amount": product_line.force_amount,
                }
            else:
                vals = {
                    "classification_id": classification.id,
                    "force_amount_unit": product_line.force_amount,
                }
            commands.append(Command.create(vals))
        return commands

    def _prepare_invoice_line(self, **optional_values):
        """Carry the product's fixed amount to the invoice as well.

        ``account_ecotax_sale`` copies only the classification and OCA's
        document-currency override; without ``product_force_amount`` a
        distributor's invoice would fall back to the scheme tariff.
        """
        res = super()._prepare_invoice_line(**optional_values)
        if "ecotax_line_ids" in res:
            res["ecotax_line_ids"] = [
                Command.create(
                    {
                        "classification_id": fee.classification_id.id,
                        "force_amount_unit": fee.force_amount_unit,
                        "product_force_amount": fee.product_force_amount,
                    }
                )
                for fee in self.ecotax_line_ids
            ]
        return res
