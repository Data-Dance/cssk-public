# Copyright 2026 Data Dance s.r.o.
# Data Dance Proprietary License v1.0 — see the LICENSE file.
"""DPPO → reconcile-with-účtovná-závierka action (umbrella module)."""
from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools.misc import format_amount

_ICON = {"ok": "✅", "mismatch": "⚠️"}


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
        """Porovnanie účtovnej závierky (VZS) ↔ DPPO r100."""
        self.ensure_one()
        uzpod = self._find_uzpod()
        if not uzpod:
            raise UserError(_(
                "No UZPODv14 účtovná závierka found for this period — create "
                "the financial statements for %(df)s – %(dt)s first.",
                df=self.date_from, dt=self.date_to))
        recon = self.env["l10n.sk.dph.reconciliation"]
        rows = recon.reconcile_vzs_dppo(uzpod, self)
        body = ["<b>%s</b>:<ul>" % _("Porovnanie účtovnej závierky ↔ DPPO")]
        for r in rows:
            body.append("<li>%s %s — VZS %s / DPPO r100 %s (rozdiel %s)</li>" % (
                _ICON.get(r["status"], ""), r["label"],
                format_amount(self.env, r["left"], self.company_id.currency_id),
                format_amount(self.env, r["right"], self.company_id.currency_id),
                format_amount(self.env, r["diff"], self.company_id.currency_id)))
        body.append("</ul>")
        errors = recon.check_kontroly_vzs_dppo(uzpod, self)
        if errors:
            body.append("<b>%s</b><ul>%s</ul>" % (
                _("Nezhody:"),
                "".join("<li>%s</li>" % e["detail"] for e in errors)))
        self.message_post(body="".join(body))
        return {
            "type": "ir.actions.client", "tag": "display_notification",
            "params": {
                "title": _("Porovnanie VZS ↔ DPPO"),
                "message": (_("%d nezhôd — pozri záznam.", len(errors))
                            if errors else _("VZS a DPPO sa zhodujú.")),
                "type": "danger" if errors else "success", "sticky": False,
            },
        }
