# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

# (field, label, max digits) — mirrors SYMBOL_SPECS on account.move.
PAYMENT_SYMBOL_SPECS = (
    ("l10n_cssk_variable_symbol", "Variable Symbol", 10),
    ("l10n_cssk_constant_symbol", "Constant Symbol", 4),
    ("l10n_cssk_specific_symbol", "Specific Symbol", 10),
)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    l10n_cssk_variable_symbol = fields.Char(
        string="Variable Symbol",
        copy=False,
        help="Variable symbol carried by the outgoing payment — pairs it "
        "with the supplier's document. Prefilled from the paid "
        "document(s) when unambiguous.",
    )
    l10n_cssk_constant_symbol = fields.Char(
        string="Constant Symbol",
        copy=False,
        help="Constant symbol — payment classification code. Optional.",
    )
    l10n_cssk_specific_symbol = fields.Char(
        string="Specific Symbol",
        copy=False,
        help="Specific symbol — additional payment identifier. Optional.",
    )

    @api.constrains(*(spec[0] for spec in PAYMENT_SYMBOL_SPECS))
    def _check_l10n_cssk_symbols(self):
        for payment in self:
            for field_name, label, size in PAYMENT_SYMBOL_SPECS:
                value = payment[field_name]
                if value and not re.fullmatch(r"\d{1,%d}" % size, value):
                    raise ValidationError(
                        _(
                            "%(label)s must be at most %(size)s digits "
                            "(got %(value)r).",
                            label=_(label),
                            size=size,
                            value=value,
                        )
                    )


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    @api.model
    def _l10n_cssk_symbol_vals(self, moves):
        """Symbol vals for a payment covering ``moves`` — a symbol is
        carried over only when every source document agrees on it, so a
        grouped payment over documents with different variable symbols
        gets none (the bank could not match it to one document anyway)."""
        vals = {}
        for field_name, _label, _size in PAYMENT_SYMBOL_SPECS:
            values = {move[field_name] or False for move in moves}
            if len(values) == 1 and (value := values.pop()):
                vals[field_name] = value
        return vals

    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)
        moves = batch_result["lines"].move_id
        payment_vals.update(self._l10n_cssk_symbol_vals(moves))
        return payment_vals

    def _create_payment_vals_from_batch(self, batch_result):
        payment_vals = super()._create_payment_vals_from_batch(batch_result)
        moves = batch_result["lines"].move_id
        payment_vals.update(self._l10n_cssk_symbol_vals(moves))
        return payment_vals
