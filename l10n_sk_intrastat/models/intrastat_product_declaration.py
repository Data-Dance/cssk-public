# Copyright 2026 Data Dance s.r.o.
# License AGPL-3 — see the LICENSE file.
"""SK INTRASTAT — CE adapter on the OCA intrastat_product engine.

Subclasses OCA ``intrastat.product.declaration`` and implements the country XML
hook ``_generate_xml`` by mapping the engine's computed declaration lines onto
the edition-neutral INSTAT builder in ``l10n_cssk_intrastat_base``. The
engine (gather invoices → computation lines → grouped declaration lines) is all
OCA; we add only the SK Štatistický úrad / Finančná správa INSTAT output.
"""
from lxml import etree

from odoo import fields, models

#: OCA names eight units differently from the Eurostat supplementary-unit
#: codes ("items" for p/st, "1000 kWh" for 1 000 kWh, …), and INSTAT wants the
#: code. The spellings are Odoo Enterprise's ``account_intrastat`` list, so
#: both adapters file the same SUCode; every other OCA unit is already named
#: by its code. Keyed by xmlid, not name: names are editable.
_SU_CODE_BY_XMLID = {
    "intrastat_product.intrastat_unit_pce": "p/st",
    "intrastat_product.intrastat_unit_100pce": "100 p/st",
    "intrastat_product.intrastat_unit_1000pce": "1 000 p/st",
    "intrastat_product.intrastat_unit_l_alc_100_pct": "l alc. 100 %",
    "intrastat_product.intrastat_unit_kg_90_pct_sdt": "kg 90 % sdt",
    "intrastat_product.intrastat_unit_1000_kWh": "1 000 kWh",
    "intrastat_product.intrastat_unit_1000m3": "1 000 m3",
    "intrastat_product.intrastat_unit_gi_FS": "gi F / S",
}


def sk_instat_finish_functions(builder, xml_bytes):
    """Complete the Function block the shared builder leaves bare, then validate.

    FS SR's INSTAT description: ``functionCode`` is O (štandardné), N (nulové),
    M (opravné) or D (zrušené hlásenie); ``previousDeclarationId`` is "poradové
    číslo opravného hlásenia (vypĺňa sa len pre functionCode = M alebo D)";
    ``Item`` and ``totalNumberLines`` are filled "len pre functionCode = M
    alebo O". The builder writes the function code it is given and always a
    ``totalNumberLines``, so a D or N declaration is finished here.

    A D carries the sequence number of the correction, which runs per
    corrected declaration from 1 (Príručka 2026, ods. 127). Only a whole
    declaration is ever cancelled here, and each at most once, so it is 1.
    """
    root = etree.fromstring(xml_bytes)
    for decl in root.iter("Declaration"):
        fn = decl.find("Function")
        code = fn.findtext("functionCode")
        if code == "D" and fn.find("previousDeclarationId") is None:
            etree.SubElement(fn, "previousDeclarationId").text = "1"
        if code in ("N", "D"):
            for el in decl.findall("totalNumberLines"):
                decl.remove(el)
    xml_bytes = etree.tostring(root, xml_declaration=True, encoding="UTF-8",
                               pretty_print=True)
    builder.validate_instat_xml(xml_bytes)
    return xml_bytes


class IntrastatProductDeclaration(models.Model):
    _inherit = "intrastat.product.declaration"

    def _sk_cancelled_revisions(self):
        """Revision numbers this declaration's file must cancel first.

        An OCA revision is a copy of the declaration with the next number.
        INTRASTAT-SK numbers a month's declarations 1, 2, 3 … per flow, and a
        further file under the next number is a further *partial* declaration
        that ADDS to the earlier ones (Príručka pre spravodajské jednotky 2026,
        ods. 221–222). Filed that way, a revision with the action *Replace*
        doubled the month. The Statistical Office's own way to replace a
        declaration is to cancel it (opravné hlásenie with function D, ods.
        229–230) and file the correct items under the next number (Príklad
        19 b). So a *Replace* or *Nil* revision cancels every declaration
        still standing for the month and flow: those filed since the last
        earlier *Replace* / *Nil* revision, which cancelled what came before
        it. An *Append* revision cancels nothing — it is the further partial
        declaration the handbook describes, and must hold only the added
        transactions.
        """
        self.ensure_one()
        revision = self.revision or 1
        if revision <= 1 or self.action not in ("replace", "nihil"):
            return []
        earlier = self.search([
            ("company_id", "=", self.company_id.id),
            ("year_month", "=", self.year_month),
            ("declaration_type", "=", self.declaration_type),
            ("revision", "<", revision),
            ("action", "in", ("replace", "nihil")),
        ], order="revision desc", limit=1)
        first_standing = earlier.revision if earlier and earlier.revision > 1 else 1
        return list(range(first_standing, revision))

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
            # N: nulové hlásenie — the engine sets Nil when the month is empty
            "function_code": "N" if self.action == "nihil" else "O",
            "declaration_type_code": "1",   # plné hlásenie (simplified=2 TODO)
            "flow_code": "A" if self.declaration_type == "arrivals" else "D",
            "currency_code": self.currency_id.name or "EUR",
        }
        lines = []
        for dl in self.declaration_line_ids:
            hs = dl.hs_code_id
            lines.append({
                "cn8": (hs.local_code or hs.hs_code or "").replace(" ", ""),
                "su_code": self._sk_su_code(dl.intrastat_unit_id),
                "ms_cons_dest": dl.src_dest_country_code,
                "country_of_origin": dl.product_origin_country_code,
                "net_mass": dl.weight,
                "quantity_in_su": dl.suppl_unit_qty,
                "invoiced_amount": dl.amount_company_currency,
                "nature_a": dl.transaction_code,
                # modeOfTransportCode and TODCode belong on every item of a full
                # declaration (FS SR: "len pre declarationTypeCode = 1"); the
                # engine has both and this used to file neither.
                "transport_mode": dl.transport_id.code or "",
                "delivery_terms": dl.incoterm_id.code or "",
                "region": dl.region_code,
                "partner_vat": dl.vat,
            })
        if header["function_code"] == "N":
            lines = []
        decl_keys = ("reference_period", "declaration_type_code", "flow_code",
                     "currency_code")
        groups = [{
            # zrušenie celého hlásenia (ods. 230): the number of the
            # declaration cancelled, function D, no items
            "header": dict({k: header[k] for k in decl_keys},
                           declaration_id=cancelled, function_code="D"),
            "lines": [],
        } for cancelled in self._sk_cancelled_revisions()]
        groups.append({"header": dict(header), "lines": lines})
        return sk_instat_finish_functions(
            builder, builder.build_instat_envelope(header, groups, validate=False))

    def _sk_su_code(self, unit):
        """The official supplementary-unit code INSTAT carries, not OCA's name."""
        if not unit:
            return ""
        xmlid = unit.get_external_id().get(unit.id, "")
        return _SU_CODE_BY_XMLID.get(xmlid) or unit.name
