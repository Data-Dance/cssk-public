# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""Fio XML generation and upload, hooked onto the OCA payment order."""

import base64

from odoo import _, fields, models
from odoo.exceptions import UserError

from odoo.addons.account_cz_bankfile_base.utils.common import (
    BankPaymentItem,
    resolve_symbol,
)
from odoo.addons.account_fio_base.utils.orders import (
    FioOrderError,
    account_from_country,
    build_fio_import_xml,
    order_from_item,
    validate_order,
)

from .account_payment_method import FIO_XML_CODE


class AccountPaymentOrder(models.Model):
    _name = "account.payment.order"
    _inherit = ["account.payment.order", "fio.upload.mixin"]

    # ------------------------------------------------------------------
    # building the file
    # ------------------------------------------------------------------

    def _fio_line_item(self, line):
        """One payment line → the shared ``BankPaymentItem``.

        The same tuple ABO and MultiCash consume, so the CZ/SK account parsing
        and the VS/KS/SS resolution are the ones already in production here.
        """
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
            label=line.name or line.display_name,
            partner=line.partner_id,
            ref_id=line.id,
            iso_priority=line.iso20022_priority,
            iso_charge_bearer=line.iso20022_charge_bearer,
        )

    def _fio_build_orders(self):
        self.ensure_one()
        # ref_id is the payment line; for a netted group, its first positive
        # line, whose platební titul the transfer carries.
        lines = self.payment_line_ids
        return [
            order_from_item(
                item,
                payment_reason=lines.browse(item.ref_id).fio_payment_reason,
            )
            for item in self._bankfile_items(self._fio_line_item)
        ]

    def _fio_validate(self):
        """Every problem in the order, in one message rather than one at a time."""
        self.ensure_one()
        problems = []
        # Fio serves CZ and SK on one API, and §6.3.2's platební-titul
        # threshold applies only to accounts held at the Slovak branch — so the
        # pre-flight has to know where the money leaves from, not just where it
        # goes.
        home_country = account_from_country(self.journal_id.bank_account_id)
        try:
            for order in self._fio_build_orders():
                problems.extend(validate_order(order, home_country))
        except FioOrderError as exception:
            problems.append(str(exception))
        if problems:
            raise UserError(_(
                "This payment order cannot be sent to Fio yet:\n\n%(problems)s",
                problems="\n".join("• %s" % problem for problem in problems),
            ))

    def draft2open(self):
        # EXTENDS account_payment_order — fail at confirmation, not at the
        # moment somebody is trying to get the payments out of the door.
        # After super(), not before: draft2open dates the lines, and the date
        # decides which lines are grouped (and so netted) into one transfer.
        # A refusal raises, which rolls the payments it created back.
        result = super().draft2open()
        for order in self:
            if order.payment_method_id.code == FIO_XML_CODE:
                order._fio_validate()
        return result

    def generate_payment_file(self):
        # EXTENDS account_payment_order
        self.ensure_one()
        if self.payment_method_id.code != FIO_XML_CODE:
            return super().generate_payment_file()
        if not self.journal_id.bank_account_id:
            raise UserError(_(
                "Journal %(journal)s has no bank account, so Fio cannot be told "
                "which account the money leaves.",
                journal=self.journal_id.display_name,
            ))
        try:
            payload = build_fio_import_xml(
                self._fio_build_orders(), self.journal_id.bank_account_id,
            )
        except FioOrderError as exception:
            raise UserError(str(exception)) from None
        filename = "FIO-%s-%s.xml" % (
            self.journal_id.code or self.name,
            fields.Datetime.now().strftime("%Y%m%d%H%M%S"),
        )
        return (payload, filename)

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

    # ------------------------------------------------------------------
    # fio.upload.mixin
    # ------------------------------------------------------------------

    def _fio_journal(self):
        self.ensure_one()
        return self.journal_id

    def _fio_can_upload(self):
        self.ensure_one()
        return self.state == "generated"

    def _fio_payload(self):
        """The file ``open2generated`` stored on the order."""
        self.ensure_one()
        attachment = self.env["ir.attachment"].search(
            [("res_model", "=", "account.payment.order"), ("res_id", "=", self.id)],
            order="id desc", limit=1,
        )
        if not attachment:
            raise UserError(_(
                "No payment file on this order — generate it first."
            ))
        return (base64.b64decode(attachment.datas), attachment.name)

    def action_fio_upload(self):
        # EXTENDS fio.upload.mixin — on success the order follows the OCA
        # workflow into "uploaded", which posts and reconciles the payments.
        result = super().action_fio_upload()
        if self.fio_upload_state == "sent" and self.state == "generated":
            self.generated2uploaded()
        return result
