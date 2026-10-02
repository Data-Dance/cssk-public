# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import Command, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    recycling_fee_presentation = fields.Selection(
        related="company_id.recycling_fee_presentation"
    )

    def action_update_recycling_fee_lines(self):
        """Invoice the statutory fee as separate lines ('on top').

        One line per classification and VAT treatment, priced at the sum of
        the fees of the product lines it covers. The lines are regenerated from
        scratch each time, so the button is safe to press again after the
        order changes. Fees whose disclosure is prohibited (portable
        batteries) get no line: listing them separately is exactly what CZ
        § 85 odst. 3 and SK § 46 ods. 2 forbid, so they stay in the price.
        """
        for order in self:
            product = order.company_id.recycling_fee_product_id
            if not product:
                raise UserError(
                    self.env._(
                        "Set the recycling fee product in the Invoicing settings "
                        "of %(company)s first.",
                        company=order.company_id.name,
                    )
                )
            old_lines = order.order_line.filtered("is_recycling_fee_line")
            if old_lines.filtered("qty_invoiced"):
                raise UserError(
                    self.env._(
                        "The recycling fee of %(order)s is already invoiced "
                        "and can no longer be regenerated.",
                        order=order.name,
                    )
                )
            groups = defaultdict(float)
            for line in order.order_line - old_lines:
                for fee in line.ecotax_line_ids:
                    classification = fee.classification_id
                    if not classification.country_id or not classification.disclose:
                        continue
                    groups[(classification, line.tax_ids)] += fee.amount_total
            commands = [Command.unlink(line.id) for line in old_lines]
            for (classification, taxes), amount in groups.items():
                if order.currency_id.is_zero(amount):
                    continue
                included = taxes.filtered("price_include")
                if included:
                    # The tariff is net of VAT; a price-included tax would
                    # otherwise carve the VAT out of it and under-charge.
                    # Only the included taxes are grossed up: an excluded one
                    # is added on top by the line itself.
                    amount = included.compute_all(
                        amount, order.currency_id, handle_price_include=False
                    )["total_included"]
                phrases = classification._statutory_phrases() or {}
                label = phrases.get("fee_line") or self.env._("Recycling fee")
                commands.append(
                    Command.create(
                        {
                            "product_id": product.id,
                            "name": f"{label} — {classification.name}",
                            "product_uom_qty": 1.0,
                            "price_unit": amount,
                            "tax_ids": [Command.set(taxes.ids)],
                            "is_recycling_fee_line": True,
                            "sequence": 10000,
                        }
                    )
                )
            order.order_line = commands
        return True
