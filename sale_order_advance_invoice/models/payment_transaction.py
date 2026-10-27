from odoo import models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _create_payment(self, **extra_create_values):
        """Book an online payment of an advance invoice to the clearing account.

        Like *Register Payment* does: the tax document raised on the payment
        puts its receivable leg on the advance clearing account, and posting
        it reconciles the two there. A provider payment left on the
        customer's receivable never met the tax document.
        """
        orders = self.sale_order_ids
        clearing = self.provider_id.company_id.advance_received_account_id
        if (
            orders
            and all(orders.mapped("is_advance_invoice"))
            and clearing
            and "destination_account_id" not in extra_create_values
        ):
            extra_create_values["destination_account_id"] = clearing.id
        return super()._create_payment(**extra_create_values)
