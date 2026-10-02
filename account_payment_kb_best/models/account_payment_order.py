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

    def _kb_best_build_items(self):
        items = []
        for line in self.payment_line_ids:
            text = line.communication or ""
            items.append(BankPaymentItem(
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
                # the day, which KB requires and a per-file counter is not
                ref_id=line.id,
                iso_priority=getattr(line, "iso20022_priority", None),
                iso_charge_bearer=getattr(line, "iso20022_charge_bearer", None),
            ))
        return items

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
