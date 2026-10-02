# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import re

from odoo import _, models
from odoo.exceptions import UserError


def split_vat(vat):
    """``(country prefix, rest)`` of a VAT number; prefix '' when absent."""
    vat = re.sub(r"\s", "", vat or "").upper()
    if re.match(r"^[A-Z]{2}", vat):
        return vat[:2], vat[2:]
    return "", vat


class CsskOssReturn(models.Model):
    _inherit = "cssk.oss.return"

    def _l10n_sk_oss_applies(self):
        return self.version_id.country_id.code == "SK"

    def _l10n_sk_oss_vat(self):
        """IČ DPH as the eForm writes it into ``TraderID/VATNumber``.

        WITH the SK prefix: the eForm's own field validation is "Musí
        obsahovať SK a 10 numerických znakov" and its serializer copies the
        field verbatim, so a bare number would be a document the portal's own
        form could never have produced.
        """
        prefix, rest = split_vat(self.company_id.vat)
        return "SK" + rest if prefix in ("", "SK") else prefix + rest

    def _cssk_preflight_export(self):
        res = super()._cssk_preflight_export()
        for ret in self.filtered(lambda r: r._l10n_sk_oss_applies()):
            vat = ret._l10n_sk_oss_vat()
            if not re.fullmatch(r"SK\d{10}", vat):
                raise UserError(_(
                    "The OSS return (DPOSS_EU) identifies the filer by its "
                    "IČ DPH (SK followed by 10 digits); company %(company)s "
                    "has '%(vat)s'.",
                    company=ret.company_id.display_name, vat=vat or "—"))
        return res

    def _cssk_render_context(self):
        ctx = super()._cssk_render_context()
        if self._l10n_sk_oss_applies():
            rows = ctx["rows"]

            def vat_sum(recs, supply):
                return sum(recs.filtered(
                    lambda ln: ln.supply_type == supply).mapped("vat_amount"))

            ctx.update({
                "sk_vat": self._l10n_sk_oss_vat(),
                "split_vat": split_vat,
                "sk_rate_type": {"standard": "STANDARD", "reduced": "REDUCED"},
                "sk_supply_type": {"goods": "GOODS", "services": "SERVICES"},
                "iso_date": lambda d: d.strftime("%Y-%m-%d") if d else None,
                "grand_msid_services": vat_sum(ctx["msid_rows"], "services"),
                "grand_msid_goods": vat_sum(ctx["msid_rows"], "goods"),
                "grand_mest_services": vat_sum(ctx["mest_rows"], "services"),
                "grand_mest_goods": vat_sum(ctx["mest_rows"], "goods"),
                "grand_total": sum(rows.mapped("vat_amount")),
            })
        return ctx
