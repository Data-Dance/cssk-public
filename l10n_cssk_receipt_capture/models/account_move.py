# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, models
from odoo.exceptions import UserError

from ..tools.amounts import reconciles


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        """Refuse to post deductible VAT from a receipt that does not allow it.

        The document is created without VAT and checked at creation — but it is
        created as a DRAFT for someone to review, and changing its partner or an
        account there can bring a default purchase tax back. This is the check
        that holds at the moment it counts.
        """
        receipts = self.env["cssk.receipt"].sudo().search([
            ("move_id", "in", self.ids), ("vat_deductible", "=", False)])
        for receipt in receipts:
            move = receipt.move_id
            if not reconciles(move.amount_tax, 0.0, tolerance=0.001):
                raise UserError(_(
                    "%(move)s carries %(tax).2f of VAT, but it comes from a "
                    "receipt whose VAT is not deductible (%(receipt)s). Remove "
                    "the VAT, or tick \u201cFull invoice held\u201d on the receipt "
                    "if you have one.",
                    move=move.display_name, tax=move.amount_tax,
                    receipt=receipt.display_name))
        return super()._post(soft=soft)
