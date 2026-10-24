# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    def _do_auto_reconcile_invoices(self):
        """Exact variable-symbol pass BEFORE OCA's label-in-reference match.

        Returns ``(not done, done)`` like the method it extends. A line is
        done only when the widget data balances (``can_reconcile``); an
        over-payment keeps its proposal and stays for a person."""
        done = proposed = self.browse()
        for st_line in self.filtered(
            lambda line: line.variable_symbol
            # foreign-currency lines are left to OCA and to a person: the
            # amounts below are compared in one currency
            and not line.foreign_currency_id
            and line.currency_id == line.company_id.currency_id
        ):
            amls = st_line._l10n_cssk_find_vs_counterpart_amls()
            if not amls:
                continue
            liquidity_lines, _suspense, _other = st_line._seek_for_lines()
            data = []
            reconcile_auxiliary_id = 1
            for line in liquidity_lines:
                reconcile_auxiliary_id, lines = st_line._get_reconcile_line(
                    line,
                    "liquidity",
                    reconcile_auxiliary_id=reconcile_auxiliary_id,
                    move=True,
                )
                data += lines
            remaining = st_line.amount
            currency = st_line.currency_id
            for aml in amls.sorted(lambda aml: (aml.date_maturity or aml.date, aml.id)):
                if currency.is_zero(remaining) or (remaining > 0) != (
                    st_line.amount > 0
                ):
                    break
                reconcile_auxiliary_id, lines = st_line._get_reconcile_line(
                    aml,
                    "other",
                    is_counterpart=True,
                    max_amount=remaining,
                    reconcile_auxiliary_id=reconcile_auxiliary_id,
                    move=True,
                )
                data += lines
                remaining -= aml.amount_residual
            st_line.reconcile_data_info = st_line._recompute_suspense_line(
                data,
                reconcile_auxiliary_id,
                st_line.manual_reference,
            )
            _logger.info(
                "auto reconcile - exact VS %s - st_line: %s proposes %s",
                st_line.variable_symbol,
                st_line.id,
                amls.ids,
            )
            if st_line.reconcile_data_info.get("can_reconcile"):
                done |= st_line
            else:
                proposed |= st_line
        # A line with a proposal by symbol is neither handed on (OCA's own
        # match would overwrite it with a guess) nor returned as not done (the
        # caller would reset it to the default proposal).
        not_done, done_by_oca = super(
            AccountBankStatementLine, self - done - proposed
        )._do_auto_reconcile_invoices()
        return not_done, done | done_by_oca
