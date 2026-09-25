# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import datetime

from lxml import etree

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestInstatBuilder(TransactionCase):
    def _hdr(self, **kw):
        h = {
            "envelope_id": "DD00001", "dt": datetime(2026, 4, 15, 10, 30, 0),
            "psi_vat": "SK2121576435", "psi_name": "Data Dance s.r.o.",
            "declaration_id": 1, "reference_period": "2026-03",
            "function_code": "O", "declaration_type_code": "1",
            "flow_code": "D", "currency_code": "EUR"}
        h.update(kw)
        return h

    LINE = {
        "cn8": "84713000", "su_code": "p/st", "ms_cons_dest": "CZ",
        "country_of_origin": "CN", "net_mass": 13.0, "quantity_in_su": 3,
        "invoiced_amount": 4380.0, "nature_a": "11", "region": "SK010",
        "partner_vat": "CZ12345678"}

    def _xml(self, header, lines):
        return etree.fromstring(
            self.env["cssk.instat.builder"].build_instat_xml(header, lines))

    def test_full_dispatch(self):
        root = self._xml(self._hdr(flow_code="D"), [self.LINE])
        self.assertEqual(root.tag, "INSTAT")
        self.assertEqual(root.findtext(".//Party/partyId"), "SK2121576435")
        self.assertEqual(root.findtext(".//Declaration/referencePeriod"), "2026-03")
        self.assertEqual(root.findtext(".//Function/functionCode"), "O")
        self.assertEqual(root.findtext(".//Declaration/flowCode"), "D")
        self.assertEqual(root.findtext(".//totalNumberLines"), "1")
        item = root.find(".//Item")
        self.assertEqual(item.findtext("CN8/CN8Code"), "84713000")
        self.assertEqual(item.findtext("CN8/SUCode"), "p/st")
        self.assertEqual(item.findtext("MSConsDestCode"), "CZ")
        self.assertEqual(item.findtext("countryOfOriginCode"), "CN")
        self.assertEqual(item.findtext("netMass"), "13")     # xs:integer
        self.assertEqual(item.findtext("invoicedAmount"), "4380")
        self.assertEqual(
            item.findtext("NatureOfTransaction/natureOfTransactionACode"), "11")
        self.assertEqual(item.findtext("regionCode"), "SK010")
        self.assertEqual(item.findtext("partnerId"), "CZ12345678")  # dispatch only

    def test_validates_against_instat62_xsd(self):
        b = self.env["cssk.instat.builder"]
        # build_* validate on output, so a returned doc is XSD-valid; re-assert it
        b.validate_instat_xml(b.build_instat_xml(self._hdr(), [dict(self.LINE)]))
        # a malformed document is rejected with a clear error
        with self.assertRaises(UserError):
            b.validate_instat_xml(b"<INSTAT><Envelope/></INSTAT>")

    def test_arrival_has_no_partner_id(self):
        root = self._xml(self._hdr(flow_code="A"), [self.LINE])
        self.assertEqual(root.findtext(".//Declaration/flowCode"), "A")
        self.assertIsNone(root.find(".//Item/partnerId"))

    def test_envelope_multi_declaration(self):
        """build_instat_envelope: one envelope, a Declaration per flow."""
        env_header = {
            "envelope_id": "DD00002", "dt": datetime(2026, 4, 15, 9, 0, 0),
            "psi_vat": "SK2121576435", "psi_name": "Data Dance s.r.o."}
        groups = [
            {"header": {"declaration_id": 1, "reference_period": "2026-03",
                        "flow_code": "A"}, "lines": [dict(self.LINE)]},
            {"header": {"declaration_id": 2, "reference_period": "2026-03",
                        "flow_code": "D"}, "lines": [dict(self.LINE), dict(self.LINE)]},
        ]
        root = etree.fromstring(
            self.env["cssk.instat.builder"].build_instat_envelope(env_header, groups))
        decls = root.findall(".//Declaration")
        self.assertEqual(len(decls), 2)
        self.assertEqual(decls[0].findtext("flowCode"), "A")
        self.assertEqual(decls[1].findtext("flowCode"), "D")
        self.assertEqual(decls[1].findtext("totalNumberLines"), "2")
        # PSIId propagated from the envelope to each declaration
        self.assertEqual(decls[0].findtext("PSIId"), "SK2121576435")
        # arrival has no partnerId, dispatch does
        self.assertIsNone(decls[0].find("Item/partnerId"))
        self.assertEqual(decls[1].find("Item/partnerId").text, "CZ12345678")

    def test_simplified_omits_mass_and_origin(self):
        root = self._xml(self._hdr(declaration_type_code="2"), [self.LINE])
        self.assertIsNone(root.find(".//Item/netMass"))
        self.assertIsNone(root.find(".//Item/countryOfOriginCode"))
        self.assertIsNone(root.find(".//Item/quantityInSU"))
        # core fields still present
        self.assertEqual(root.find(".//Item").findtext("CN8/CN8Code"), "84713000")

    # ------------------------------------------------------------------
    # CZ Celní správa InstatOnline CSV
    # ------------------------------------------------------------------
    def test_cz_intrastat_csv_matches_official_format(self):
        """Byte-for-byte match with the official InstatOnline CSV format.

        Header, field order, separator and decimal convention are all fixed by
        Celní správa; this pins the exact bytes so a refactor cannot quietly
        reshape a filing."""
        b = self.env["cssk.instat.builder"]
        dispatch = b.build_cz_intrastat_csv(
            {"month": "07", "year": "2025", "vat": "CZ12345679", "direction": "D"},
            [{"partner_vat": "BE0897223670", "country_code": "BE",
              "origin_country": "ES", "transaction_code": "11",
              "transport_code": "2", "incoterm_code": "", "cn8": "88023000",
              "weight": 0.2, "supplementary_units": 8, "value": 800}])
        arrival = b.build_cz_intrastat_csv(
            {"month": "07", "year": "2025", "vat": "CZ12345679", "direction": "A"},
            [{"partner_vat": "BE0897223670", "country_code": "BE",
              "origin_country": "ES", "transaction_code": "11",
              "transport_code": "1", "incoterm_code": "", "cn8": "88023000",
              "weight": 50000, "supplementary_units": 10, "value": 300000}])
        self.assertEqual(
            dispatch.decode("utf-8"),
            "07;2025;CZ12345679;D;BE0897223670;BE;;ES;11;2;;ST;88023000;;;0.200;8;800;;\n")
        self.assertEqual(
            arrival.decode("utf-8"),
            "07;2025;CZ12345679;A;BE0897223670;BE;;ES;11;1;;ST;88023000;;;50000;10;300000;;\n")

    def test_cz_intrastat_csv_strips_cn8_spaces(self):
        b = self.env["cssk.instat.builder"]
        out = b.build_cz_intrastat_csv(
            {"month": "03", "year": "2026", "vat": "CZ25663585", "direction": "A"},
            [{"country_code": "DE", "transaction_code": "11", "cn8": "8471 3000",
              "weight": 13, "supplementary_units": 3, "value": 4380}]).decode()
        # CN8 spaces removed; empty optional fields render blank
        self.assertIn(";84713000;", out)
        self.assertTrue(out.endswith(";;\n"))
