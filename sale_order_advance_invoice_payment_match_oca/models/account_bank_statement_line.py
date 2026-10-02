from odoo import models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    def _do_auto_reconcile(self, reconcile_if_possible=True):
        """Advance-invoice matching before the OCA reconcile-model and
        invoice-matching passes. _cssk_try_match_advance is a no-op unless
        the company opted in; matched lines are fully reconciled and
        therefore skipped by the OCA passes.

        Only when reconciling: OCA also calls this with
        ``reconcile_if_possible=False`` merely to compute the proposal, from
        ``_compute_reconcile_data_info`` and ``_synchronize_to_moves``. Matching
        there applied the advance from inside a compute (a second time, when
        the first application's own partner write resynchronised the line),
        and skipped super() so the proposal was never set."""
        if not reconcile_if_possible:
            return super()._do_auto_reconcile(reconcile_if_possible=False)
        matched = self.browse()
        for st_line in self:
            if not st_line.is_reconciled and st_line._cssk_try_match_advance():
                matched |= st_line
        return super(
            AccountBankStatementLine, self - matched
        )._do_auto_reconcile(reconcile_if_possible=reconcile_if_possible)
