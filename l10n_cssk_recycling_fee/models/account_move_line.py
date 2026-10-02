# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_new_vals_list(self):
        """Keep only the classifications of the selling company's market.

        A product sold in both countries carries a CZ and an SK classification;
        a Czech invoice must not charge the Slovak fee (and vice versa). The
        product's fixed amount is passed as ``product_force_amount`` — in the
        classification's currency — rather than OCA's ``force_amount_unit``,
        which is read in the document currency and would be wrong on any
        invoice not issued in CZK/EUR respectively.
        """
        self.ensure_one()
        company = self.company_id or self.move_id.company_id or self.env.company
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

    def _get_recycling_fee_texts(self):
        """Printable sentences for this invoice line (one per classification)."""
        self.ensure_one()
        move = self.move_id
        presentation = move.company_id.recycling_fee_presentation or "included"
        tax_included = any(
            tax.price_include for tax in self.tax_ids
        )
        texts = []
        for fee_line in self.ecotax_line_ids:
            text = fee_line._get_recycling_fee_text(
                presentation=presentation, tax_included=tax_included
            )
            if text:
                texts.append(text)
        return texts
