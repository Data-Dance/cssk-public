"""ABO file generation hooked onto the OCA payment order (CE variant).

Builds a normalized item list from the payment lines and delegates the actual
file rendering to ``account_cz_bankfile_base``.
"""
from odoo import fields, models

from odoo.addons.account_cz_bankfile_base.utils.abo import build_abo_file
from odoo.addons.account_cz_bankfile_base.utils.common import (
    BankPaymentItem, resolve_symbol,
)

_ABO_CODE = 'abo'


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    def _abo_build_items(self):
        items = []
        for line in self.payment_line_ids:
            text = line.communication or ''
            items.append(BankPaymentItem(
                partner_bank=line.partner_bank_id,
                amount=line.amount_currency,
                currency_name=line.currency_id.name,
                vs=resolve_symbol('VS', line.variable_symbol, text),
                ks=resolve_symbol('KS', line.constant_symbol, text),
                ss=resolve_symbol('SS', line.specific_symbol, text),
                message=line.communication or '',
                date=line.date or fields.Date.context_today(self),
                label=line.display_name,
            ))
        return items

    def generate_payment_file(self):
        self.ensure_one()
        if self.payment_method_id.code != _ABO_CODE:
            return super().generate_payment_file()
        file_bytes = build_abo_file(
            self.journal_id.bank_account_id, self.company_id.name,
            self._abo_build_items(),
        )
        filename = 'ABO-%s-%s.abo' % (
            self.journal_id.code or self.name,
            fields.Datetime.now().strftime('%Y%m%d%H%M%S'),
        )
        return (file_bytes, filename)
