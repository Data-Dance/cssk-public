# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Runtime test — proves VPP generation + XSD validation on BOTH payroll
engines, scoped to a dohoda (DoVP) employee. Detects whichever SK payroll
engine is installed, drives it to a computed dohoda payslip, generates the VPP
declaration and validates the produced XML against the shipped
``VPP-v2026.xsd``."""
import base64
from datetime import date

from lxml import etree

from odoo.tests import TransactionCase, tagged
from odoo.tools import file_path

NS = {"v": "http://socpoist.sk/xsd/vpp2026"}


@tagged("post_install", "-at_install")
class TestVpp(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.engine = cls._detect_engine()
        cls.company = cls.env["res.company"].create({
            "name": "SK VPP Co",
            "country_id": cls.env.ref("base.sk").id,
            "company_registry": "12345678",
            "l10n_sk_sp_vs": "1234567890",
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
        if cls.env.ref(
                "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_employee_salary",
                raise_if_not_found=False):
            return "oca"
        return "ee"

    def _dohodar_payslip(self, agreement="dovp", wage=1000.0):
        emp_vals = {
            "name": "Dohodar Peter",
            "company_id": self.company.id,
            "resource_calendar_id": self.calendar.id,
            "identification_id": "8501011234",  # rodné číslo (10 digits)
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
        # Mark the current version as a dohoda so the rules and the VPP scope
        # both recognise it (engine-neutral: the field lives on hr.version).
        employee.version_id.l10n_sk_agreement_type = agreement

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
        employee, slip = self._dohodar_payslip()
        totals = {line.code: line.total for line in slip.line_ids}
        social_er = abs(round(totals.get("SOCIALEMPLOYERTOTAL", 0.0), 2))
        social_ee = abs(round(totals.get("SOCIALEMPLOYEETOTAL", 0.0), 2))
        self.assertGreater(social_er, 0.0, "employer social must be computed")
        # DoVP is irregular income -> no sickness / unemployment employee side.
        self.assertAlmostEqual(abs(totals.get("SICK", 0.0)), 0.0, 2)
        self.assertAlmostEqual(abs(totals.get("UNEMPLOYMENT", 0.0)), 0.0, 2)

        decl = self.env["l10n.sk.vpp"].with_company(self.company).create({
            "company_id": self.company.id,
            "year": "2026",
            "month": "3",
        })
        self.assertTrue(decl.version_id, "VPP version should default")
        decl.action_generate()
        self.assertEqual(decl.state, "generated")

        xml_bytes = base64.b64decode(decl.xml_attachment_id.datas)
        schema = etree.XMLSchema(etree.parse(
            file_path("l10n_sk_hr_payroll_vpp/data/VPP-v2026.xsd")))
        root = etree.fromstring(xml_bytes)
        schema.assertValid(root)

        # Header shape.
        self.assertEqual(root.find("v:cisloVykazu", NS).text, "03992026")
        self.assertEqual(
            root.find("v:obdobieVyplPrijmov", NS).text, "032026")

        # Aggregate total matches the payslip.
        spolu = float(root.find(".//v:poistne/v:spoluPoistne", NS).text)
        self.assertAlmostEqual(spolu, round(social_er + social_ee, 2), 2)

        # Per-employee annex present with rodné číslo and dohoda typZec.
        annex = root.findall(".//v:poistneZamestnanca", NS)
        self.assertEqual(len(annex), 1)
        self.assertEqual(annex[0].get("rc"), "8501011234")
        self.assertEqual(annex[0].get("typZec"), "ZECD1N")
        self.assertEqual(annex[0].get("obdobie"), "032026")

    def test_non_dohoda_excluded(self):
        """A standard employment payslip must NOT appear on the VPP."""
        from odoo.exceptions import UserError
        employee, slip = self._dohodar_payslip(agreement="none")
        decl = self.env["l10n.sk.vpp"].with_company(self.company).create({
            "company_id": self.company.id, "year": "2026", "month": "3"})
        # No dohoda payslip in the period -> generation refuses (nothing to file)
        with self.assertRaises(UserError):
            decl.action_generate()
