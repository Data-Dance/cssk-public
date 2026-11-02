# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    def _do_auto_reconcile(self, models):
        """Exact variable-symbol pass BEFORE OCA's own rules.

        **18.0 delta, and it is the whole design.** 19.0's
        ``account_reconcile_oca`` proposes a counterpart for every line of the
        batch first and reconciles afterwards, so the 19.0 bridge hooks
        ``_do_auto_reconcile_invoices``, returns ``(not done, done)``, and has
        to track what earlier lines of the same import will take — two payments
        of one invoice were both given its full residual and the second
        reconcile raised inside ``create()`` (cssk-public#9).

        OCA 18.0 has no ``_do_auto_reconcile_invoices`` at all: ``_auto_reconcile``
        walks the batch and **this** method reconciles each line before the next
        one is looked at. So the hook is here, there is no batch to return, and
        #9 cannot arise — by the time the second payment looks, the first has
        already consumed the residual and the matcher sees what is left.
        The bridge ported from 19.0 overrode a method nothing calls here, which
        made the module inert; these tests had never run.

        A line whose proposal does not balance (an over-payment) keeps the
        proposal and stays for a person — it is deliberately NOT handed on to
        OCA, whose own match would overwrite it with a guess. So this returns
        without calling ``super()`` and leaves ``reconcile_data_info`` holding
        the VS-matched counterpart: that proposal is the output, not stale
        state, and it is what the widget shows whoever opens the line.
        """
        self.ensure_one()
        if self.is_reconciled or not self.variable_symbol:
            return super()._do_auto_reconcile(models)
        # foreign-currency lines are left to OCA and to a person: the exchange
        # counterpart OCA builds is not something to second-guess by symbol
        if (
            self.foreign_currency_id
            or self.currency_id != self.company_id.currency_id
        ):
            return super()._do_auto_reconcile(models)
        amls = self._l10n_cssk_find_vs_counterpart_amls()
        if not amls:
            return super()._do_auto_reconcile(models)

        # The proposal is built exactly as OCA's own `res['amls']` branch does
        # it, so the widget data, the exchange handling and the reconcile mode
        # are OCA's; only the choice of counterpart is ours.
        liquidity_lines, _suspense_lines, _other_lines = self._seek_for_lines()
        data = []
        for line in liquidity_lines:
            reconcile_auxiliary_id, lines = self._get_reconcile_line(
                line, "liquidity", move=True,
            )
            data += lines
        reconcile_auxiliary_id = 1
        amount = self.amount_currency or self.amount
        for aml in amls.sorted(lambda aml: (aml.date_maturity or aml.date, aml.id)):
            if self.currency_id.is_zero(amount) or (amount > 0) != (self.amount > 0):
                break
            reconcile_auxiliary_id, line_datas = self._get_reconcile_line(
                aml,
                "other",
                is_counterpart=True,
                max_amount=amount,
                reconcile_auxiliary_id=reconcile_auxiliary_id,
                move=True,
            )
            amount -= sum(line_data.get("amount") for line_data in line_datas)
            data += line_datas
        data = self._recompute_suspense_line(
            data, reconcile_auxiliary_id, self.manual_reference,
        )
        self.reconcile_data_info = data
        if not data.get("can_reconcile"):
            _logger.info(
                "VS %s matched %s on %s, but the proposal does not balance; "
                "left for a person.",
                self.variable_symbol, amls.move_id.ids, self.display_name,
            )
            return
        getattr(self, f"_reconcile_bank_line_{self.journal_id.reconcile_mode}")(
            self._prepare_reconcile_line_data(data["data"])
        )
