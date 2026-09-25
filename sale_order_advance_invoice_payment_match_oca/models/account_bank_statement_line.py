from odoo import models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    def _do_auto_reconcile(self, reconcile_if_possible=True):
        """Advance-invoice matching before the OCA reconcile-model and
        invoice-matching passes. _cssk_try_match_advance is a no-op unless
        the company opted in; matched lines are fully reconciled and
        therefore skipped by the OCA passes."""
        matched = self.browse()
        for st_line in self:
            if not st_line.is_reconciled and st_line._cssk_try_match_advance():
                matched |= st_line
        return super(
            AccountBankStatementLine, self - matched
        )._do_auto_reconcile(reconcile_if_possible=reconcile_if_possible)
