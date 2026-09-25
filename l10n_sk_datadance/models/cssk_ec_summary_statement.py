# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Súhrnný výkaz → reconcile-with-priznanie action (umbrella module)."""
from odoo import _, models
from odoo.exceptions import UserError


class CSSKEcSummaryStatement(models.Model):
    _inherit = "cssk.ec.summary.statement"

    def _find_vat_return(self):
        self.ensure_one()
        returns = self.env["cssk.vat.return"].search([
            ("company_id", "=", self.company_id.id),
            ("state", "in", ("preview", "exported")),
            ("date_from", "<=", self.date_to),
            ("date_to", ">=", self.date_from),
        ], order="date_from desc")
        exact = returns.filtered(
            lambda r: r.date_from == self.date_from and r.date_to == self.date_to)
        return (exact or returns)[:1]

    def action_reconcile_dph(self):
        """Porovnanie súhrnného výkazu ↔ DPH priznanie (r14) — on screen."""
        self.ensure_one()
        vat_return = self._find_vat_return()
        if not vat_return:
            raise UserError(_(
                "No computed DPH priznanie found for this period — compute the "
                "VAT return for %(df)s – %(dt)s first.",
                df=self.date_from, dt=self.date_to))
        recon = self.env["l10n.sk.dph.reconciliation"]
        details = {w["desc"]: w["detail"]
                   for w in recon.check_kontroly_sv_dph(self, vat_return)}
        self._cssk_upsert_comparison_rows(
            [{"code": r["block"], "label": r["label"],
              "filed": r["left"], "computed": r["right"], "diff": r["diff"],
              "kind": recon.recon_kind(r["status"]),
              "detail": details.get(r["label"])}
             for r in recon.reconcile_sv_dph(self, vat_return)],
            "filing", _("DPH priznanie %s", vat_return.display_name))
        return self._cssk_comparison_action(
            "filing", _("SV ↔ priznanie — %s", self.display_name))
