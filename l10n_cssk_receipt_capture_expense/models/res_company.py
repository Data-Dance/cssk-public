# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    cssk_receipt_expense_product_id = fields.Many2one(
        "product.product", string="Receipt Expense Category",
        domain="[('can_be_expensed', '=', True)]",
        help="Expense category used for expenses created from a captured "
             "receipt. Defaults to Odoo's general expense category.")
    cssk_receipt_capture_on_expense_upload = fields.Boolean(
        string="Capture on Expense Upload", default=True,
        help="When receipt images are uploaded in the Expenses app, create a "
             "captured receipt for each and try the capture providers.")
