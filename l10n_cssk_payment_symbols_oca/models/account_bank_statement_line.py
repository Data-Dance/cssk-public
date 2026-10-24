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
        over-payment keeps its proposal and stays for a person.

        Every proposal here is reconciled only after the whole batch has been
        proposed (``_do_auto_reconcile``), so a journal item one line of this
        import takes is still open while the next line looks. Two payments of
        one invoice in one statement were both given its full residual, the
        second reconcile raised, and as this runs inside ``create()`` the
        whole import was lost. What earlier lines took is therefore tracked
        here, and a line finds only what they left open."""
        done = proposed = exhausted = self.browse()
        # aml id -> amount of its residual an earlier line of the batch will
        # reconcile
        claimed = {}
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
            currency = st_line.currency_id
            amls = amls.filtered(
                lambda aml: not currency.is_zero(
                    aml.amount_residual - claimed.get(aml.id, 0.0)
                )
            )
            if not amls:
                # Its document was paid by an earlier line of this import: a
                # second payment is for a person, and OCA's matcher would only
                # propose the same item again.
                exhausted |= st_line
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
            taking = {}
            for aml in amls.sorted(lambda aml: (aml.date_maturity or aml.date, aml.id)):
                if currency.is_zero(remaining) or (remaining > 0) != (
                    st_line.amount > 0
                ):
                    break
                available = aml.amount_residual - claimed.get(aml.id, 0.0)
                taken = remaining if abs(remaining) <= abs(available) else available
                reconcile_auxiliary_id, lines = st_line._get_reconcile_line(
                    aml,
                    "other",
                    is_counterpart=True,
                    max_amount=taken,
                    reconcile_auxiliary_id=reconcile_auxiliary_id,
                    move=True,
                )
                data += lines
                taking[aml.id] = taken
                remaining -= taken
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
                # Only a line that will be reconciled takes anything: a
                # proposal left for a person reconciles nothing.
                for aml_id, taken in taking.items():
                    claimed[aml_id] = claimed.get(aml_id, 0.0) + taken
            else:
                proposed |= st_line
        # A line with a proposal by symbol is neither handed on (OCA's own
        # match would overwrite it with a guess) nor returned as not done (the
        # caller would reset it to the default proposal).
        not_done, done_by_oca = super(
            AccountBankStatementLine, self - done - proposed - exhausted
        )._do_auto_reconcile_invoices()
        return not_done | exhausted, done | done_by_oca
