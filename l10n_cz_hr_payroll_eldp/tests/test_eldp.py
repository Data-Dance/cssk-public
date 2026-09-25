# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Runtime test — proves ELDP generation + XSD validation on BOTH payroll
engines. Detects whichever CZ payroll engine is installed (the ``payroll`` engine
``l10n_cz_hr_payroll_oca`` or ``l10n_cz_hr_payroll_ee``), drives it to a computed
payslip, generates the annual ELDP and validates the produced XML against the
shipped ``ELDP09.xsd``."""
import base64
from datetime import date

from lxml import etree

from odoo.tests import TransactionCase, tagged
from odoo.tools import file_path

NS = {"e": "http://schemas.cssz.cz/ELDP09"}


@tagged("post_install", "-at_install")
class TestEldp(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.engine = cls._detect_engine()
        cls.company = cls.env["res.company"].create({
            "name": "CZ ELDP Co",
            "country_id": cls.env.ref("base.cz").id,
            "company_registry": "12345678",
            "street": "Hluboká",
            "street2": "1",
            "city": "Praha",
            "zip": "11000",
            "l10n_cz_ossz_vs": "1234567890",
            "l10n_cz_ossz_code": "100",
        })
        cls.env.user.company_ids |= cls.company
        cls.env = cls.env(context=dict(
            cls.env.context, allowed_company_ids=cls.company.ids))
        if cls.engine == "oca":
            cls.env.user.group_ids |= cls.env.ref(
                "payroll.group_payroll_manager")
            cls.structure = cls.env.ref(
                "l10n_cz_hr_payroll_oca.hr_payroll_structure_cz_employee_salary")
        else:
            cls.env.user.group_ids |= cls.env.ref(
                "hr_payroll.group_hr_payroll_manager")
            cls.structure = cls.env.ref(
                "l10n_cz_hr_payroll_ee.hr_payroll_structure_cz_employee_salary")
        cls.calendar = cls.env["resource.calendar"].create(
            {"name": "CZ 40h", "company_id": cls.company.id})

    @classmethod
    def _detect_engine(cls):
        if cls.env.ref(
                "l10n_cz_hr_payroll_oca.hr_payroll_structure_cz_employee_salary",
                raise_if_not_found=False):
            return "oca"
        return "ee"

    def _employee_payslip(self, wage=50000.0):
        emp_vals = {
            "name": "Pavel Novak",
            "company_id": self.company.id,
            "resource_calendar_id": self.calendar.id,
            "identification_id": "8001011117",  # rodné číslo
            "birthday": date(1980, 1, 1),
            "place_of_birth": "Praha",
            "private_street": "Dlouhá 5",
            "private_city": "Praha",
            "private_zip": "11000",
            "private_country_id": self.env.ref("base.cz").id,
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
        employee.version_id.write({"l10n_cz_tax_declaration": True})

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
        gross = abs(round(
            sum(line.total for line in slip.line_ids
                if line.code == "GROSS"), 0))
        self.assertGreater(gross, 0.0, "GROSS must be computed")

        decl = self.env["l10n.cz.eldp"].with_company(self.company).create({
            "company_id": self.company.id,
            "year": "2026",
        })
        self.assertTrue(decl.version_id, "ELDP version should default")
        decl.action_generate()
        self.assertEqual(decl.state, "generated")
        self.assertTrue(decl.xml_attachment_id)

        xml_bytes = base64.b64decode(decl.xml_attachment_id.datas)
        schema = etree.XMLSchema(etree.parse(
            file_path("l10n_cz_hr_payroll_eldp/data/ELDP09.xsd")))
        root = etree.fromstring(xml_bytes)
        schema.assertValid(root)

        eldp = root.findall(".//e:eldp09", NS)
        self.assertEqual(len(eldp), 1)
        client = eldp[0].find("e:client", NS)
        self.assertEqual(client.get("bno"), "8001011117")
        self.assertEqual(eldp[0].get("yer"), "2026")
        self.assertEqual(eldp[0].get("typ"), "1")  # ongoing employment

        t1 = eldp[0].find(".//e:t1", NS)
        # assessment base = the year's gross (single March payslip here)
        self.assertEqual(int(t1.get("inc")), int(gross))
        # full-year employment (no end date) -> 365 insured days
        self.assertEqual(int(t1.get("din")), 365)

    def test_ended_employment_typ2(self):
        employee, slip = self._employee_payslip()
        employee.version_id.write({"contract_date_end": date(2026, 6, 30)})
        decl = self.env["l10n.cz.eldp"].with_company(self.company).create({
            "company_id": self.company.id, "year": "2026"})
        decl.action_generate()
        xml_bytes = base64.b64decode(decl.xml_attachment_id.datas)
        root = etree.fromstring(xml_bytes)
        eldp = root.find(".//e:eldp09", NS)
        self.assertEqual(eldp.get("typ"), "2")  # ended within the year
        t1 = eldp.find(".//e:t1", NS)
        self.assertEqual(int(t1.get("din")), 181)  # Jan 1 - Jun 30 (2026)
