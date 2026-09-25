# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Runtime test — proves ELDP annual generation + XSD validation on BOTH
payroll engines. Detects the installed SK payroll engine, drives it to a
computed payslip inside the year, generates the annual ELDP and validates the
produced XML against the shipped ``ELDP-v2015_1.3.xsd``."""
import base64
from datetime import date

from lxml import etree

from odoo.tests import TransactionCase, tagged
from odoo.tools import file_path

NS = {"e": "http://socpoist.sk/xsd/eldpzec"}


@tagged("post_install", "-at_install")
class TestEldp(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.engine = cls._detect_engine()
        cls.company = cls.env["res.company"].create({
            "name": "SK ELDP Co",
            "country_id": cls.env.ref("base.sk").id,
            "company_registry": "12345678",
            "l10n_sk_sp_vs": "1234567890",
            "city": "Bratislava",
            "zip": "81101",
            "street": "Hlavna 1",
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

    def _employee_payslip(self, wage=2000.0):
        emp_vals = {
            "name": "Jozko Mrkvicka",
            "company_id": self.company.id,
            "resource_calendar_id": self.calendar.id,
            "identification_id": "8501011234",
            "birthday": date(1985, 1, 1),
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
        gross = abs(round(totals.get("GROSS", 0.0), 2))
        self.assertGreater(gross, 0.0, "GROSS must be computed")

        decl = self.env["l10n.sk.eldp"].with_company(self.company).create({
            "company_id": self.company.id,
            "year": "2026",
        })
        self.assertTrue(decl.version_id, "ELDP version should default")
        # Whole-year period.
        self.assertEqual(decl.date_from, date(2026, 1, 1))
        self.assertEqual(decl.date_to, date(2026, 12, 31))
        decl.action_generate()
        self.assertEqual(decl.state, "generated")

        xml_bytes = base64.b64decode(decl.xml_attachment_id.datas)
        schema = etree.XMLSchema(etree.parse(
            file_path("l10n_sk_hr_payroll_eldp/data/ELDP-v2015_1.3.xsd")))
        root = etree.fromstring(xml_bytes)
        schema.assertValid(root)

        # One eldpZec for the employee, with rc and the pension base = GROSS.
        rows = root.findall(".//e:eldpZec", NS)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].find(".//e:poistenec/e:rc", NS).text,
                         "8501011234")
        vz = root.find(".//e:vzZaObdobiePoist", NS)
        self.assertEqual(vz.get("rok"), "2026")
        self.assertAlmostEqual(float(vz.get("vzDP")), gross, 2)
        # Still employed -> relationship reported as ongoing (trva=1).
        self.assertEqual(rows[0].find(".//e:poistVztah/e:trva", NS).text, "1")
