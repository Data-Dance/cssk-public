# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""CZ souhrnné hlášení (DPHSHV): country code, value rounding, XI.

Source: the DPHSHV EPO structure (``data/dphshv_epo2.xsd``) and § 102 zákona
č. 235/2004 Sb.
"""
import math

from odoo import _, models
from odoo.exceptions import UserError

#: k_pln_eu codes that report GOODS (0 dodání zboží, 1 přemístění, 2 třístranný
#: obchod). Northern Ireland (XI) is in the EU VAT area for goods only, so a
#: service (code 3) to an XI number does not belong in the hlášení.
CZ_SH_GOODS_CODES = ("0", "1", "2")


class CSSKEcSummaryStatement(models.Model):
    _inherit = "cssk.ec.summary.statement"

    def _cz_sh_vies_codes(self):
        """Member-state codes as the DPHSHV table lists them: the EU's ISO
        codes with Greece as EL, plus XI (Northern Ireland, goods only)."""
        eu = self.env.ref("base.europe", raise_if_not_found=False)
        codes = {"EL" if c == "GR" else c
                 for c in (eu.country_ids.mapped("code") if eu else [])}
        return codes | {"XI"}

    def _cz_sh_country(self, line):
        """k_stat: "Kód státu, který přidělil daňové identifikační číslo
        registrace k DPH pořizovatele" — the VAT number's own prefix (EL for
        Greece, XI for Northern Ireland), not the ISO code of the partner's
        country (GR, GB)."""
        vat = "".join((line.partner_vat or "").split()).upper()
        if len(vat) > 2 and vat[:2].isalpha():
            return vat[:2]
        code = (line.partner_country_code or "").upper()
        return "EL" if code == "GR" else code

    @staticmethod
    def _cz_sh_whole(value):
        """pln_hodnota: "Celková hodnota plnění se zaokrouhlí na celé koruny
        nahoru" (DPHSHV, VetaR). Rounded towards the higher whole crown —
        ``'%.0f'`` rounded half-to-even, so 1 000.40 was filed as 1 000.
        Rounded to cents first so float noise (1 000.0000001) is not a crown.
        """
        return int(math.ceil(round(value or 0.0, 2)))

    def _cssk_ec_is_delta(self):
        # Every later hlášení for a period is "N" (následné); it reports the
        # changes, withdrawing a filed row by a storno row.
        if self.country_id.code == "CZ":
            return self.statement_type_id.fa_xml_value == "N"
        return super()._cssk_ec_is_delta()

    def _cssk_ec_cancels_by_storno(self):
        if self.country_id.code == "CZ":
            return True
        return super()._cssk_ec_cancels_by_storno()

    def _cssk_ec_whole(self, value):
        if self.country_id.code == "CZ":
            return self._cz_sh_whole(value)
        return super()._cssk_ec_whole(value)

    def _check_vies(self):
        """The base gate, with the DPHSHV's own country codes.

        The base accepts a line only when the partner's COUNTRY is in the EU,
        which refuses every Northern Ireland customer (their country is GB)
        although the structure lists XI. XI is accepted for goods only.
        """
        if self.country_id.code != "CZ":
            return super()._check_vies()
        self.ensure_one()
        allowed = self._cz_sh_vies_codes()
        invalid = []
        for line in self.line_ids:
            vat = "".join((line.partner_vat or "").split()).upper()
            code = self._cz_sh_country(line)
            ok = (
                len(vat) >= 3 and vat[:2].isalpha() and code in allowed
                and (code != "XI" or line.transaction_code in CZ_SH_GOODS_CODES)
            )
            if not ok:
                invalid.append("%s / %s / %s" % (
                    line.partner_country_code or "??", vat or "—",
                    line.transaction_code or "—"))
        if invalid:
            raise UserError(_(
                "The souhrnné hlášení cannot be exported — these lines have a "
                "missing or non-EU VAT number, or report a service to a "
                "Northern Ireland (XI) number, which is valid for goods only "
                "(hard block):\n%s") % "\n".join(invalid))
