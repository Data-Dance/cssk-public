# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""DPH priznanie → reconcile-with-účtovníctvo action (umbrella module)."""
from odoo import _, models
from odoo.exceptions import UserError


class CSSKVatReturn(models.Model):
    _inherit = "cssk.vat.return"

    def _l10n_sk_check_slovak_filing(self):
        """The comparison reads Slovak rows; on another country's filing it
        would compare figures that mean something else."""
        if self.country_id.code != "SK":
            raise UserError(_(
                "This comparison is for Slovak filings. %(name)s belongs to "
                "a company filing in %(country)s.",
                name=self.display_name,
                country=self.country_id.name or "?"))

    def action_reconcile_books(self):
        """Porovnanie priznania s účtovníctvom (účet 343 + tržby).

        The result goes to the comparison screen, not to the chatter. A
        reconciliation that is re-run whenever anything changes does not
        become an audit trail by being posted — it becomes a thread nobody
        can read, and it buries the record it claims to be. The rows
        themselves are the record: queryable, and they carry what the
        accountant said about each one.
        """
        self.ensure_one()
        self._l10n_sk_check_slovak_filing()
        recon = self.env["l10n.sk.dph.reconciliation"]
        rows = recon.reconcile_dph_books(self)
        # ``check_kontroly_*`` derives its guidance from these same rows and
        # titles each warning with the row's own label, so the advice lands on
        # the row it is about rather than in a list beside it.
        details = {w["desc"]: w["detail"]
                   for w in recon.check_kontroly_dph_books(self)}
        self._cssk_upsert_comparison_rows(
            [{"code": r["block"], "label": r["label"],
              "filed": r["left"], "computed": r["right"], "diff": r["diff"],
              "kind": recon.recon_kind(r["status"]),
              "detail": details.get(r["label"])}
             for r in rows],
            "ledger", _("účtovníctvo — účet 343 a účtová trieda 60"))
        return self._cssk_comparison_action(
            "ledger", _("Priznanie ↔ účtovníctvo — %s", self.display_name))
