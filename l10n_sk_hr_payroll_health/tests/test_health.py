# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Runtime test — proves dávka 514 generation on BOTH payroll engines against
the official 514-2023.xsd element model (root MZSR). Because that published
schema is internally defective (single-char patterns, impossible integer
bounds) no instance can pass assertValid, so the pipeline runs it non-fatally;
the test asserts well-formedness + structural conformance (the three blocks,
NumberOfRecords = PersonData count, insurer code) and that the per-employee
health advances match the payslip. It also asserts the shipped XSD compiles."""
import base64
import unittest
from datetime import date

from lxml import etree

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged
from odoo.tools import file_path


@tagged("post_install", "-at_install")
class TestHealth514(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.engine = cls._detect_engine()
        if not cls.engine:
            raise unittest.SkipTest(
                "no SK payroll engine installed "
                "(l10n_sk_hr_payroll_oca or l10n_sk_hr_payroll)")
        cls.company = cls.env["res.company"].create({
            "name": "SK Health Co s.r.o.",
            "country_id": cls.env.ref("base.sk").id,
            "company_registry": "12345679",
            "l10n_sk_dic": "1234567890",
            "l10n_sk_health_insurer_code": "24",
            "l10n_sk_health_payer_number": "9900112233",
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
        health_ee = abs(round(totals.get("HEALTH", 0.0), 2))
        health_er = abs(round(totals.get("HEALTHEMPLOYER", 0.0), 2))
        self.assertGreater(health_ee, 0.0, "employee health must be computed")
        self.assertGreater(health_er, 0.0, "employer health must be computed")

        decl = self.env["l10n.sk.health"].with_company(self.company).create({
            "company_id": self.company.id,
            "year": "2026",
            "month": "3",
            "payment_date": date(2026, 3, 31),
        })
        self.assertTrue(decl.version_id, "dávka 514 version should default")
        self.assertEqual(decl.insurer_code, "24", "insurer defaults from company")
        decl.action_generate()
        self.assertEqual(decl.state, "generated")

        xml_bytes = base64.b64decode(decl.xml_attachment_id.datas)
        root = etree.fromstring(xml_bytes)  # well-formed
        self.assertEqual(etree.QName(root).localname, "MZSR")

        # the shipped official XSD compiles (loads as an XMLSchema)
        etree.XMLSchema(etree.parse(
            file_path("l10n_sk_hr_payroll_health/data/514-2023.xsd")))

        # structural: the three header blocks present
        for block in ("Identification", "CorporateBody", "InsuranceBody"):
            self.assertIsNotNone(root.find(block), "missing %s" % block)

        # The DIČ must actually arrive. This element was emitted EMPTY for any
        # company without one -- _preflight checked the IČO, the payer number
        # and the insurer but not the DIČ, and the render context read it
        # through a getattr default, so the dávka went to the insurer with
        # nothing in it and raised nothing.
        self.assertEqual(
            root.findtext("CorporateBody/CompanyIDTaxCode")
            or root.findtext(".//CompanyIDTaxCode"),
            "1234567890",
            "the DIČ must reach <CompanyIDTaxCode>")

        # identification: 4-digit insurer code, IČO, NumberOfRecords
        self.assertEqual(
            root.findtext("Identification/CodeOfHealthInsuranceCompany"),
            "2400")
        self.assertEqual(root.findtext("Identification/IDCode"), "12345679")
        self.assertEqual(root.findtext("Identification/NumberOfRecords"), "1")
        self.assertEqual(root.findtext("CorporateBody/Period"), "2026-03")

        # one employee row, advances match the payslip
        rows = root.findall("PersonData")
        self.assertEqual(len(rows), 1)
        self.assertEqual(
            rows[0].findtext("IdentificationNumberOfInsured"), "8501011234")
        self.assertAlmostEqual(
            float(rows[0].findtext("DepositOfEmployee")), health_ee, 2)
        self.assertAlmostEqual(
            float(rows[0].findtext("DepositOfEmployer")), health_er, 2)

        # aggregate employer total matches the single row
        self.assertAlmostEqual(
            float(root.findtext("InsuranceBody/DepositOfInsurance1")),
            health_er, 2)

    def test_missing_payer_number_raises(self):
        self._employee_payslip()
        self.company.l10n_sk_health_payer_number = False
        decl = self.env["l10n.sk.health"].with_company(self.company).create({
            "company_id": self.company.id, "year": "2026", "month": "3"})
        with self.assertRaises(UserError):
            decl.action_generate()

    def test_generation_refuses_without_a_dic(self):
        """The silent failure this guards: no DIČ produced an empty
        <CompanyIDTaxCode> and no error. The Prehľad and the Hlásenie always
        refused in that situation; the dávka 514 did not."""
        self.company.l10n_sk_dic = False
        decl = self.env["l10n.sk.health"].with_company(self.company).create({
            "company_id": self.company.id,
            "year": "2026",
            "month": "3",
            "payment_date": date(2026, 3, 31),
        })
        with self.assertRaises(UserError):
            decl.action_generate()
