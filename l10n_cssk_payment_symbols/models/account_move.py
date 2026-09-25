# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

# (field, label, max digits) — VS and SS are 10 digits, KS is 4.
SYMBOL_SPECS = (
    ("l10n_cssk_variable_symbol", "Variable Symbol", 10),
    ("l10n_cssk_constant_symbol", "Constant Symbol", 4),
    ("l10n_cssk_specific_symbol", "Specific Symbol", 10),
)


def _symbol_digits(value, size=10):
    """Digits of ``value``, keeping the LAST ``size`` — bank systems cap the
    variable symbol at 10 digits and the trailing digits are the significant
    ones of a document number."""
    return re.sub(r"\D", "", value or "")[-size:]


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_cssk_variable_symbol = fields.Char(
        string="Variable Symbol",
        compute="_compute_l10n_cssk_variable_symbol",
        store=True,
        readonly=False,
        recursive=True,
        help="Variable symbol — pairs the payment with the "
        "invoice (usually the invoice number, digits only).",
    )
    l10n_cssk_constant_symbol = fields.Char(
        string="Constant Symbol",
        compute="_compute_l10n_cssk_constant_symbol",
        store=True,
        readonly=False,
        help="Constant symbol — payment classification code "
        "(e.g. 0008 goods, 0308 services). Optional.",
    )
    l10n_cssk_specific_symbol = fields.Char(
        string="Specific Symbol",
        help="Specific symbol — additional payment identifier "
        "(used by insurers, leasing companies …). Optional.",
    )

    @api.depends(
        "name",
        "ref",
        "move_type",
        "reversed_entry_id.l10n_cssk_variable_symbol",
        "company_id.l10n_cssk_refund_vs_policy",
    )
    def _compute_l10n_cssk_variable_symbol(self):
        for move in self:
            move.l10n_cssk_variable_symbol = (
                move._l10n_cssk_default_variable_symbol()
            )

    def _l10n_cssk_default_variable_symbol(self):
        self.ensure_one()
        if self.move_type in ("out_invoice", "out_refund", "out_receipt"):
            if (
                self.move_type == "out_refund"
                and self.company_id.l10n_cssk_refund_vs_policy == "origin"
                and self.reversed_entry_id
            ):
                origin = self.reversed_entry_id
                return origin.l10n_cssk_variable_symbol or _symbol_digits(
                    origin.name
                )
            return _symbol_digits(self.name)
        if self.move_type in ("in_invoice", "in_refund", "in_receipt") and self.ref:
            return _symbol_digits(self.ref)
        return False

    @api.depends("move_type", "company_id.l10n_cssk_default_constant_symbol")
    def _compute_l10n_cssk_constant_symbol(self):
        for move in self:
            value = move.l10n_cssk_constant_symbol
            if not value and move.move_type in (
                "out_invoice",
                "out_refund",
                "out_receipt",
            ):
                value = move.company_id.l10n_cssk_default_constant_symbol
            move.l10n_cssk_constant_symbol = value or False

    @api.constrains(*(spec[0] for spec in SYMBOL_SPECS))
    def _check_l10n_cssk_symbols(self):
        for move in self:
            for field_name, label, size in SYMBOL_SPECS:
                value = move[field_name]
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

    def _get_invoice_computed_reference(self):
        """Company toggle: customer documents use the variable symbol as
        payment reference — core QR, UBL payment IDs and bank matching then
        carry the VS without any further glue."""
        self.ensure_one()
        if (
            self.company_id.l10n_cssk_payment_reference_use_vs
            and self.move_type in ("out_invoice", "out_refund", "out_receipt")
            and self.l10n_cssk_variable_symbol
        ):
            return self.l10n_cssk_variable_symbol
        return super()._get_invoice_computed_reference()

    def _generate_qr_code(self, silent_errors=False):
        """Expose the document's symbols to the QR generation stack — the
        res.partner.bank hooks never see the move, only communication
        strings, so the symbols travel via context."""
        self.ensure_one()
        symbols = {
            key: value
            for key, value in (
                ("variable_symbol", self.l10n_cssk_variable_symbol),
                ("constant_symbol", self.l10n_cssk_constant_symbol),
                ("specific_symbol", self.l10n_cssk_specific_symbol),
            )
            if value
        }
        move = self.with_context(cssk_payment_symbols=symbols) if symbols else self
        return super(AccountMove, move)._generate_qr_code(
            silent_errors=silent_errors
        )
