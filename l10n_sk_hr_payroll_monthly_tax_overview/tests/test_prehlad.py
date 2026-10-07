# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Runtime test — proves Prehľad generation + XSD validation on BOTH payroll
engines. Detects whichever SK payroll engine is installed (the ``payroll`` engine
``l10n_sk_hr_payroll_oca`` or the ``l10n_sk_hr_payroll``), drives it to a
computed payslip, generates the monthly Prehľad and validates the produced XML
against the shipped ``prehlad2026.xsd``."""
import base64
import unittest
from datetime import date

from lxml import etree

from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tools import file_path


@tagged("post_install", "-at_install")
class TestPrehlad(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.engine = cls._detect_engine()
        if not cls.engine:
            raise unittest.SkipTest(
                "no SK payroll engine installed "
                "(l10n_sk_hr_payroll_oca or l10n_sk_hr_payroll)")
        cls.company = cls.env["res.company"].create({
            "name": "SK Prehlad Co s.r.o.",
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

    def _employee_payslip(self, wage=2000.0):
        emp_vals = {
            "name": "Jozko Mrkvicka",
            "company_id": self.company.id,
            "resource_calendar_id": self.calendar.id,
            "identification_id": "8501011234",
            "date_version": date(2026, 1, 1),
            "contract_date_start": date(2026, 1, 1),
            "wage": wage,
        }
        if self.engine == "oca":
            emp_vals["struct_id"] = self.structure.id
        else:
            emp_vals["structure_type_id"] = self.structure.type_id.id
        employee = self.env["hr.employee"].with_company(
            self.company).create(emp_vals)

        slip = self.env["hr.payslip"].with_company(self.company).create({
            "name": "Payslip",
            "employee_id": employee.id,
            "struct_id": self.structure.id,
            "company_id": self.company.id,
            "date_from": date(2026, 3, 1),
            "date_to": date(2026, 3, 31),
        })
        if self.engine == "ee":
            slip = slip.with_context(salary_simulation=True)
        slip.compute_sheet()
        return employee, slip

    def test_generate_and_validate(self):
        employee, slip = self._employee_payslip()
        totals = {line.code: line.total for line in slip.line_ids}
        split = abs(round(
            totals.get("INCOMETAX19", 0.0) + totals.get("INCOMETAX25", 0.0), 2))
        tax = split or abs(round(totals.get("INCOMETAX", 0.0), 2))
        self.assertGreater(tax, 0.0, "an income-tax advance must be computed")
        gross = abs(round(totals.get("GROSS", 0.0), 2))

        decl = self.env["l10n.sk.prehlad"].with_company(self.company).create({
            "company_id": self.company.id,
            "year": "2026",
            "month": "3",
            "payment_date": date(2026, 3, 31),
        })
        self.assertTrue(decl.version_id, "Prehľad version should default")
        decl.action_generate()
        self.assertEqual(decl.state, "generated")

        xml_bytes = base64.b64decode(decl.xml_attachment_id.datas)
        schema = etree.XMLSchema(etree.parse(
            file_path("l10n_sk_hr_payroll_monthly_tax_overview/data/prehlad2026.xsd")))
        root = etree.fromstring(xml_bytes)
        schema.assertValid(root)

        # root + header
        self.assertEqual(etree.QName(root).localname, "dokument")
        self.assertEqual(root.findtext("hlavicka/dic"), "1234567890")
        self.assertEqual(
            root.findtext("hlavicka/zdanovacieObdobie/mesiac"), "3")

        # r00 = gross, r01/suma = withheld tax advance, r04 = r01
        self.assertAlmostEqual(
            float(root.findtext("telo/cast1/r00")), gross, 2)
        self.assertAlmostEqual(
            float(root.findtext("telo/cast1/r01/suma")), tax, 2)
        self.assertAlmostEqual(
            float(root.findtext("telo/cast1/r04")), tax, 2)
        # r08 = r04 - r05 (no children here -> equals the advance)
        r05 = float(root.findtext("telo/cast1/r05"))
        r08 = float(root.findtext("telo/cast1/r08"))
        self.assertAlmostEqual(r08, round(tax - r05, 2), 2)

    def test_missing_dic_raises(self):
        self._employee_payslip()
        self.company.l10n_sk_dic = False
        decl = self.env["l10n.sk.prehlad"].with_company(self.company).create({
            "company_id": self.company.id, "year": "2026", "month": "3"})
        with self.assertRaises(UserError):
            decl.action_generate()

    # ------------------------------------------------------------------
    # Corrections (opravný Prehľad)
    # ------------------------------------------------------------------
    def _prehlad(self, **vals):
        base = {
            "company_id": self.company.id,
            "year": "2026",
            "month": "3",
            "payment_date": date(2026, 3, 31),
        }
        base.update(vals)
        return self.env["l10n.sk.prehlad"].with_company(self.company).create(base)

    def test_regular_prehlad_emits_riadny(self):
        """The default filing is riadny=1 / opravny=0."""
        self._employee_payslip()
        decl = self._prehlad()
        self.assertEqual(decl.correction_type, "regular")
        self.assertFalse(decl.is_correction)
        decl.action_generate()
        xml = base64.b64decode(decl.xml_attachment_id.datas).decode("utf-8")
        self.assertIn("<riadny>1</riadny>", xml)
        self.assertIn("<opravny>0</opravny>", xml)

    def test_corrective_prehlad_emits_opravny(self):
        """An opravný flips both flags. Before this the pair was hardcoded, so
        the form could only ever produce a regular Prehľad."""
        self._employee_payslip()
        first = self._prehlad()
        first.action_generate()
        first.action_submit()

        fix = self._prehlad(correction_type="corrective")
        self.assertTrue(fix.is_correction)
        fix.action_generate()
        xml = base64.b64decode(fix.xml_attachment_id.datas).decode("utf-8")
        self.assertIn("<riadny>0</riadny>", xml)
        self.assertIn("<opravny>1</opravny>", xml)

    def test_correction_needs_something_to_correct(self):
        """An opravný for a period never filed is a rejection at best and a
        duplicate at worst, so generating one is refused."""
        # Seed a payslip: without one the generation would be refused for
        # having nothing to report, and the test would pass whether or not the
        # correction guard exists.
        self._employee_payslip()
        fix = self._prehlad(correction_type="corrective")
        with self.assertRaises(UserError):
            fix.action_generate()

    def test_a_draft_original_does_not_count_as_filed(self):
        """Only a SUBMITTED filing can be amended — a draft or generated one
        has not reached the Finančná správa."""
        self._employee_payslip()
        first = self._prehlad()
        first.action_generate()          # generated, not submitted
        fix = self._prehlad(correction_type="corrective")
        with self.assertRaises(UserError):
            fix.action_generate()

    def test_unsupported_correction_types_are_refused(self):
        """The FS Prehľad wire format has no dodatočný and no storno, so the
        selection must not offer them."""
        offered = dict(
            self.env["l10n.sk.prehlad"]
            .fields_get(["correction_type"])["correction_type"]["selection"]
        )
        self.assertEqual(set(offered), {"regular", "corrective"})
        # A dynamic selection cannot be validated by the ORM the way a literal
        # one is, so the constraint is what actually stops it — which is the
        # reason the constraint exists rather than relying on the field.
        with self.assertRaises(ValidationError):
            self._prehlad(correction_type="storno")
