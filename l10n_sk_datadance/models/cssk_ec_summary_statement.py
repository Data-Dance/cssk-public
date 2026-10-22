# Copyright 2026 Data Dance s.r.o.
# Data Dance Proprietary License v1.0 — see the LICENSE file.
"""Súhrnný výkaz → reconcile-with-priznanie action (umbrella module)."""
from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools.misc import format_amount

_ICON = {"ok": "✅", "mismatch": "⚠️"}


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
        """Porovnanie súhrnného výkazu ↔ DPH priznanie (r14)."""
        self.ensure_one()
        vat_return = self._find_vat_return()
        if not vat_return:
            raise UserError(_(
                "No computed DPH priznanie found for this period — compute the "
                "VAT return for %(df)s – %(dt)s first.",
                df=self.date_from, dt=self.date_to))
        recon = self.env["l10n.sk.dph.reconciliation"]
        rows = recon.reconcile_sv_dph(self, vat_return)
        body = ["<b>%s</b> (%s):<ul>" % (
            _("Porovnanie súhrnného výkazu ↔ priznanie"), vat_return.name)]
        for r in rows:
            body.append("<li>%s %s — SV %s / priznanie %s (rozdiel %s)</li>" % (
                _ICON.get(r["status"], ""), r["label"],
                format_amount(self.env, r["left"], self.currency_id),
                format_amount(self.env, r["right"], self.currency_id),
                format_amount(self.env, r["diff"], self.currency_id)))
        body.append("</ul>")
        warnings = recon.check_kontroly_sv_dph(self, vat_return)
        if warnings:
            body.append("<b>%s</b><ul>%s</ul>" % (
                _("Upozornenia:"),
                "".join("<li>%s</li>" % w["detail"] for w in warnings)))
        self.message_post(body="".join(body))
        return {
            "type": "ir.actions.client", "tag": "display_notification",
            "params": {
                "title": _("Porovnanie SV ↔ priznanie"),
                "message": (_("%d upozornení — pozri záznam.", len(warnings))
                            if warnings else _("SV a priznanie sú konzistentné.")),
                "type": "warning" if warnings else "success", "sticky": False,
            },
        }
