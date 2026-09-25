# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""SK súhrnný výkaz kontrolné pravidlá.

Source: Poučenie na vyplnenie súhrnného výkazu k DPH (FS SR) + § 80 zákona
č. 222/2004 Z. z. The kód plnenia identifies the supply type:
  0 = dodanie tovaru (intra-EU goods, § 43),
  1 = trojstranný obchod – prostredná osoba (§ 45),
  2 = dodanie služby (§ 9 ods. 1 with place of supply in the customer's MS).
Only these codes are accepted; any other value is portal-rejected.
"""
from odoo import _, models
from odoo.exceptions import UserError

from odoo.addons.l10n_cssk_core.tools import statutory_whole


class CSSKEcSummaryStatement(models.Model):
    _inherit = "cssk.ec.summary.statement"

    def _kontroly_valid_codes(self):
        if self.country_id.code == "SK":
            return {"0", "1", "2"}
        return super()._kontroly_valid_codes()

    def _cssk_preflight_export(self):
        """The svdph20 zaznam splits each customer VAT into kodStatu + idCislo
        by stripping the 2-letter prefix — a VAT whose prefix is not a
        plausible country code would be silently mis-split (or emitted
        whole), so fail early and name the offending lines. 'Plausible' =
        an existing ISO country code, or the two VAT-specific prefixes EL
        (Greece) and XI (Northern Ireland)."""
        res = super()._cssk_preflight_export()
        for rec in self:
            if rec.country_id.code != "SK":
                continue
            plausible = set(
                self.env["res.country"].search([]).mapped("code")
            ) | {"EL", "XI"}
            bad = [
                line for line in rec.line_ids
                if (line.partner_vat or "")[:2].upper() not in plausible
            ]
            if bad:
                labels = [
                    "%s / %s" % (line.partner_country_code or "??",
                                 line.partner_vat or "—")
                    for line in bad]
                detail = ", ".join(labels[:5])
                if len(labels) > 5:
                    detail += ", … (+%d)" % (len(labels) - 5)
                raise UserError(_(
                    "The súhrnný výkaz cannot be exported — %(n)d line(s) "
                    "carry a customer VAT number that does not start with a "
                    "plausible country code (fix the partner's Tax ID in "
                    "Contacts): %(refs)s", n=len(bad), refs=detail))
        return res

    def _sv_whole(self, value):
        """Súhrnný výkaz amounts: whole euros, half-up (SVDPHv20 poučenie).
        Ties and negatives round AWAY from zero (−9.7 → −10), unlike the
        ``int(x + 0.5)`` idiom which truncates toward zero."""
        return statutory_whole(value or 0.0)
