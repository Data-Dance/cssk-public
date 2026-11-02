# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""VS/KS/SS and the platební titul on the OCA payment line.

The symbol fields are declared identically to ``account_abo`` and
``account_multicash`` so the modules stay independently installable — Odoo
collapses duplicate declarations.
"""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.account_fio_base.utils.payment_reason import (
    payment_reason_selection,
)


class AccountPaymentLine(models.Model):
    _inherit = "account.payment.line"

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
    fio_payment_reason = fields.Selection(
        selection=lambda self: payment_reason_selection(),
        string="Platební titul",
        help="ČNB payment reason. Fio requires one on every foreign payment "
             "and, for accounts at its Slovak branch, on a Europlatba above "
             "EUR 50 000. Defaults from the partner.",
    )

    @api.constrains("variable_symbol", "constant_symbol", "specific_symbol")
    def _check_payment_symbols_cz(self):
        for rec in self:
            for label, value, max_len in (
                ("Variable Symbol", rec.variable_symbol, 10),
                ("Constant Symbol", rec.constant_symbol, 4),
                ("Specific Symbol", rec.specific_symbol, 10),
            ):
                if value and (not value.isdigit() or len(value) > max_len):
                    raise ValidationError(_(
                        "%(label)s must be a numeric string up to "
                        "%(max_len)s digits.", label=label, max_len=max_len,
                    ))

    @api.onchange("partner_id")
    def _onchange_partner_fio_payment_reason(self):
        for line in self:
            if line.partner_id and not line.fio_payment_reason:
                line.fio_payment_reason = line.partner_id.fio_payment_reason

    @api.model_create_multi
    def create(self, vals_list):
        """Default the platební titul from the partner.

        On create as well as on change: payment lines are usually generated
        from invoices by ``account_payment_order``, where no onchange runs.
        """
        lines = super().create(vals_list)
        for line in lines:
            if not line.fio_payment_reason and line.partner_id:
                line.fio_payment_reason = line.partner_id.fio_payment_reason
        return lines
