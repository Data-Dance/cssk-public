# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""DPPO → reconcile-with-účtovná-závierka action (umbrella module)."""
from odoo import _, models
from odoo.exceptions import UserError


class CSSKIncomeTaxReturn(models.Model):
    _inherit = "cssk.income.tax.return"

    def _find_uzpod(self):
        """The UZPODv14 účtovná závierka covering this DPPO period."""
        self.ensure_one()
        uz = self.env["l10n.sk.uzpod"].search([
            ("company_id", "=", self.company_id.id),
            ("date_from", "<=", self.date_to),
            ("date_to", ">=", self.date_from),
        ], order="date_to desc")
        exact = uz.filtered(
            lambda u: u.date_from == self.date_from and u.date_to == self.date_to)
        return (exact or uz)[:1]

    def action_reconcile_vzs(self):
        """Porovnanie účtovnej závierky (VZS) ↔ DPPO r100 — on screen."""
        self.ensure_one()
        uzpod = self._find_uzpod()
        if not uzpod:
            raise UserError(_(
                "No UZPODv14 účtovná závierka found for this period — create "
                "the financial statements for %(df)s – %(dt)s first.",
                df=self.date_from, dt=self.date_to))
        recon = self.env["l10n.sk.dph.reconciliation"]
        details = {e["desc"]: e["detail"]
                   for e in recon.check_kontroly_vzs_dppo(uzpod, self)}
        # ``reconcile_vzs_dppo`` reads VZS-first; the screen reads
        # THIS-filing-first, on every comparator, so the left column always
        # holds the record the user is standing on. Flipped here rather than
        # in the reconciliation, which other callers and its tests share.
        self._cssk_upsert_comparison_rows(
            [{"code": r["block"], "label": r["label"],
              "filed": r["right"], "computed": r["left"], "diff": -r["diff"],
              "kind": recon.recon_kind(r["status"]),
              "detail": details.get(r["label"])}
             for r in recon.reconcile_vzs_dppo(uzpod, self)],
            "filing", _("účtovná závierka %s", uzpod.display_name))
        return self._cssk_comparison_action(
            "filing", _("DPPO ↔ účtovná závierka — %s", self.display_name))
