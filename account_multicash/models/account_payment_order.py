"""MultiCash file generation hooked onto the OCA payment order (CE variant).

Builds a normalized item list from the payment lines and delegates the actual
file rendering to ``account_cz_bankfile_base``.
"""
from odoo import fields, models, _
from odoo.exceptions import UserError

from odoo.addons.account_cz_bankfile_base.utils.multicash import build_multicash_file
from odoo.addons.account_cz_bankfile_base.utils.common import (
    BankPaymentItem, resolve_symbol,
)

_MULTICASH_CODES = (
    'multicash_cfd', 'multicash_cfu', 'multicash_cfa', 'multicash_mt101',
)
_FILE_EXTENSIONS = {
    'multicash_cfd': 'cfd', 'multicash_cfu': 'cfu',
    'multicash_cfa': 'cfa', 'multicash_mt101': 'mt101',
}


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    def _multicash_build_items(self):
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
                partner=line.partner_id,
                ref_id=line.id,
                iso_priority=getattr(line, 'iso20022_priority', None),
                iso_charge_bearer=getattr(line, 'iso20022_charge_bearer', None),
            ))
        return items

    def generate_payment_file(self):
        self.ensure_one()
        code = self.payment_method_id.code
        if code not in _MULTICASH_CODES:
            return super().generate_payment_file()
        if code in ('multicash_cfa', 'multicash_mt101'):
            bank = self.journal_id.bank_account_id.bank_id
            if not bank or not bank.bic:
                raise UserError(_(
                    "Journal %(j)s must have a bank with a BIC configured to "
                    "export %(c)s files.", j=self.journal_id.name, c=code.upper(),
                ))
        file_bytes = build_multicash_file(
            self.journal_id.bank_account_id, self.company_id.partner_id,
            self.company_id.name, self._multicash_build_items(), code,
            batch_type=self.payment_type,
        )
        filename = '%s-%s-%s.%s' % (
            code.replace('multicash_', '').upper(),
            self.journal_id.code or self.name,
            fields.Datetime.now().strftime('%Y%m%d%H%M%S'),
            _FILE_EXTENSIONS[code],
        )
        return (file_bytes, filename)
