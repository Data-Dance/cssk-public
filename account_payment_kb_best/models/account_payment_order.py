# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""BEST file generation hooked onto the OCA payment order (CE variant).

Builds the normalized item list from the payment lines and delegates the
record layout to ``account_kb_best_base``.
"""
from odoo import fields, models

from odoo.addons.account_cz_bankfile_base.utils.common import (
    BankPaymentItem,
    resolve_symbol,
)
from odoo.addons.account_kb_best_base.utils.best import (
    build_best_domestic,
    build_best_foreign,
)

from .account_payment_method import KB_BEST_CODES


class AccountPaymentOrder(models.Model):
    _inherit = "account.payment.order"

    def _kb_best_line_item(self, line):
        text = line.communication or ""
        return BankPaymentItem(
            partner_bank=line.partner_bank_id,
            amount=line.amount_currency,
            currency_name=line.currency_id.name,
            vs=resolve_symbol("VS", line.variable_symbol, text),
            ks=resolve_symbol("KS", line.constant_symbol, text),
            ss=resolve_symbol("SS", line.specific_symbol, text),
            message=text,
            date=line.date or fields.Date.context_today(self),
            label=line.display_name,
            partner=line.partner_id,
            # the database id makes Sekv_No unique across every file of
            # the day, which KB requires and a per-file counter is not (a
            # netted group keeps its first positive line's id, still unique)
            ref_id=line.id,
            iso_priority=line.iso20022_priority,
            iso_charge_bearer=line.iso20022_charge_bearer,
        )

    def _kb_best_build_items(self):
        return self._bankfile_items(self._kb_best_line_item)

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
        code = self.payment_method_id.code
        if code not in KB_BEST_CODES:
            return super().generate_payment_file()
        today = fields.Date.context_today(self)
        journal = self.journal_id
        account_currency = (journal.currency_id or self.company_id.currency_id).name
        file_id = (self.name or "")[:14]
        if code == "kb_best_domestic":
            data = build_best_domestic(
                journal.bank_account_id, self._kb_best_build_items(),
                account_currency, today, file_id=file_id,
                batch_type=self.payment_type,
            )
            kind = "DP"
        else:
            data = build_best_foreign(
                journal.bank_account_id, self.company_id.partner_id,
                self._kb_best_build_items(), account_currency, today,
                file_id=file_id,
            )
            kind = "ZP"
        filename = "BEST-%s-%s-%s.ikm" % (
            kind, journal.code or self.name,
            fields.Datetime.now().strftime("%Y%m%d%H%M%S"),
        )
        return (data, filename)
