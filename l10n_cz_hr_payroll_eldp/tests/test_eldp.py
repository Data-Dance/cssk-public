# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Runtime test — proves ELDP generation + XSD validation on BOTH payroll
engines. Detects whichever CZ payroll engine is installed (the ``payroll`` engine
``l10n_cz_hr_payroll_oca`` or ``l10n_cz_hr_payroll_ee``), drives it to a computed
payslip, generates the annual ELDP and validates the produced XML against the
shipped ``ELDP09.xsd``."""
import base64
import calendar
from datetime import date

from lxml import etree

from odoo.addons.l10n_cssk_payroll_declaration_base.tests.common import (
    confirm_payslips,
)
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
            "company_registry": "12345679",
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

    def _employee_payslip(self, wage=50000.0, year=2025, end=None):
        employee = self._employee(wage, year, end)
        return employee, self._payslip(employee, year, 3)

    def _employee(self, wage=50000.0, year=2025, end=None):
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
            "date_version": date(year, 1, 1),
            "contract_date_start": date(year, 1, 1),
            "contract_date_end": end,
            "wage": wage,
        }
        if self.engine == "oca":
            emp_vals["struct_id"] = self.structure.id
        else:
            emp_vals["structure_type_id"] = self.structure.type_id.id
        employee = self.env["hr.employee"].with_company(
            self.company).create(emp_vals)
        employee.version_id.write({"l10n_cz_tax_declaration": True})
        return employee

    def _payslip(self, employee, year, month, confirm=True):
        last = calendar.monthrange(year, month)[1]
        slip = self.env["hr.payslip"].with_company(self.company).create({
            "name": "Payslip",
            "employee_id": employee.id,
            "struct_id": self.structure.id,
            "company_id": self.company.id,
            "date_from": date(year, month, 1),
            "date_to": date(year, month, last),
        })
        if self.engine == "ee":
            slip = slip.with_context(salary_simulation=True)
        slip.compute_sheet()
        if confirm:
            # Declarations report confirmed payroll only.
            confirm_payslips(slip)
        return slip

    def test_generate_and_validate(self):
        employee, slip = self._employee_payslip()
        gross = abs(round(
            sum(line.total for line in slip.line_ids
                if line.code == "GROSS"), 0))
        self.assertGreater(gross, 0.0, "GROSS must be computed")

        decl = self.env["l10n.cz.eldp"].with_company(self.company).create({
            "company_id": self.company.id,
            "year": "2025",
        })
        decl.action_generate()
        self.assertTrue(decl.version_id, "the ELDP vintage follows the year")
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
        # "Pavel Novak": příjmení (sur) is the LAST word — they were swapped.
        name = client.find("e:name", NS)
        self.assertEqual(name.get("sur"), "Novak")
        self.assertEqual(name.get("fir"), "Pavel")
        self.assertEqual(eldp[0].get("yer"), "2025")
        self.assertEqual(eldp[0].get("typ"), "1")  # ongoing employment

        t1 = eldp[0].find(".//e:t1", NS)
        # assessment base = the year's insured base (single March payslip,
        # below the cap, so equal to its gross)
        self.assertEqual(int(t1.get("inc")), int(gross))
        # full-year employment (no end date) -> 365 insured days
        self.assertEqual(int(t1.get("din")), 365)

    def test_ended_employment_typ2(self):
        employee, slip = self._employee_payslip()
        employee.version_id.write({"contract_date_end": date(2025, 6, 30)})
        decl = self.env["l10n.cz.eldp"].with_company(self.company).create({
            "company_id": self.company.id, "year": "2025"})
        decl.action_generate()
        xml_bytes = base64.b64decode(decl.xml_attachment_id.datas)
        root = etree.fromstring(xml_bytes)
        eldp = root.find(".//e:eldp09", NS)
        self.assertEqual(eldp.get("typ"), "2")  # ended within the year
        t1 = eldp.find(".//e:t1", NS)
        self.assertEqual(int(t1.get("din")), 181)  # Jan 1 - Jun 30 (2025)

    def test_2026_refused_for_an_ongoing_employee(self):
        """Zákon č. 360/2025 Sb., čl. V: from 2026 the ČSSZ compiles the ELDP
        from JMHZ; the employer files one only for an employee whose pension
        insurance ended before 1 April 2026."""
        from odoo.exceptions import UserError
        self._employee_payslip(year=2026)
        decl = self.env["l10n.cz.eldp"].with_company(self.company).create({
            "company_id": self.company.id, "year": "2026"})
        with self.assertRaisesRegex(UserError, "JMHZ"):
            decl.action_generate()
        self.assertFalse(decl.xml_attachment_id)

    def test_2026_for_an_employee_who_left_before_april(self):
        employee, _slip = self._employee_payslip(
            year=2026, end=date(2026, 3, 31))
        decl = self.env["l10n.cz.eldp"].with_company(self.company).create({
            "company_id": self.company.id, "year": "2026"})
        decl.action_generate()
        root = etree.fromstring(base64.b64decode(decl.xml_attachment_id.datas))
        eldp = root.findall(".//e:eldp09", NS)
        self.assertEqual(len(eldp), 1)
        self.assertEqual(eldp[0].get("typ"), "2")
        self.assertEqual(int(eldp[0].find(".//e:t1", NS).get("din")), 90)

    def test_2027_is_refused(self):
        from odoo.exceptions import UserError
        decl = self.env["l10n.cz.eldp"].with_company(self.company).create({
            "company_id": self.company.id, "year": "2027"})
        with self.assertRaisesRegex(UserError, "discontinued"):
            decl.action_generate()

    def _t1_rows(self):
        decl = self.env["l10n.cz.eldp"].with_company(self.company).create({
            "company_id": self.company.id, "year": "2025"})
        decl.action_generate()
        root = etree.fromstring(base64.b64decode(decl.xml_attachment_id.datas))
        etree.XMLSchema(etree.parse(file_path(
            "l10n_cz_hr_payroll_eldp/data/ELDP09.xsd"))).assertValid(root)
        eldp = root.find(".//e:eldp09", NS)
        return eldp, eldp.findall(".//e:t1", NS)

    def test_periods_come_from_every_contract_version(self):
        """An employee who left on 31 March and was re-hired on 1 July has
        two pension periods. Reading only today's version reported one
        period from 1 July and dropped January-March."""
        employee, _slip = self._employee_payslip(end=date(2025, 3, 31))
        employee.create_version({
            "date_version": date(2025, 7, 1),
            "contract_date_start": date(2025, 7, 1),
            "contract_date_end": False,
        })
        self._payslip(employee, 2025, 7)
        eldp, rows = self._t1_rows()
        self.assertEqual(len(rows), 2)
        self.assertEqual((rows[0].get("fro"), rows[0].get("to")),
                         ("2025-01-01", "2025-03-31"))
        self.assertEqual(int(rows[0].get("din")), 90)
        self.assertEqual((rows[1].get("fro"), rows[1].get("to")),
                         ("2025-07-01", "2025-12-31"))
        self.assertEqual(int(rows[1].get("din")), 184)
        self.assertEqual(eldp.find(".//e:items", NS).get("coun"), "2")
        self.assertEqual(eldp.get("typ"), "1")
        # Each period carries the base of its own payslips.
        self.assertEqual(int(rows[0].get("inc")), 50000)
        self.assertEqual(int(rows[1].get("inc")), 50000)

    def test_base_is_capped_at_the_maximum_assessment_base(self):
        """§ 15a zák. 589/1992 Sb.: the base stops at the annual maximum
        (2 234 736 Kč in 2025). Summing GROSS reported 3 300 000 for three
        months of 1 100 000; the insured base is 2 234 736."""
        employee = self._employee(wage=1100000.0)
        # January and February first, so the March payslip sees them.
        for month in (1, 2, 3):
            self._payslip(employee, 2025, month)
        _eldp, rows = self._t1_rows()
        self.assertEqual(int(rows[0].get("inc")), 2234736)

    def test_draft_payslips_are_not_reported(self):
        employee, slip = self._employee_payslip()
        self._payslip(employee, 2025, 4, confirm=False)
        _eldp, rows = self._t1_rows()
        self.assertEqual(int(rows[0].get("inc")), 50000)
