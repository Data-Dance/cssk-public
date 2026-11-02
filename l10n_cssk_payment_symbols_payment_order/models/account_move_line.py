# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _prepare_payment_line_vals(self, payment_order):
        vals = super()._prepare_payment_line_vals(payment_order)
        move = self.move_id
        for move_field, line_field in (
            ("l10n_cssk_variable_symbol", "variable_symbol"),
            ("l10n_cssk_constant_symbol", "constant_symbol"),
            ("l10n_cssk_specific_symbol", "specific_symbol"),
        ):
            value = move[move_field]
            if value:
                vals[line_field] = value
        return vals
