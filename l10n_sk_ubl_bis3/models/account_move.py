# -*- coding: utf-8 -*-
from odoo import _, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_sk_original_invoice_ref = fields.Char(
        string="Original invoice number(s)",
        copy=False,
        help="For a credit note that was not made from an invoice: the "
             "number(s) of the invoice(s) it corrects, separated by commas. "
             "They go into the e-invoice as the corrected invoices.",
    )

    def _l10n_sk_is_sent_as_slovak_einvoice(self):
        """Whether the customer of this sale document is on the Slovak format."""
        self.ensure_one()
        partner = self.commercial_partner_id.with_company(self.company_id)
        return self.is_sale_document() and partner.invoice_edi_format == 'ubl_bis3_sk'

    def _get_alerts(self):
        """Two things a Slovak e-invoice should carry and Odoo cannot demand.

        Warnings, not refusals. Without a payment-means field a cash invoice
        looks exactly like one whose bank account was forgotten, and a credit
        note covering many invoices (a rebate) has no single original, so a
        refusal would stop documents that are in order.
        """
        # EXTENDS 'account'
        alerts = super()._get_alerts()
        if self.state == 'cancel' or not self._l10n_sk_is_sent_as_slovak_einvoice():
            return alerts
        if (
            self.move_type == 'out_invoice'
            and not self.partner_bank_id
            and self.payment_state not in ('paid', 'in_payment')
        ):
            alerts['l10n_sk_ubl_bis3_no_bank_account'] = {
                'level': 'warning',
                'message': _(
                    "This invoice has no bank account, so the e-invoice will "
                    "not say where to pay. Set 'Recipient Bank' unless the "
                    "invoice is paid in cash or by card."
                ),
            }
        if self.move_type == 'out_refund':
            builder = self.env['account.edi.xml.ubl_sk']
            if not builder._l10n_sk_corrected_invoices(self) and not builder._l10n_sk_typed_original_numbers(self):
                alerts['l10n_sk_ubl_bis3_no_original_invoice'] = {
                    'level': 'warning',
                    'message': _(
                        "This credit note is not linked to an invoice, so the "
                        "e-invoice will not name the invoice it corrects. Fill "
                        "in 'Original invoice number(s)'."
                    ),
                }
        return alerts
