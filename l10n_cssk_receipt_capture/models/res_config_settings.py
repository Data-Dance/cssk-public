# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cssk_receipt_journal_id = fields.Many2one(
        related="company_id.cssk_receipt_journal_id", readonly=False)
    cssk_receipt_expense_account_id = fields.Many2one(
        related="company_id.cssk_receipt_expense_account_id", readonly=False)
    cssk_receipt_bill_detail = fields.Selection(
        related="company_id.cssk_receipt_bill_detail", readonly=False)
    cssk_receipt_auto_create_partner = fields.Boolean(
        related="company_id.cssk_receipt_auto_create_partner", readonly=False)
