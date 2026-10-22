# Copyright 2026 Data Dance s.r.o.
# License AGPL-3 — see the LICENSE file.
"""SK INTRASTAT — CE adapter on the OCA intrastat_product engine.

Subclasses OCA ``intrastat.product.declaration`` and implements the country XML
hook ``_generate_xml`` by mapping the engine's computed declaration lines onto
the edition-neutral INSTAT builder in ``l10n_cssk_intrastat_base`` (LGPL). The
engine (gather invoices → computation lines → grouped declaration lines) is all
OCA; we add only the SK Štatistický úrad / Finančná správa INSTAT output.
"""
from odoo import fields, models


class IntrastatProductDeclaration(models.Model):
    _inherit = "intrastat.product.declaration"

    def _generate_xml(self):
        self.ensure_one()
        if (self.company_id.country_id.code or "") != "SK":
            return super()._generate_xml()
        builder = self.env["cssk.instat.builder"]
        cp = self.company_id.partner_id
        header = {
            "envelope_id": "DD%05d" % self.id,
            "dt": fields.Datetime.now(),
            "psi_vat": (self.company_id.vat or "").replace(" ", ""),
            "psi_name": self.company_id.name,
            "psi_street": cp.street or "",
            "psi_zip": cp.zip or "",
            "psi_city": cp.city or "",
            "software": "Data Dance",
            "declaration_id": self.revision or 1,
            "reference_period": self.year_month,
            "function_code": "O",
            "declaration_type_code": "1",   # plné hlásenie (simplified=2 TODO)
            "flow_code": "A" if self.declaration_type == "arrivals" else "D",
            "currency_code": self.currency_id.name or "EUR",
        }
        lines = []
        for dl in self.declaration_line_ids:
            hs = dl.hs_code_id
            lines.append({
                "cn8": (hs.local_code or hs.hs_code or "").replace(" ", ""),
                "su_code": dl.intrastat_unit_id.name or "",
                "ms_cons_dest": dl.src_dest_country_code,
                "country_of_origin": dl.product_origin_country_code,
                "net_mass": dl.weight,
                "quantity_in_su": dl.suppl_unit_qty,
                "invoiced_amount": dl.amount_company_currency,
                "nature_a": dl.transaction_code,
                "region": dl.region_code,
                "partner_vat": dl.vat,
            })
        return builder.build_instat_xml(header, lines)
