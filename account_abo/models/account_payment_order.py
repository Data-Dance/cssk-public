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

    def _abo_line_item(self, line):
        text = line.communication or ''
        return BankPaymentItem(
            partner_bank=line.partner_bank_id,
            amount=line.amount_currency,
            currency_name=line.currency_id.name,
            vs=resolve_symbol('VS', line.variable_symbol, text),
            ks=resolve_symbol('KS', line.constant_symbol, text),
            ss=resolve_symbol('SS', line.specific_symbol, text),
            message=line.communication or '',
            date=line.date or fields.Date.context_today(self),
            label=line.display_name,
        )

    def _abo_build_items(self):
        return self._bankfile_items(self._abo_line_item)

    # ------------------------------------------------------------------
    # One item per grouped payment when the group nets a credit note.
    # Declared identically by account_abo, account_multicash,
    # account_payment_kb_best and account_payment_fio, which stay
    # independently installable; Odoo collapses the duplicates.
    # ------------------------------------------------------------------

    def _bankfile_line_groups(self):
        """The payment lines, in the groups ``draft2open`` makes one
        ``account.payment`` of (same key, same switch)."""
        self.ensure_one()
        groups = {}
        for line in self.payment_line_ids:
            key = (
                line.payment_line_hashcode()
                if self.payment_mode_id.group_lines
                else line.id
            )
            groups[key] = groups.get(key, line.browse()) | line
        return list(groups.values())

    def _bankfile_items(self, line_item):
        """One item per payment line, except where a group holds a line that
        is not positive — a credit note grouped with the invoice it reduces.

        Such a group is one transfer of the net amount: that is the payment
        ``draft2open`` books, and the only one a bank takes, since none accepts
        a zero or negative item. Groups of positive lines keep one item each,
        so every invoice still travels under its own variable symbol.
        """
        items = []
        for lines in self._bankfile_line_groups():
            if all(line.amount_currency > 0 for line in lines):
                items.extend(line_item(line) for line in lines)
            else:
                items.append(self._bankfile_net_item(lines, line_item))
        return items

    def _bankfile_net_item(self, lines, line_item):
        """The single item of a netted group, built on its first positive line.

        A symbol is the one the positive lines share (the credit note is
        deducted from those invoices, which is what the payee pairs the money
        with); positive lines with different symbols have no one right
        symbol, so none is sent rather than a wrong one.
        """
        ordered = lines.sorted(lambda line: (line.amount_currency <= 0, line.id))
        parts = [line_item(line) for line in ordered]
        positive = [
            part for line, part in zip(ordered, parts) if line.amount_currency > 0
        ] or parts

        def pick(attr):
            values = {getattr(part, attr) or "" for part in positive}
            return values.pop() if len(values) == 1 else ""

        currency = ordered[:1].currency_id
        total = sum(ordered.mapped("amount_currency"))
        return parts[0]._replace(
            amount=currency.round(total) if currency else total,
            vs=pick("vs"),
            ks=pick("ks"),
            ss=pick("ss"),
            message=" - ".join(
                dict.fromkeys(part.message for part in parts if part.message)
            ),
            label=", ".join(part.label for part in parts if part.label),
        )

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
