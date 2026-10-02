# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang


class AccountMove(models.Model):
    _inherit = "account.move"

    recycling_fee_disclosed = fields.Float(
        string="Recycling Fee Shown",
        digits="Ecotax",
        compute="_compute_recycling_fee_disclosed",
        help="Sum of the statutory recycling fees that are printed on this "
        "document. Portable-battery fees are excluded: they may not be shown.",
    )
    recycling_fee_statutory = fields.Boolean(
        compute="_compute_recycling_fee_disclosed",
        help="The document carries a CZ/SK statutory fee, so the CZ/SK "
        "presentation replaces OCA's generic 'Eco Part' column and total.",
    )

    @api.depends(
        "invoice_line_ids.ecotax_line_ids.amount_total",
        "invoice_line_ids.ecotax_line_ids.classification_id.disclose",
        "invoice_line_ids.ecotax_line_ids.classification_id.country_id",
    )
    def _compute_recycling_fee_disclosed(self):
        for move in self:
            fee_lines = move.invoice_line_ids.ecotax_line_ids.filtered(
                "classification_id.country_id"
            )
            move.recycling_fee_statutory = bool(fee_lines)
            move.recycling_fee_disclosed = sum(
                fee_lines.filtered("classification_id.disclose").mapped(
                    "amount_total"
                )
            )

    def _get_recycling_fee_total_text(self):
        """Label and amount of the document-level total, or ``False``.

        MŽP's model invoices close with "Příspěvek na recyklaci celkem bez
        DPH" — the sum of the per-line fees (guideline point 2.1 (iv)).
        """
        self.ensure_one()
        if not self.recycling_fee_disclosed:
            return False
        classification = self.invoice_line_ids.ecotax_line_ids.filtered(
            lambda f: f.classification_id.country_id
            and f.classification_id.disclose
        )[:1].classification_id
        phrases = classification._statutory_phrases()
        label = (
            phrases["total"]
            if phrases
            else self.env._("Recycling fee total (excl. VAT)")
        )
        amount = formatLang(
            self.env, self.recycling_fee_disclosed, currency_obj=self.currency_id
        )
        return label, amount

    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        # Price once more on the final invoice date and today's exchange rate:
        # ``_post`` may only now have set the date, and from here on the
        # lines are frozen (see ``ecotax.line.mixin._compute_ecotax``).
        fee_lines = posted.invoice_line_ids.ecotax_line_ids.filtered(
            "classification_id.country_id"
        )
        if fee_lines:
            fee_lines.with_context(recycling_fee_recompute=True)._compute_ecotax()
        posted._check_recycling_fee_rates()
        return posted

    def _check_recycling_fee_rates(self):
        """Refuse to post a fee that silently came out as zero.

        A line whose classification has no rate for the invoice date would
        otherwise print nothing and report nothing — the one outcome § 125
        odst. 2 písm. i) zákona č. 542/2020 Sb. sanctions, found only at an
        inspection.
        """
        missing = []
        for move in self.filtered(lambda m: m.move_type in ("out_invoice", "out_refund")):
            date = move.invoice_date or move.date
            for fee_line in move.invoice_line_ids.ecotax_line_ids:
                classification = fee_line.classification_id
                if not classification.country_id:
                    continue
                if fee_line.force_amount_unit or fee_line.product_force_amount:
                    continue
                if not classification._get_rate(date):
                    missing.append(
                        f"{move.name}: {fee_line.product_id.display_name} — "
                        f"{classification.display_name} ({date})"
                    )
        if missing:
            raise UserError(
                self.env._(
                    "No recycling fee rate is valid on the invoice date for:\n%s",
                    "\n".join(missing),
                )
            )
