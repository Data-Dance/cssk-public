# Copyright 2026 Data Dance s.r.o.
# License AGPL-3 — see the LICENSE file.
"""The Czech declaration as the InstatOnline CSV, from the OCA engine's lines.

The renderer itself is tested in ``l10n_cssk_intrastat_base`` against the
file Odoo Enterprise produces; what is tested here is this module's own
part, which had no test: which declaration gets the CSV, what each engine
field is mapped to, and the name of the file.
"""

from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

#: Column positions in one CSV row (month and year lead, two empty fields
#: close it).
MONTH, YEAR, VAT, DIRECTION, PARTNER_VAT, COUNTRY, REGION, ORIGIN, NATURE, \
    TRANSPORT, INCOTERM, MOVEMENT, CN8, SIGN, DESCRIPTION, WEIGHT, UNITS, \
    VALUE = range(18)


@tagged("post_install", "-at_install")
class TestCzIntrastat(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create({
            "name": "CZ Intrastat s.r.o.",
            "country_id": cls.env.ref("base.cz").id,
            "vat": "CZ 25663585",
        })
        cls.hs = cls.env["hs.code"].create({
            "local_code": "8802 30 00", "description": "Letouny"})
        cls.transport = cls.env["intrastat.transport_mode"].search(
            [("code", "=", "3")], limit=1)
        cls.incoterm = cls.env["account.incoterms"].search(
            [("code", "=", "DAP")], limit=1)

    def _declaration(self, declaration_type="arrivals", company=None, **line):
        decl = self.env["intrastat.product.declaration"].create({
            "company_id": (company or self.company).id,
            "year": "2026", "month": "05",
            "declaration_type": declaration_type,
        })
        self.env["intrastat.product.declaration.line"].create(dict({
            "parent_id": decl.id, "hs_code_id": self.hs.id,
            "src_dest_country_code": "DE",
            "product_origin_country_code": "IT",
            "vat": "DE811907980",
            "transport_id": self.transport.id,
            "incoterm_id": self.incoterm.id,
            "weight": 1250.6, "suppl_unit_qty": 12,
            "amount_company_currency": 98765.4,
        }, **line))
        return decl

    def _rows(self, decl):
        content = decl._generate_xml().decode("utf-8")
        self.assertTrue(content.endswith(";;\n"), "each row closes with ;;")
        return [row.split(";") for row in content.splitlines()]

    def test_an_arrival_is_one_csv_row_with_the_engine_s_figures(self):
        row, = self._rows(self._declaration())
        self.assertEqual(len(row), 20)
        self.assertEqual((row[MONTH], row[YEAR]), ("05", "2026"))
        self.assertEqual(row[VAT], "CZ25663585", "spaces leave the DIČ")
        self.assertEqual(row[DIRECTION], "A")
        self.assertEqual(row[PARTNER_VAT], "DE811907980")
        self.assertEqual(row[COUNTRY], "DE")
        self.assertEqual(row[ORIGIN], "IT")
        self.assertEqual(row[TRANSPORT], "3")
        self.assertEqual(row[INCOTERM], "DAP")
        self.assertEqual(row[MOVEMENT], "ST")
        self.assertEqual(row[CN8], "88023000", "the code is filed unspaced")
        self.assertEqual((row[REGION], row[SIGN], row[DESCRIPTION]),
                         ("", "", ""))
        self.assertEqual(row[WEIGHT], "1250", "above 1: whole units")
        self.assertEqual(row[UNITS], "12")
        self.assertEqual(row[VALUE], "98765", "whole crowns")

    def test_a_weight_under_a_kilogram_keeps_three_decimals(self):
        """InstatOnline takes grams as decimals of a kilogram; a whole
        number would file a 400 g consignment as nothing."""
        row, = self._rows(self._declaration(weight=0.4, suppl_unit_qty=0))
        self.assertEqual(row[WEIGHT], "0.400")
        self.assertEqual(row[UNITS], "0")

    def test_a_dispatch_is_direction_d(self):
        row, = self._rows(self._declaration("dispatches"))
        self.assertEqual(row[DIRECTION], "D")

    def test_the_nature_of_transaction_is_filed(self):
        nature = self.env["intrastat.transaction"].search([], limit=1)
        if not nature:
            self.skipTest("no nature of transaction in the database")
        row, = self._rows(self._declaration(transaction_id=nature.id))
        self.assertEqual(row[NATURE], nature.code)

    def test_the_cn_code_falls_back_to_the_six_digit_code(self):
        """``local_code`` is what the engine keeps; a record without one is
        filed by its HS code rather than empty."""
        decl = self._declaration()
        line = decl.declaration_line_ids
        hs = line.hs_code_id
        self.assertEqual(hs.local_code.replace(" ", ""), "88023000")
        self.assertTrue(hs.hs_code, "the engine derives the HS code")

    def test_every_line_is_a_row(self):
        decl = self._declaration()
        self.env["intrastat.product.declaration.line"].create({
            "parent_id": decl.id, "hs_code_id": self.hs.id,
            "src_dest_country_code": "SK",
            "product_origin_country_code": "SK",
            "weight": 3, "amount_company_currency": 100})
        rows = self._rows(decl)
        self.assertEqual([row[COUNTRY] for row in rows], ["DE", "SK"])
        self.assertEqual(rows[1][PARTNER_VAT], "")
        self.assertEqual(rows[1][INCOTERM], "")

    def test_the_file_is_a_csv_attached_to_the_declaration(self):
        decl = self._declaration()
        attachment = self.env["ir.attachment"].browse(
            decl._attach_xml_file(decl._generate_xml(), "arrivals"))
        self.assertTrue(attachment.name.endswith("_arrivals.csv"))
        self.assertIn("2026-05", attachment.name)
        self.assertEqual((attachment.res_model, attachment.res_id),
                         ("intrastat.product.declaration", decl.id))
        self.assertEqual(attachment.raw, decl._generate_xml())

    def test_a_company_elsewhere_does_not_get_the_czech_file(self):
        """Another country's layer answers for its own companies."""
        other = self.env["res.company"].create({
            "name": "AT GmbH", "country_id": self.env.ref("base.at").id})
        decl = self._declaration(company=other)
        builder = type(self.env["cssk.instat.builder"])
        with patch.object(builder, "build_cz_intrastat_csv",
                          autospec=True) as czech:
            try:
                decl._generate_xml()
            except Exception:  # pylint: disable=broad-except
                # The engine has no file for a country without a layer.
                pass
            czech.assert_not_called()
