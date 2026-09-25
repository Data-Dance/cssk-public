from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    # Legacy aliases of the canonical l10n_cssk_payment_symbols fields, kept
    # (stored, writable) for one release so ISDOC and customer code keep
    # working; a pre-migration merged old values into the canonical columns.
    variable_symbol = fields.Char(
        string="Variable Symbol",
        related="l10n_cssk_variable_symbol",
        store=True,
        readonly=False,
    )
    constant_symbol = fields.Char(
        string="Constant Symbol",
        related="l10n_cssk_constant_symbol",
        store=True,
        readonly=False,
    )
    specific_symbol = fields.Char(
        string="Specific Symbol",
        related="l10n_cssk_specific_symbol",
        store=True,
        readonly=False,
    )
