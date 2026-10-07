# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Edition-neutral INSTAT (instat62) XML builder + validator for INTRASTAT-SK.

Renders and validates the official Finančná správa INTRASTAT-SK message
(``intrastat.financnasprava.sk``, schema ``instat62.xsd`` vendored in ``data/``)
from a normalized, dependency-free input. Two entry points:

* ``build_instat_xml(header, lines)`` — one declaration (one flow); CE adapter.
* ``build_instat_envelope(env_header, decl_groups)`` — one envelope, several
  declarations (arrivals + dispatches); EE adapter.

Both validate the output against ``instat62.xsd`` (raise on failure).

header keys: envelope_id, dt (datetime), psi_vat, psi_name, psi_street,
  psi_zip, psi_city, psi_phone, psi_email, software, declaration_id,
  reference_period ('YYYY-MM'), function_code (O/N/M/D), declaration_type_code
  ('1' full / '2' simplified), flow_code ('A'/'D'), currency_code ('EUR').
line keys: cn8, su_code, ms_cons_dest, country_of_origin, net_mass,
  quantity_in_su, invoiced_amount, nature_a, nature_b, transport_mode, region,
  delivery_terms, partner_vat.
"""
import os

from lxml import etree

from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_round

_XSD_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "instat62.xsd")
_PSI_FIELDS = ("psi_vat", "psi_name", "psi_street", "psi_zip", "psi_city",
               "psi_phone", "psi_email")


class CSSKInstatBuilder(models.AbstractModel):
    _name = "cssk.instat.builder"
    _description = "INTRASTAT-SK INSTAT (instat62) XML builder"

    @staticmethod
    def _t(parent, tag, value):
        el = etree.SubElement(parent, tag)
        el.text = "" if value is None else str(value)
        return el

    @staticmethod
    def _int(value):
        # netMass / quantityInSU / invoicedAmount are xs:integer in instat62.xsd
        return str(int(round(float(value or 0.0))))

    @staticmethod
    def _split_nature(nature_a, nature_b=None):
        """``("11", None)`` → ``("1", "1")``.

        Both Intrastat engines store the nature of transaction as one 2-digit
        code (OCA ``intrastat.transaction``, EE ``account.intrastat.code``:
        11, 12, 21 …), but INSTAT carries it as two 1-digit codes, column A
        and column B of the table (FS SR: "kód A druhu obchodu", "kód B …
        ak existuje"). Passed whole, "11" landed in the A code — and the
        schema types both as a bare string, so nothing objected."""
        nature_a = str(nature_a or "").strip()
        nature_b = str(nature_b or "").strip()
        if len(nature_a) == 2 and not nature_b:
            nature_a, nature_b = nature_a[0], nature_a[1]
        return nature_a, nature_b

    def _party(self, parent, h, party_role):
        # Party (instat62): partyId, partyName, Address(streetName req'd) — both
        # the Envelope sender and each Declaration's PSI carry one.
        p = etree.SubElement(parent, "Party", partyType="PSI", partyRole=party_role)
        self._t(p, "partyId", h.get("psi_vat"))
        self._t(p, "partyName", h.get("psi_name"))
        addr = etree.SubElement(p, "Address")
        self._t(addr, "streetName", h.get("psi_street") or "")
        if h.get("psi_zip"):
            self._t(addr, "postalCode", h["psi_zip"])
        if h.get("psi_city"):
            self._t(addr, "cityName", h["psi_city"])
        if h.get("psi_phone"):
            self._t(addr, "phoneNumber", h["psi_phone"])
        if h.get("psi_email"):
            self._t(addr, "e-mail", h["psi_email"])
        return p

    def _build_root(self, env_header):
        root = etree.Element("INSTAT")
        env = etree.SubElement(root, "Envelope")
        self._t(env, "envelopeId", env_header.get("envelope_id"))
        dt = env_header.get("dt")
        dte = etree.SubElement(env, "DateTime")
        self._t(dte, "date", dt.strftime("%Y-%m-%d") if dt else "")
        self._t(dte, "time", dt.strftime("%H:%M:%S") if dt else "")
        self._party(env, env_header, "sender")
        self._t(env, "softwareUsed", env_header.get("software") or "Data Dance")
        return root, env

    def _append_declaration(self, env, dh, lines):
        full = (dh.get("declaration_type_code") or "1") == "1"
        dispatch = (dh.get("flow_code") or "").upper() == "D"
        decl = etree.SubElement(env, "Declaration")
        self._t(decl, "declarationId", dh.get("declaration_id"))
        self._t(decl, "referencePeriod", dh.get("reference_period"))
        self._t(decl, "PSIId", dh.get("psi_vat"))
        self._party(decl, dh, "PSI")
        fn = etree.SubElement(decl, "Function")
        self._t(fn, "functionCode", dh.get("function_code") or "O")
        self._t(decl, "declarationTypeCode",
                dh.get("declaration_type_code") or "1")
        self._t(decl, "flowCode", dh.get("flow_code"))
        self._t(decl, "currencyCode", dh.get("currency_code") or "EUR")
        for i, ln in enumerate(lines, start=1):
            item = etree.SubElement(decl, "Item")
            self._t(item, "itemNumber", i)
            cn8 = etree.SubElement(item, "CN8")
            self._t(cn8, "CN8Code", ln.get("cn8"))
            if ln.get("su_code"):
                self._t(cn8, "SUCode", ln["su_code"])
            self._t(item, "MSConsDestCode", ln.get("ms_cons_dest"))
            if full and ln.get("country_of_origin"):
                self._t(item, "countryOfOriginCode", ln["country_of_origin"])
            if full:
                self._t(item, "netMass", self._int(ln.get("net_mass")))
                if ln.get("su_code"):
                    self._t(item, "quantityInSU",
                            self._int(ln.get("quantity_in_su")))
            self._t(item, "invoicedAmount", self._int(ln.get("invoiced_amount")))
            nature_a, nature_b = self._split_nature(
                ln.get("nature_a"), ln.get("nature_b"))
            if nature_a:
                nt = etree.SubElement(item, "NatureOfTransaction")
                self._t(nt, "natureOfTransactionACode", nature_a)
                if nature_b:
                    self._t(nt, "natureOfTransactionBCode", nature_b)
            if ln.get("transport_mode"):
                self._t(item, "modeOfTransportCode", ln["transport_mode"])
            if ln.get("region"):
                self._t(item, "regionCode", ln["region"])
            if ln.get("delivery_terms"):
                dts = etree.SubElement(item, "DeliveryTerms")
                self._t(dts, "TODCode", ln["delivery_terms"])
            if dispatch and ln.get("partner_vat"):
                self._t(item, "partnerId", ln["partner_vat"])
        # totalNumberLines comes AFTER the items (instat62 sequence)
        self._t(decl, "totalNumberLines", len(lines))
        return decl

    def validate_instat_xml(self, xml_bytes):
        """Validate against the official instat62.xsd; raise on failure."""
        schema = etree.XMLSchema(etree.parse(_XSD_PATH))
        try:
            schema.assertValid(etree.fromstring(xml_bytes))
        except etree.DocumentInvalid as exc:
            raise UserError(_(
                "INTRASTAT-SK XML failed instat62.xsd validation:\n%s") % exc)

    def _serialize(self, root, validate=True):
        xml_bytes = etree.tostring(root, xml_declaration=True, encoding="UTF-8",
                                   pretty_print=True)
        if validate:
            self.validate_instat_xml(xml_bytes)
        return xml_bytes

    def build_instat_xml(self, header, lines, validate=True):
        """One declaration (one flow). header carries envelope + decl + PSI keys."""
        root, env = self._build_root(header)
        self._append_declaration(env, header, lines)
        return self._serialize(root, validate)

    def build_instat_envelope(self, env_header, decl_groups, validate=True):
        """One envelope, several declarations: decl_groups = [{header, lines}]."""
        root, env = self._build_root(env_header)
        for grp in decl_groups:
            dh = dict(grp["header"])
            for key in _PSI_FIELDS:
                dh.setdefault(key, env_header.get(key))
            self._append_declaration(env, dh, grp.get("lines") or [])
        return self._serialize(root, validate)

    # ------------------------------------------------------------------
    # CZ INTRASTAT — Celní správa "InstatOnline" CSV (separate national format)
    # ------------------------------------------------------------------
    # Unlike SK (INSTAT XML), the Czech declaration is filed as a semicolon CSV
    # uploaded to the Celní správa InstatOnline portal. Column layout, constant
    # fields ('ST' code of movement, empty region/statistical-sign/description)
    # and the weight/SU number formatting reproduce the official Odoo EE
    # ``l10n_cz_intrastat`` output exactly (validated against its expected file in
    # the tests). No XSD — the portal validates on upload.

    # order of the 16 data columns after the leading month;year
    _CZ_CSV_COLUMNS = (
        "vat", "direction", "partner_vat", "country_code", "region_code",
        "origin_country", "transaction_code", "transport_code", "incoterm_code",
        "code_of_movement", "cn8", "statistical_sign", "description_of_goods",
        "weight", "supplementary_units", "value",
    )

    @staticmethod
    def _cz_format_number(value):
        """Weight / supplementary units: 3 decimals when ≤ 1, else integer
        (matches the official l10n_cz_intrastat ``format_number``)."""
        if value:
            val = float(value)
            if float_compare(val, 1.0, precision_digits=3) <= 0:
                return "%0.3f" % float_round(val, 3)
            return str(int(val))
        return "0"

    def build_cz_intrastat_csv(self, header, lines):
        """Render the CZ Celní správa InstatOnline CSV.

        header keys: month ('MM'), year ('YYYY'), vat, direction ('A'/'D').
        line keys: partner_vat, country_code, origin_country, transaction_code,
          transport_code, incoterm_code, cn8, weight, supplementary_units, value.
        region_code, statistical_sign and description_of_goods are intentionally
        left empty; code_of_movement is the constant 'ST'.
        """
        month = str(header.get("month") or "")
        year = str(header.get("year") or "")
        content = ""
        for ln in lines:
            row = {
                "vat": header.get("vat") or "",
                "direction": header.get("direction") or "",
                "partner_vat": ln.get("partner_vat") or "",
                "country_code": ln.get("country_code") or "",
                "region_code": "",
                "origin_country": ln.get("origin_country") or "",
                "transaction_code": ln.get("transaction_code") or "",
                "transport_code": ln.get("transport_code") or "",
                "incoterm_code": ln.get("incoterm_code") or "",
                "code_of_movement": "ST",
                "cn8": (ln.get("cn8") or "").replace(" ", ""),
                "statistical_sign": "",
                "description_of_goods": "",
                "weight": self._cz_format_number(ln.get("weight")),
                "supplementary_units": self._cz_format_number(
                    ln.get("supplementary_units")),
                "value": str(int(ln.get("value") or 0)),
            }
            content += ";".join(
                [month, year] + [str(row[c]) for c in self._CZ_CSV_COLUMNS]
            ) + ";;\n"
        return content.encode("utf-8")
