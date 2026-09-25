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
            file_path("l10n_sk_hr_payroll_hlasenie/data/rh2023.xsd")))
        root = etree.fromstring(xml_bytes)
        schema.assertValid(root)  # strict XSD validation

        # root + header
        self.assertEqual(etree.QName(root).localname, "dokument")
        self.assertEqual(root.findtext("hlavicka/dic"), "1234567890")
        self.assertEqual(
            root.findtext("hlavicka/zdanovacieObdobie/rok"), str(YEAR))
        self.assertEqual(root.findtext("hlavicka/druhHlasenia/rh"), "1")
        self.assertEqual(root.findtext("hlavicka/pocetZamC5"), "2")

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
            file_path("l10n_sk_hr_payroll_hlasenie/data/rh2023.xsd")))
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
