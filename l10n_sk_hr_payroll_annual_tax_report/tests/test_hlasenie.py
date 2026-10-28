# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Runtime test — proves annual Hlásenie generation + strict XSD validation on
BOTH payroll engines. Detects whichever SK payroll engine is installed (the ``payroll`` engine
``l10n_sk_hr_payroll_oca`` or the ``l10n_sk_hr_payroll`` EE engine), drives it
to a full year of monthly payslips for two employees, generates the annual
Hlásenie and validates the produced XML against the shipped ``rh2023.xsd`` —
asserting the aggregate totals and a per-employee annex (Časť V) row match the
summed payslips."""
import base64
import unittest
from datetime import date

from lxml import etree

from odoo.exceptions import UserError
from odoo.addons.l10n_cssk_payroll_declaration_base.tests.common import (
    confirm_payslips,
)
from odoo.tests import TransactionCase, tagged
from odoo.tools import file_path

YEAR = 2025


@tagged("post_install", "-at_install")
class TestHlasenie(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.engine = cls._detect_engine()
        if not cls.engine:
            raise unittest.SkipTest(
                "no SK payroll engine installed "
                "(l10n_sk_hr_payroll_oca or l10n_sk_hr_payroll)")
        cls.company = cls.env["res.company"].create({
            "name": "SK Hlasenie Co s.r.o.",
            "country_id": cls.env.ref("base.sk").id,
            "company_registry": "12345679",
            "l10n_sk_dic": "1234567890",
            "street": "Hlavna 1",
            # A second address line, never the house number.
            "street2": "Budova B",
            "city": "Bratislava",
            "zip": "81101",
        })
        cls.env.user.company_ids |= cls.company
        cls.env = cls.env(context=dict(
            cls.env.context, allowed_company_ids=cls.company.ids))
        if cls.engine == "oca":
            cls.env.user.group_ids |= cls.env.ref(
                "payroll.group_payroll_manager")
            cls.structure = cls.env.ref(
                "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_employee_salary")
        else:
            cls.env.user.group_ids |= cls.env.ref(
                "hr_payroll.group_hr_payroll_manager")
            cls.structure = cls.env.ref(
                "l10n_sk_hr_payroll.hr_payroll_structure_sk_employee_salary")
        cls.calendar = cls.env["resource.calendar"].create(
            {"name": "SK 40h", "company_id": cls.company.id})

    @classmethod
    def _detect_engine(cls):
        """Which SK payroll engine is installed, or None for neither.

        This used to test for the OCA engine and ASSUME the Enterprise one
        otherwise, then go on to ``env.ref`` an ``hr_payroll`` group. On a
        database with neither engine that raised in ``setUpClass``, so the whole
        suite errored instead of skipping -- and since a Community database
        without the OCA payroll engine is the common case, it had not run at
        all. That is how a fixture using a non-checksum-valid IČO survived
        unnoticed until 04da4a3.

        A missing engine is a skip, not a failure: there is no payslip to build
        a declaration from, and nothing in this module is under test without
        one.
        """
        if cls.env.ref(
                "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_employee_salary",
                raise_if_not_found=False):
            return "oca"
        if cls.env.ref(
                "l10n_sk_hr_payroll.hr_payroll_structure_sk_employee_salary",
                raise_if_not_found=False):
            return "ee"
        return None

    def _create_employee(self, name, rc, wage):
        emp_vals = {
            "name": name,
            "company_id": self.company.id,
            "resource_calendar_id": self.calendar.id,
            "identification_id": rc,
            "date_version": date(YEAR, 1, 1),
            "contract_date_start": date(YEAR, 1, 1),
            "wage": wage,
        }
        if self.engine == "oca":
            emp_vals["struct_id"] = self.structure.id
        else:
            emp_vals["structure_type_id"] = self.structure.type_id.id
        return self.env["hr.employee"].with_company(self.company).create(
            emp_vals)

    def _year_of_payslips(self, employee):
        """Compute one payslip per month of YEAR; return summed rule totals."""
        totals = {}
        for month in range(1, 13):
            last = 28 if month == 2 else (
                30 if month in (4, 6, 9, 11) else 31)
            slip = self.env["hr.payslip"].with_company(self.company).create({
                "name": "Payslip %02d/%d" % (month, YEAR),
                "employee_id": employee.id,
                "struct_id": self.structure.id,
                "company_id": self.company.id,
                "date_from": date(YEAR, month, 1),
                "date_to": date(YEAR, month, last),
            })
            if self.engine == "ee":
                slip = slip.with_context(salary_simulation=True)
            slip.compute_sheet()
            confirm_payslips(slip)
            for line in slip.line_ids:
                totals[line.code] = totals.get(line.code, 0.0) + line.total
        return totals

    @staticmethod
    def _advance(totals):
        split = abs(round(
            totals.get("INCOMETAX19", 0.0) + totals.get("INCOMETAX25", 0.0), 2))
        return split or abs(round(totals.get("INCOMETAX", 0.0), 2))

    def test_full_year_generate_and_validate(self):
        emp1 = self._create_employee("Jozko Mrkvicka", "8501011234", 2000.0)
        emp2 = self._create_employee("Anna Novakova", "9002022345", 1500.0)
        emp1.write({"private_street": "Krátka 7/3", "private_street2": "byt 12"})
        t1 = self._year_of_payslips(emp1)
        t2 = self._year_of_payslips(emp2)

        gross = abs(round(
            t1.get("GROSS", 0.0) + t2.get("GROSS", 0.0), 2))
        tax = abs(round(self._advance(t1) + self._advance(t2), 2))
        self.assertGreater(tax, 0.0, "an annual income-tax advance is expected")

        decl = self.env["l10n.sk.hlasenie"].with_company(self.company).create({
            "company_id": self.company.id,
            "year": str(YEAR),
        })
        self.assertTrue(decl.version_id, "Hlásenie version should default")
        self.assertEqual(decl.date_from, date(YEAR, 1, 1))
        self.assertEqual(decl.date_to, date(YEAR, 12, 31))
        decl.action_generate()
        self.assertEqual(decl.state, "generated")
        self.assertEqual(decl.lines_count, 2)

        xml_bytes = base64.b64decode(decl.xml_attachment_id.datas)
        schema = etree.XMLSchema(etree.parse(
            file_path("l10n_sk_hr_payroll_annual_tax_report/data/rh2023.xsd")))
        root = etree.fromstring(xml_bytes)
        schema.assertValid(root)  # strict XSD validation

        # root + header
        self.assertEqual(etree.QName(root).localname, "dokument")
        self.assertEqual(root.findtext("hlavicka/dic"), "1234567890")
        self.assertEqual(
            root.findtext("hlavicka/zdanovacieObdobie/rok"), str(YEAR))
        self.assertEqual(root.findtext("hlavicka/druhHlasenia/rh"), "1")
        self.assertEqual(root.findtext("hlavicka/pocetZamC5"), "2")
        # sídlo: the house number split off the street, never Street 2
        self.assertEqual(root.findtext("hlavicka/sidlo/ulica"), "Hlavna")
        self.assertEqual(root.findtext("hlavicka/sidlo/cislo"), "1")

        # aggregate Časť I: r00 = Σ gross, r01 = r04 = Σ withheld advance
        self.assertAlmostEqual(
            float(root.findtext("telo/cast1/r00")), gross, 2)
        self.assertAlmostEqual(
            float(root.findtext("telo/cast1/r01")), tax, 2)
        self.assertAlmostEqual(
            float(root.findtext("telo/cast1/r04")), tax, 2)

        # per-employee annex Časť V: exactly one page (two columns), and emp1's
        # column carries emp1's annual income + withheld advance.
        pages = root.findall("telo/cast5")
        self.assertEqual(len(pages), 1)
        cols = (root.findall("telo/cast5/c5stlpec1")
                + root.findall("telo/cast5/c5stlpec2"))
        by_rc = {c.findtext("c5rodneCislo"): c for c in cols}
        self.assertIn("8501011234", by_rc)
        col1 = by_rc["8501011234"]
        self.assertEqual(col1.findtext("c5ulica"), "Krátka")
        self.assertEqual(col1.findtext("c5cislo"), "7/3")
        self.assertAlmostEqual(
            float(col1.findtext("c5r3a")),
            abs(round(t1.get("GROSS", 0.0), 2)), 2)
        self.assertAlmostEqual(
            float(col1.findtext("c5r4a")), self._advance(t1), 2)

    def test_odd_employee_count_pads_with_empty_column(self):
        """A single employee still produces a valid page whose second column is
        an empty filler (exercises the odd-count annex path + strict XSD)."""
        emp = self._create_employee("Solo Zamestnanec", "8803033456", 1800.0)
        self._year_of_payslips(emp)
        decl = self.env["l10n.sk.hlasenie"].with_company(self.company).create({
            "company_id": self.company.id, "year": str(YEAR)})
        decl.action_generate()
        self.assertEqual(decl.state, "generated")

        xml_bytes = base64.b64decode(decl.xml_attachment_id.datas)
        schema = etree.XMLSchema(etree.parse(
            file_path("l10n_sk_hr_payroll_annual_tax_report/data/rh2023.xsd")))
        root = etree.fromstring(xml_bytes)
        schema.assertValid(root)
        self.assertEqual(root.findtext("hlavicka/pocetZamC5"), "1")
        self.assertEqual(len(root.findall("telo/cast5")), 1)
        # the filler column carries no birth number but a mandatory 0 flag
        col2 = root.find("telo/cast5/c5stlpec2")
        self.assertFalse((col2.findtext("c5rodneCislo") or "").strip())
        self.assertEqual(col2.findtext("c5doplnUdaj"), "0")

    def test_missing_dic_raises(self):
        emp = self._create_employee("No Dic", "7705054567", 1600.0)
        self._year_of_payslips(emp)
        self.company.l10n_sk_dic = False
        decl = self.env["l10n.sk.hlasenie"].with_company(self.company).create({
            "company_id": self.company.id, "year": str(YEAR)})
        with self.assertRaises(UserError):
            decl.action_generate()

    # ------------------------------------------------------------------
    # Corrections (opravné / dodatočné hlásenie)
    # ------------------------------------------------------------------
    def _hlasenie(self, **vals):
        base = {"company_id": self.company.id, "year": str(YEAR)}
        base.update(vals)
        return self.env["l10n.sk.hlasenie"].with_company(self.company).create(base)

    def _seed_year(self):
        emp = self._create_employee("Opravar Oto", "8501011234", 2000.0)
        self._year_of_payslips(emp)
        return emp

    def test_regular_hlasenie_sets_rh(self):
        """druhHlaseniaType is three mutually exclusive flags; a regular filing
        is rh=1 with the other two off."""
        self._seed_year()
        decl = self._hlasenie()
        decl.action_generate()
        xml = base64.b64decode(decl.xml_attachment_id.datas).decode("utf-8")
        self.assertIn("<rh>1</rh>", xml)
        self.assertIn("<oh>0</oh>", xml)
        self.assertIn("<dh>0</dh>", xml)

    def test_corrective_and_supplementary_move_the_flag(self):
        """All three flags used to be literals, so only a riadne hlásenie could
        ever be produced."""
        self._seed_year()
        first = self._hlasenie()
        first.action_generate()
        first.action_submit()

        for kind, expected in (("corrective", "oh"), ("supplementary", "dh")):
            with self.subTest(kind=kind):
                decl = self._hlasenie(correction_type=kind)
                decl.action_generate()
                xml = base64.b64decode(
                    decl.xml_attachment_id.datas).decode("utf-8")
                for flag in ("rh", "oh", "dh"):
                    want = "1" if flag == expected else "0"
                    self.assertIn("<%s>%s</%s>" % (flag, want, flag), xml)

    def test_hlasenie_has_no_storno(self):
        """The XSD offers riadne / opravné / dodatočné and nothing else."""
        offered = dict(
            self.env["l10n.sk.hlasenie"]
            .fields_get(["correction_type"])["correction_type"]["selection"]
        )
        self.assertEqual(
            set(offered), {"regular", "corrective", "supplementary"})

    def test_correction_needs_something_to_correct(self):
        self._seed_year()
        decl = self._hlasenie(correction_type="corrective")
        with self.assertRaises(UserError):
            decl.action_generate()

    def test_legal_form_comes_from_the_register_field(self):
        """pravnaForma carries the partner's recorded právna forma (it called
        a method no module defines and was always empty)."""
        partner = self.company.partner_id
        if "l10n_sk_legal_form" not in partner._fields:
            self.skipTest("l10n_sk_trade_registry is not installed")
        partner.l10n_sk_legal_form = "akciová spoločnosť"
        self._seed_year()
        decl = self._hlasenie()
        decl.action_generate()
        root = etree.fromstring(base64.b64decode(decl.xml_attachment_id.datas))
        self.assertEqual(root.findtext("hlavicka/po/pravnaForma"),
                         "akciová spoločnosť")

    # ------------------------------------------------------------------
    # III. časť — bonus paid beyond the advances (2026-10-27)
    # ------------------------------------------------------------------
    def test_bonus_beyond_the_advances_is_recapitulated(self):
        """r. 5 is capped at r. 4, so a bonus larger than the withheld advances
        was reported nowhere: III. časť (rA/rB/rC) was emitted empty. The
        poučenie: A = the whole bonus, B = the part paid from the advances,
        C = A − B (paid from the employer's own money)."""
        emp = self._create_employee("Bonus Velky", "8501011234", 915.0)
        emp.version_id.write({
            "l10n_sk_tax_declaration_signed": True,
            "l10n_sk_children_under_15": 4,
        })
        totals = self._year_of_payslips(emp)
        bonus = abs(round(totals.get("CHILD_BONUS", 0.0), 2))
        advance = self._advance(totals)
        self.assertGreater(bonus, advance,
                           "premise: the bonus exceeds the withheld advances")
        decl = self._hlasenie()
        decl.action_generate()
        root = etree.fromstring(base64.b64decode(decl.xml_attachment_id.datas))
        etree.XMLSchema(etree.parse(file_path(
            "l10n_sk_hr_payroll_annual_tax_report/data/rh2023.xsd"))
        ).assertValid(root)
        r04 = float(root.findtext("telo/cast1/r04"))
        r05 = float(root.findtext("telo/cast1/r05"))
        self.assertAlmostEqual(r05, r04, 2, "r. 5 is capped at r. 4")
        self.assertAlmostEqual(float(root.findtext("telo/cast3/rA")), bonus, 2)
        self.assertAlmostEqual(float(root.findtext("telo/cast3/rB")), r05, 2)
        self.assertAlmostEqual(
            float(root.findtext("telo/cast3/rC")), round(bonus - r05, 2), 2)
        self.assertGreater(float(root.findtext("telo/cast3/rC")), 0.0)

    def test_multi_word_first_name_is_kept(self):
        """The name was split as first word = first name, last word = surname,
        dropping everything between. The surname is the last word; the first
        name is everything before it."""
        self._create_employee("Ján Peter Novák", "8501011234", 2000.0)
        emp = self.env["hr.employee"].search(
            [("identification_id", "=", "8501011234"),
             ("company_id", "=", self.company.id)])
        self._year_of_payslips(emp)
        decl = self._hlasenie()
        decl.action_generate()
        root = etree.fromstring(base64.b64decode(decl.xml_attachment_id.datas))
        col = root.find("telo/cast5/c5stlpec1")
        self.assertEqual(col.findtext("c5meno"), "Ján Peter")
        self.assertEqual(col.findtext("c5priezvisko"), "Novák")


@tagged("post_install", "-at_install")
class TestSchemaPins(TransactionCase):
    """The bundled schemas must match data/SCHEMA_VERSION.

    Not a check that our copies are CURRENT — nothing local can answer that,
    and a schema revised in place by the authority validates exactly as
    before. What this checks is that the bundled bytes are the ones recorded
    in SCHEMA_VERSION, and that no schema sits in data/ unpinned.
    """

    @staticmethod
    def _data_dir():
        import os
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(here, "data")

    def _pins(self):
        import os
        pins = {}
        path = os.path.join(self._data_dir(), "SCHEMA_VERSION")
        with open(path, encoding="utf-8") as fh:
            for raw in fh:
                parts = raw.split()
                if (len(parts) == 3 and parts[0].endswith(".xsd")
                        and "/" not in parts[0]):
                    pins[parts[0]] = (parts[1], int(parts[2]))
        return pins

    def test_bundled_schemas_match_the_pinned_digests(self):
        import hashlib
        import os
        pins = self._pins()
        self.assertTrue(pins, "SCHEMA_VERSION lists no schemas")
        for name, (digest, size) in pins.items():
            path = os.path.join(self._data_dir(), name)
            self.assertTrue(os.path.exists(path),
                            "%s is pinned but missing" % name)
            with open(path, "rb") as fh:
                blob = fh.read()
            self.assertEqual(len(blob), size, "%s size moved" % name)
            self.assertEqual(
                hashlib.md5(blob).hexdigest(), digest,
                "%s does not match its pin — if this is a deliberate "
                "refresh, update data/SCHEMA_VERSION" % name)

    def test_every_bundled_schema_is_pinned(self):
        import os
        on_disk = {f for f in os.listdir(self._data_dir())
                   if f.endswith(".xsd")}
        self.assertEqual(on_disk, set(self._pins()),
                         "unpinned schema(s): %s"
                         % sorted(on_disk - set(self._pins())))
