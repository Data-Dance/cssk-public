# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    cssk_receipt_journal_id = fields.Many2one(
        "account.journal", string="Receipt Journal",
        domain="[('type', '=', 'purchase')]",
        help="Journal for vendor receipts created from captured fiscal "
             "receipts. Defaults to the company's first purchase journal.")
    cssk_receipt_expense_account_id = fields.Many2one(
        "account.account", string="Receipt Expense Account",
        help="Default expense account for captured receipt lines. Fuel, meals "
             "and the rest are usually re-coded afterwards; this is the "
             "landing account.")
    cssk_receipt_bill_detail = fields.Selection(
        [
            ("summary", "One line per VAT rate"),
            ("lines", "One line per receipt item"),
        ],
        string="Receipt Bill Detail", default="summary", required=True,
        help="Per VAT rate posts exactly the base the seller reported and "
             "cannot drift. Per item is easier to read; the posted tax is "
             "still checked against the receipt's own recap, and the document "
             "is refused if they disagree.")
    cssk_receipt_auto_create_partner = fields.Boolean(
        string="Auto-create Seller", default=False,
        help="Create the seller from the receipt's own identifiers when no "
             "partner matches, instead of parking the receipt.")
