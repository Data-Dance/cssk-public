# Copyright 2026 Data Dance s.r.o.
# License AGPL-3 — see the LICENSE file.
from odoo.tests import TransactionCase, tagged

from odoo.addons.l10n_sk_intrastat.models.intrastat_product_declaration import (
    _SU_CODE_BY_XMLID,
)


@tagged("post_install", "-at_install")
class TestSkIntrastat(TransactionCase):

    def test_supplementary_units_file_the_eurostat_code(self):
        """OCA's unit NAME is not always the code: "items" is p/st."""
        decl = self.env["intrastat.product.declaration"]
        for xmlid, code in _SU_CODE_BY_XMLID.items():
            self.assertEqual(decl._sk_su_code(self.env.ref(xmlid)), code, xmlid)
        # the rest are named by their code already
        self.assertEqual(
            decl._sk_su_code(self.env.ref("intrastat_product.intrastat_unit_m2")), "m2")
        self.assertEqual(decl._sk_su_code(self.env["intrastat.unit"]), "")

    def test_every_mapped_unit_exists(self):
        """A renamed or dropped OCA xmlid would silently fall back to the name."""
        for xmlid in _SU_CODE_BY_XMLID:
            self.assertTrue(self.env.ref(xmlid, raise_if_not_found=False), xmlid)


@tagged("post_install", "-at_install")
class TestSkIntrastatRevisions(TransactionCase):
    """A revision is filed as the Statistical Office's correction, not as a
    further partial declaration that would add to the month."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create({
            "name": "SK Intrastat s.r.o.",
            "country_id": cls.env.ref("base.sk").id,
            "vat": "SK2020000004",
            "street": "Hlavná 1", "zip": "81101", "city": "Bratislava",
        })
        cls.hs = cls.env["hs.code"].create({
            "local_code": "88023000", "description": "Satellites"})

    def _declaration(self, **vals):
        decl = self.env["intrastat.product.declaration"].create(dict({
            "company_id": self.company.id, "year": "2026", "month": "05",
            "declaration_type": "arrivals",
        }, **vals))
        return decl

    def _with_line(self, decl):
        self.env["intrastat.product.declaration.line"].create({
            "parent_id": decl.id, "hs_code_id": self.hs.id,
            "src_dest_country_code": "BE", "product_origin_country_code": "ES",
            "weight": 50, "amount_company_currency": 1000,
        })
        return decl

    def _declarations(self, decl):
        from lxml import etree
        root = etree.fromstring(decl._generate_xml())  # already XSD-validated
        return [(d.findtext("declarationId"),
                 d.findtext("Function/functionCode"),
                 d.findtext("Function/previousDeclarationId"),
                 len(d.findall("Item")),
                 d.find("totalNumberLines") is not None)
                for d in root.iter("Declaration")]

    def test_the_first_declaration_is_an_original(self):
        decl = self._with_line(self._declaration())
        self.assertEqual(self._declarations(decl), [("1", "O", None, 1, True)])

    def test_a_replacing_revision_cancels_the_declaration_it_replaces(self):
        first = self._with_line(self._declaration())
        second = self._with_line(first.copy())
        self.assertEqual(second.revision, 2)
        self.assertEqual(self._declarations(second), [
            # zrušenie celého hlásenia č. 1: first correction of it, no items,
            # no line count (filled only for O and M)
            ("1", "D", "1", 0, False),
            # the correct items, under the month's next number
            ("2", "O", None, 1, True),
        ])

    def test_an_appending_revision_is_a_further_partial_declaration(self):
        first = self._with_line(self._declaration())
        appended = self._with_line(first.copy({"action": "append"}))
        self.assertEqual(self._declarations(appended), [("2", "O", None, 1, True)])

    def test_a_later_replacement_cancels_only_what_still_stands(self):
        first = self._with_line(self._declaration())
        second = self._with_line(first.copy())                      # cancels 1
        third = self._with_line(second.copy({"action": "append"}))  # adds 3
        fourth = self._with_line(third.copy({"action": "replace"}))
        self.assertEqual(fourth.revision, 4)
        self.assertEqual([d[:2] for d in self._declarations(fourth)],
                         [("2", "D"), ("3", "D"), ("4", "O")])

    def test_a_nil_declaration_is_filed_as_nil(self):
        decl = self._declaration(action="nihil")
        self.assertEqual(self._declarations(decl), [("1", "N", None, 0, False)])
        # a nil revision withdraws what was filed before it
        replaced = self._with_line(self._declaration(year="2026", month="06"))
        nil = replaced.copy({"action": "nihil"})
        self.assertEqual(self._declarations(nil),
                         [("1", "D", "1", 0, False), ("2", "N", None, 0, False)])
