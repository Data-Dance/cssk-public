from odoo import _, fields, models
from odoo.exceptions import UserError


class Vrp2FiscalizeWizard(models.TransientModel):
    """Ask how the invoice was paid before registering it in VRP2.

    VRP2 records the form of each payment. A card payment is tržba just as
    cash is (§ 2 písm. u) zákona č. 384/2025 Z. z. from 1 January 2026;
    § 2 písm. z) zákona č. 289/2008 Z. z. before), so both are fiscalized —
    but as what they were, and only cash is rounded (§ 3 ods. 4 zákona
    č. 18/1996 Z. z.). The buttons used to send every invoice as CASH.
    """

    _name = "vrp2.fiscalize.wizard"
    _description = "Fiscalize invoices in VRP2"

    move_ids = fields.Many2many("account.move", string="Invoices", required=True)
    payment_type = fields.Selection(
        [("CASH", "Cash"), ("CARD", "Card")],
        string="Paid by",
        required=True,
        help="How the customer paid. Cash is rounded to 0.05 € when the "
        "register rounds; a card payment never is.",
    )

    def action_fiscalize(self):
        self.ensure_one()
        if not self.move_ids:
            raise UserError(_("Select the invoices to fiscalize."))
        receipts = self.move_ids._vrp2_fiscalize(self.payment_type)
        if len(self.move_ids) == 1:
            filename = "VRP2-%s.pdf" % (
                self.move_ids.name or "receipt").replace("/", "_")
        else:
            filename = "VRP2-receipts.pdf"
        return self.move_ids._vrp2_merged_pdf_action(receipts, filename)
