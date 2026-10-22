# Copyright 2026 Data Dance s.r.o.
# Data Dance Proprietary License v1.0 — see the LICENSE file.
"""DPH priznanie → reconcile-with-účtovníctvo action (umbrella module)."""
from odoo import _, models
from odoo.tools.misc import format_amount

_ICON = {"ok": "✅", "mismatch": "⚠️", "info": "ℹ️"}


class CSSKVatReturn(models.Model):
    _inherit = "cssk.vat.return"

    def action_reconcile_books(self):
        """Porovnanie priznania s účtovníctvom (účet 343 + tržby)."""
        self.ensure_one()
        recon = self.env["l10n.sk.dph.reconciliation"]
        rows = recon.reconcile_dph_books(self)
        body = ["<b>%s</b>:<ul>" % _("Porovnanie priznania s účtovníctvom")]
        for r in rows:
            body.append("<li>%s %s — priznanie %s / účtovníctvo %s "
                        "(rozdiel %s)</li>" % (
                            _ICON.get(r["status"], ""), r["label"],
                            format_amount(self.env, r["left"], self.currency_id),
                            format_amount(self.env, r["right"], self.currency_id),
                            format_amount(self.env, r["diff"], self.currency_id)))
        body.append("</ul>")
        warnings = recon.check_kontroly_dph_books(self)
        if warnings:
            body.append("<b>%s</b><ul>%s</ul>" % (
                _("Upozornenia:"),
                "".join("<li>%s</li>" % w["detail"] for w in warnings)))
        self.message_post(body="".join(body))
        return {
            "type": "ir.actions.client", "tag": "display_notification",
            "params": {
                "title": _("Porovnanie s účtovníctvom"),
                "message": (_("%d upozornení — pozri záznam.", len(warnings))
                            if warnings else _("Priznanie sa zhoduje s účtom 343.")),
                "type": "warning" if warnings else "success", "sticky": False,
            },
        }
