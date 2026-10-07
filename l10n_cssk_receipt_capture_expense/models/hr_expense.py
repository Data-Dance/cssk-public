# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class HrExpense(models.Model):
    _inherit = "hr.expense"

    cssk_receipt_id = fields.Many2one(
        "cssk.receipt", string="Captured receipt", readonly=True, index=True,
        ondelete="set null", copy=False)

    @api.model
    def create_expense_from_attachments(self, attachment_ids=None, view_type="list"):
        """Also create a captured receipt per attachment, and try to read it.

        Odoo's own flow creates one bare "Untitled Expense" per uploaded image
        and leaves the amounts at zero for the Enterprise OCR to fill. This
        keeps that behaviour and, in addition, hands each attachment to the
        capture providers — so a Slovak receipt whose QR a provider can read
        comes back with the seller's exact figures rather than nothing.
        """
        expense_ids = super().create_expense_from_attachments(
            attachment_ids=attachment_ids, view_type=view_type)
        if not self.env.company.cssk_receipt_capture_on_expense_upload:
            return expense_ids
        expenses = self.browse(
            expense_ids if isinstance(expense_ids, list) else [])
        for expense in expenses:
            attachment = self.env["ir.attachment"].search(
                [("res_model", "=", "hr.expense"), ("res_id", "=", expense.id)],
                limit=1)
            if not attachment:
                continue
            receipt = self.env["cssk.receipt"]._create_from_attachment(
                attachment, {"company_id": expense.company_id.id})
            expense.cssk_receipt_id = receipt.id
            if not receipt._candidate_providers():
                # Nothing installed can read it; the expense stays as Odoo left
                # it and the receipt waits for a QR payload or an AI provider.
                continue
            try:
                receipt.action_capture()
            except Exception:  # noqa: BLE001 - never break an upload
                _logger.exception(
                    "Receipt capture failed for attachment %s", attachment.id)
                continue
            if receipt.state == "captured":
                expense._cssk_apply_captured_receipt(receipt)
        return expense_ids

    def _cssk_apply_captured_receipt(self, receipt):
        """Fill a freshly uploaded expense from a receipt that read cleanly.

        Only the single-rate case is applied in place: a receipt carrying two or
        three VAT rates cannot be one expense, so it is left for *Create
        Expenses* on the receipt, which splits it properly.
        """
        self.ensure_one()
        rows = receipt.tax_summary_ids
        if len(rows) != 1:
            return False
        tax = receipt._tax_for_rate(rows.vat_rate)
        if not tax or not tax.price_include:
            return False
        vals = {
            "name": receipt.display_name,
            "date": receipt.issue_date and receipt.issue_date.date(),
            "total_amount_currency": receipt.amount_total,
            "tax_ids": [fields.Command.set(tax.ids)],
        }
        if receipt.partner_id:
            vals["vendor_id"] = receipt.partner_id.id
        self.write(vals)
        return True
