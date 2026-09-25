# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""KV statement → reconcile-with-priznanie action (umbrella: both modules present)."""
from odoo import _, models
from odoo.exceptions import UserError


class CSSKControlStatement(models.Model):
    _inherit = "cssk.control.statement"

    def _find_vat_return(self):
        """The computed DPH return covering this KV period (exact match first)."""
        self.ensure_one()
        domain = [
            ("company_id", "=", self.company_id.id),
            ("state", "in", ("preview", "exported")),
            ("date_from", "<=", self.date_to),
            ("date_to", ">=", self.date_from),
        ]
        returns = self.env["cssk.vat.return"].search(domain, order="date_from desc")
        exact = returns.filtered(
            lambda r: r.date_from == self.date_from and r.date_to == self.date_to)
        return (exact or returns)[:1]

    def action_reconcile_dph(self):
        """Porovnanie KV ↔ DPH priznanie — onto the comparison screen.

        The KV is a proper SUBSET of the priznanie, so a gap in that
        direction is structural and is recorded as expected rather than as a
        difference. Only KV > priznanie is impossible, and only that is
        flagged.
        """
        self.ensure_one()
        vat_return = self._find_vat_return()
        if not vat_return:
            raise UserError(_(
                "No computed DPH priznanie found for this period — compute the "
                "VAT return for %(df)s – %(dt)s first.",
                df=self.date_from, dt=self.date_to))
        recon = self.env["l10n.sk.dph.reconciliation"]
        details = {w["desc"]: w["detail"]
                   for w in recon.check_kontroly(self, vat_return)}
        self._cssk_upsert_comparison_rows(
            [{"code": r["block"], "label": r["label"],
              "filed": r["kv"], "computed": r["dp"], "diff": r["diff"],
              "kind": recon.recon_kind(r["status"]),
              "detail": details.get(r["label"])}
             for r in recon.reconcile(self, vat_return)],
            "filing", _("DPH priznanie %s", vat_return.display_name))
        return self._cssk_comparison_action(
            "filing", _("KV ↔ priznanie — %s", self.display_name))
