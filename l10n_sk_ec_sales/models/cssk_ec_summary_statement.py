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
import re

from odoo import _, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_cssk_core.tools import split_street, statutory_whole

#: SK kód plnenia that report GOODS (0 tovar, 1 trojstranný obchod). Northern
#: Ireland (XI) belongs to the EU VAT area for goods only, so a service (2) to
#: an XI number is not a súhrnný výkaz supply.
SK_SV_GOODS_CODES = ("0", "1")


class CSSKEcSummaryStatement(models.Model):
    _inherit = "cssk.ec.summary.statement"

    # The last block of the hlavička — svdph20.xsd / svdph2010.xsd `konatel`,
    # `konatelTel`, `konatelEmail` (2020 only) and `datumVyhlasenia`. They
    # were exported empty: a legal person's výkaz names the person who files
    # it, and every výkaz is dated. Same fields as the Slovak DPH header.
    l10n_sk_country_code = fields.Char(related="country_id.code")
    l10n_sk_authorized_name = fields.Char(
        string="Konateľ / oprávnená osoba — meno a priezvisko (SK)",
        help="konatel: the statutory body or the person authorised to file "
        "the súhrnný výkaz for a legal person.")
    l10n_sk_authorized_phone = fields.Char(
        string="Konateľ / oprávnená osoba — telefón (SK)")
    l10n_sk_authorized_email = fields.Char(
        string="Konateľ / oprávnená osoba — e-mail (SK)",
        help="konatelEmail — carried by the 2020 vzor only.")
    l10n_sk_declaration_date = fields.Date(
        string="Dátum vyhlásenia (SK)",
        help="Date of the declaration that the figures are correct and "
        "complete. Left empty, the date of the XML export is used.")

    def _cssk_render_context(self):
        ctx = super()._cssk_render_context()
        if self.country_id.code == "SK":
            ctx["sk_ulica"], ctx["sk_cislo"] = split_street(
                self.company_id.partner_id)
            declared = (self.l10n_sk_declaration_date
                        or fields.Date.context_today(self))
            ctx["sk_datum_vyhlasenia"] = {
                "den": str(declared.day), "mesiac": str(declared.month),
                "rok": str(declared.year)}
        return ctx

    def _cssk_ec_is_delta(self):
        # § 80 ods. 8: the dodatočný súhrnný výkaz carries only the added or
        # corrected records. (An opravný one replaces the original whole.)
        if self.country_id.code == "SK":
            return self.statement_type_id.fa_xml_value == "D"
        return super()._cssk_ec_is_delta()

    def _cssk_ec_whole(self, value):
        if self.country_id.code == "SK":
            return self._sv_whole(value)
        return super()._cssk_ec_whole(value)

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

    def _sv_vies_codes(self):
        """Member-state codes as the poučenie lists them: the EU's ISO codes
        with Greece as EL, plus XI (Severné Írsko od 1. 1. 2021)."""
        eu = self.env.ref("base.europe", raise_if_not_found=False)
        codes = {"EL" if c == "GR" else c
                 for c in (eu.country_ids.mapped("code") if eu else [])}
        return codes | {"XI"}

    def _sv_country(self, line):
        """kodStatu: "Kód štátu je súčasťou IČ DPH nadobúdateľa tovaru alebo
        príjemcu služby" (Poučenie SVDPHv20) — the VAT number's own prefix,
        so Greece is EL and Northern Ireland XI, never the partner country's
        ISO code (GR, GB)."""
        vat = "".join((line.partner_vat or "").split()).upper()
        if len(vat) > 2 and vat[:2].isalpha():
            return vat[:2]
        code = (line.partner_country_code or "").upper()
        return "EL" if code == "GR" else code

    def _check_vies(self):
        """The base gate, with the poučenie's own country codes.

        The base accepts a line only when the partner's COUNTRY is in the EU,
        which refuses every Northern Ireland customer (their country is GB)
        although the poučenie lists XI. XI is accepted for goods only.
        """
        if self.country_id.code != "SK":
            return super()._check_vies()
        self.ensure_one()
        allowed = self._sv_vies_codes()
        invalid = []
        for line in self.line_ids:
            vat = "".join((line.partner_vat or "").split()).upper()
            code = self._sv_country(line)
            ok = (
                len(vat) >= 3 and vat[:2].isalpha() and code in allowed
                and (code != "XI" or line.transaction_code in SK_SV_GOODS_CODES)
            )
            if not ok:
                invalid.append("%s / %s / %s" % (
                    line.partner_country_code or "??", vat or "—",
                    line.transaction_code or "—"))
        if invalid:
            raise UserError(_(
                "The súhrnný výkaz cannot be exported — these lines have a "
                "missing or non-EU VAT number, or report a service to a "
                "Northern Ireland (XI) number, which is valid for goods only "
                "(hard block):\n%s") % "\n".join(invalid))

    def _sv_whole(self, value):
        """Súhrnný výkaz amounts: whole euros, half-up (SVDPHv20 poučenie).
        Ties and negatives round AWAY from zero (−9.7 → −10), unlike the
        ``int(x + 0.5)`` idiom which truncates toward zero."""
        return statutory_whole(value or 0.0)
