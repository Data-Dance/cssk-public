# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""VS/KS/SS payment symbols on the OCA payment line for the BEST exporter.

Identical to the ones declared by account_abo and account_multicash, so the
modules stay independently installable (Odoo collapses the duplicate field declarations).
Symbol resolution (explicit value, else a token parsed from the communication)
lives in ``account_cz_bankfile_base.utils.common.resolve_symbol`` and is applied
by the payment-order hook.
"""
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountPaymentLine(models.Model):
    _inherit = 'account.payment.line'

    variable_symbol = fields.Char(
        string="Variable Symbol", size=10,
        help="Czech/Slovak payment Variable Symbol (VS). Up to 10 digits. "
             "If empty, falls back to a `VS:` token in the communication.",
    )
    constant_symbol = fields.Char(
        string="Constant Symbol", size=4,
        help="Czech/Slovak payment Constant Symbol (KS). Up to 4 digits. "
             "If empty, falls back to a `KS:` token in the communication.",
    )
    specific_symbol = fields.Char(
        string="Specific Symbol", size=10,
        help="Czech/Slovak payment Specific Symbol (SS). Up to 10 digits. "
             "If empty, falls back to a `SS:` token in the communication.",
    )

    @api.constrains('variable_symbol', 'constant_symbol', 'specific_symbol')
    def _check_payment_symbols_cz(self):
        for rec in self:
            for label, value, max_len in (
                ('Variable Symbol', rec.variable_symbol, 10),
                ('Constant Symbol', rec.constant_symbol, 4),
                ('Specific Symbol', rec.specific_symbol, 10),
            ):
                if value and (not value.isdigit() or len(value) > max_len):
                    raise ValidationError(_(
                        "%(label)s must be a numeric string up to "
                        "%(max_len)s digits.", label=label, max_len=max_len,
                    ))
