from odoo import models


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    def _prepare_default_reversal(self, move):
        """No made-up reference on a Slovak supplier's credit note.

        Odoo writes "Reversal of: BILL/…" into the reference, which is where
        the supplier's number of the credit note belongs and which C.2 files
        as FO. Left empty, the user types the number from the supplier's
        document, and posting asks for it if they do not."""
        vals = super()._prepare_default_reversal(move)
        if (move.move_type == "in_invoice"
                and move.company_id.account_fiscal_country_id.code == "SK"):
            vals["ref"] = False
        return vals
