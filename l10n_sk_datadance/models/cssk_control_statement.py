# Copyright 2026 Data Dance s.r.o.
# Data Dance Proprietary License v1.0 — see the LICENSE file.
"""KV statement → reconcile-with-priznanie action (umbrella: both modules present)."""
from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools.misc import format_amount

_ICON = {"ok": "✅", "subset": "ℹ️", "over": "⚠️"}


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
        """Porovnanie KV ↔ DPH priznanie — posts the result to the chatter."""
        self.ensure_one()
        vat_return = self._find_vat_return()
        if not vat_return:
            raise UserError(_(
                "No computed DPH priznanie found for this period — compute the "
                "VAT return for %(df)s – %(dt)s first.",
                df=self.date_from, dt=self.date_to))
        recon = self.env["l10n.sk.dph.reconciliation"]
        rows = recon.reconcile(self, vat_return)
        lines = ["<b>%s</b> (%s):<ul>" % (
            _("Porovnanie KV ↔ DPH priznanie"), vat_return.name)]
        for r in rows:
            lines.append(
                "<li>%s %s — KV %s / priznanie %s (rozdiel %s)</li>" % (
                    _ICON.get(r["status"], ""), r["label"],
                    format_amount(self.env, r["kv"], self.currency_id),
                    format_amount(self.env, r["dp"], self.currency_id),
                    format_amount(self.env, r["diff"], self.currency_id)))
        lines.append("</ul>")
        warnings = recon.check_kontroly(self, vat_return)
        if warnings:
            lines.append("<b>%s</b><ul>" % _("Upozornenia:"))
            lines += ["<li>%s</li>" % w["detail"] for w in warnings]
            lines.append("</ul>")
        self.message_post(body="".join(lines))
        return {
            "type": "ir.actions.client", "tag": "display_notification",
            "params": {
                "title": _("Porovnanie KV ↔ priznanie"),
                "message": (_("%d upozornení — pozri záznam.", len(warnings))
                            if warnings else _("KV a priznanie sú konzistentné.")),
                "type": "warning" if warnings else "success", "sticky": False,
            },
        }
