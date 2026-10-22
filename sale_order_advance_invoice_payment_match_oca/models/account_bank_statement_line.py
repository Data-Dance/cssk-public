from odoo import models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    def _do_auto_reconcile(self, models_to_apply):
        """Advance-invoice matching before the OCA reconcile-model pass.
        _cssk_try_match_advance is a no-op unless the company opted in; a
        matched line is fully reconciled here, so the OCA pass is skipped
        for it.

        18.0 signature: ``_do_auto_reconcile(models)`` is per-record and
        receives the auto-reconcile ``account.reconcile.model`` candidates
        (19.0 uses ``reconcile_if_possible`` on a multi recordset)."""
        self.ensure_one()
        if not self.is_reconciled and self._cssk_try_match_advance():
            return None
        return super()._do_auto_reconcile(models_to_apply)
