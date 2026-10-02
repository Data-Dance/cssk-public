# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountPaymentMode(models.Model):
    _inherit = "account.payment.mode"

    pay_on_post = fields.Boolean(
        string="Register payment on validation",
        help="Pay the invoice in full, in this mode's fixed journal, the "
        "moment it is posted — for a sale paid in cash or by card on the "
        "spot, where a separate payment step is only a chance to forget it.",
    )

    @api.constrains("pay_on_post", "bank_account_link", "fixed_journal_id")
    def _check_pay_on_post(self):
        for mode in self.filtered("pay_on_post"):
            if mode.bank_account_link != "fixed" or not mode.fixed_journal_id:
                raise ValidationError(_(
                    "Payment mode '%s' registers payments on validation, so "
                    "it needs a fixed journal to register them in.", mode.name))
