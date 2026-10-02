# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import re

from odoo import _, models
from odoo.exceptions import UserError


def vat_root(vat):
    """The numeric part of a VAT number, as EPO wants it ("kmenová část").

    EPO identifies the filer by the DIČ WITHOUT the "CZ" prefix (``VetaP/@dic``
    is at most 10 characters), and OSSEI1 asks for the root of a foreign VAT
    number the same way. A leading two-letter country code is dropped;
    anything else is left for the schema to judge.
    """
    vat = re.sub(r"\s", "", vat or "")
    return vat[2:] if re.match(r"^[A-Za-z]{2}", vat) else vat


class CsskOssReturn(models.Model):
    _inherit = "cssk.oss.return"

    def _cz_requires_tax_authority(self):
        # OSSEI1 carries no c_ufo: the special schemes are administered by
        # one office for everyone, not the company's own finanční úřad.
        # (Consulted by l10n_cz_statutory's preflight where it is installed.)
        return False

    def _l10n_cz_oss_applies(self):
        return self.version_id.country_id.code == "CZ"

    def _cssk_preflight_export(self):
        """A Czech OSS filer is identified by its DIČ; check it before EPO does.

        The schema only bounds the length, so a DIČ with a typo or a foreign
        prefix would validate and be rejected by the portal instead.
        """
        res = super()._cssk_preflight_export()
        for ret in self.filtered(lambda r: r._l10n_cz_oss_applies()):
            vat = re.sub(r"\s", "", ret.company_id.vat or "").upper()
            if not re.fullmatch(r"CZ\d{8,10}", vat):
                raise UserError(_(
                    "The OSS return (OSSEI1) identifies the filer by its Czech "
                    "DIČ (CZ followed by 8 to 10 digits); company %(company)s "
                    "has '%(vat)s'.",
                    company=ret.company_id.display_name, vat=vat or "—"))
        return res

    def _cssk_render_context(self):
        ctx = super()._cssk_render_context()
        if self._l10n_cz_oss_applies():
            ctx.update({
                "dic": vat_root(self.company_id.vat),
                "vat_root": vat_root,
                "cz_date": lambda d: d.strftime("%d.%m.%Y") if d else None,
                # Z = základní (standard), S = snížená (reduced)
                "cz_rate_type": {"standard": "Z", "reduced": "S"},
                # G = zboží (goods), S = služby (services)
                "cz_supply_type": {"goods": "G", "services": "S"},
            })
        return ctx
