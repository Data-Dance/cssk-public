# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Domain repeated: Odoo drops a string domain on a related field.
    cssk_receipt_expense_product_id = fields.Many2one(
        related="company_id.cssk_receipt_expense_product_id", readonly=False,
        domain="[('can_be_expensed', '=', True)]")
    cssk_receipt_capture_on_expense_upload = fields.Boolean(
        related="company_id.cssk_receipt_capture_on_expense_upload",
        readonly=False)
