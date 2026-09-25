# Copyright 2026 Data Dance s.r.o.
# License AGPL-3 — see the LICENSE file.
"""INTRASTAT-CZ — CE adapter on the OCA intrastat_product engine.

Subclasses OCA ``intrastat.product.declaration`` and implements the country file
hook ``_generate_xml`` (the OCA engine's generic "produce the declaration file"
hook) by mapping the engine's computed declaration lines onto the CZ Celní správa
InstatOnline **CSV** renderer in ``l10n_cssk_intrastat_base`` (LGPL). The engine
(gather invoices → computation lines → grouped declaration lines) is all OCA; we
add only the Czech file output. The attachment is written with a ``.csv``
extension (overriding the base's ``.xml``) since CZ files a CSV, not XML.
"""
from odoo import models


class IntrastatProductDeclaration(models.Model):
    _inherit = "intrastat.product.declaration"

    def _generate_xml(self):
        """For CZ companies, return the InstatOnline CSV bytes; otherwise defer
        to the standard (XML) localization hook."""
        self.ensure_one()
        if (self.company_id.country_id.code or "") != "CZ":
            return super()._generate_xml()
        header = {
            "month": self.month,
            "year": self.year,
            "vat": (self.company_id.vat or "").replace(" ", ""),
            # OCA declaration is single-direction: arrivals → A, dispatches → D
            "direction": "A" if self.declaration_type == "arrivals" else "D",
        }
        lines = []
        for dl in self.declaration_line_ids:
            hs = dl.hs_code_id
            lines.append({
                "partner_vat": dl.vat,
                "country_code": dl.src_dest_country_code,
                "origin_country": dl.product_origin_country_code,
                "transaction_code": dl.transaction_code,
                "transport_code": dl.transport_id.code,
                "incoterm_code": dl.incoterm_id.code,
                "cn8": hs.local_code or hs.hs_code or "",
                "weight": dl.weight,
                "supplementary_units": dl.suppl_unit_qty,
                "value": dl.amount_company_currency,
            })
        return self.env["cssk.instat.builder"].build_cz_intrastat_csv(header, lines)

    def _attach_xml_file(self, xml_bytes, declaration_name):
        """CZ files a CSV — give the attachment a ``.csv`` name/extension."""
        self.ensure_one()
        if (self.company_id.country_id.code or "") != "CZ":
            return super()._attach_xml_file(xml_bytes, declaration_name)
        filename = "%s_%s.csv" % (self.year_month, declaration_name)
        attach = self.env["ir.attachment"].create({
            "name": filename,
            "res_id": self.id,
            "res_model": self._name,
            "raw": xml_bytes,
        })
        return attach.id
