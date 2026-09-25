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
        )

    def _fio_build_orders(self):
        self.ensure_one()
        return [
            order_from_item(
                self._fio_line_item(line),
                payment_reason=line.fio_payment_reason,
            )
            for line in self.payment_line_ids
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
        for order in self:
            if order.payment_method_id.code == FIO_XML_CODE:
                order._fio_validate()
        return super().draft2open()

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
