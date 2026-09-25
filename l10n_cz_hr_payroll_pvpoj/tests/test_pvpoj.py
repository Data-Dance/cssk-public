# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Runtime test — proves PVPOJ generation + XSD validation on BOTH payroll
engines. The test detects whichever CZ payroll engine is installed (the ``payroll`` engine
``l10n_cz_hr_payroll_oca`` or the ``l10n_cz_hr_payroll_ee``) and drives it
to a computed payslip, then generates the PVPOJ declaration and validates the
produced XML against the shipped ``PVPOJ25.xsd``."""
from datetime import date

from lxml import etree

from odoo.tests import TransactionCase, tagged
from odoo.tools import file_path


@tagged("post_install", "-at_install")
class TestPvpoj(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.engine = cls._detect_engine()
        cls.company = cls.env["res.company"].create({
            "name": "CZ PVPOJ Co",
            "country_id": cls.env.ref("base.cz").id,
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
        totals = {line.code: line.total for line in slip.line_ids}
        self.assertAlmostEqual(totals.get("SOCIALEETOT", 0.0), -3550.0, 2)
        self.assertAlmostEqual(totals.get("SOCIALERTOT", 0.0), 12400.0, 2)

        decl = self.env["l10n.cz.pvpoj"].with_company(self.company).create({
            "company_id": self.company.id,
            "year": "2026",
            "month": "3",
        })
        self.assertTrue(decl.version_id, "PVPOJ version should default")
        decl.action_generate()
        self.assertEqual(decl.state, "generated")
        self.assertTrue(decl.xml_attachment_id)

        # XSD-validate the produced XML against the shipped schema.
        import base64
        xml_bytes = base64.b64decode(decl.xml_attachment_id.datas)
        schema = etree.XMLSchema(etree.parse(
            file_path("l10n_cz_hr_payroll_pvpoj/data/PVPOJ25.xsd")))
        root = etree.fromstring(xml_bytes)
        schema.assertValid(root)

        # Key totals match the payslip.
        ns = {"p": "http://schemas.cssz.cz/POJ/PVPOJ2025"}
        er = root.find(".//p:pojistneZamestnavateleCelkem", ns).text
        ee = root.find(".//p:pojistneZamestnance", ns).text
        celkem = root.find(".//p:pojistneCelkem", ns).text
        self.assertEqual(int(er), 12400)
        self.assertEqual(int(ee), 3550)
        self.assertEqual(int(celkem), 15950)

    def _discount_employee_payslip(self, wage=20000.0):
        """A part-time §7a-eligible employee -> a SOCIAL_DISCOUNT payslip line."""
        pt_cal = self.env["resource.calendar"].create({
            "name": "CZ Part Time 20h",
            "company_id": self.company.id,
            "attendance_ids": [
                (0, 0, {
                    "name": "Day %s" % d,
                    "dayofweek": str(d),
                    "hour_from": 8.0,
                    "hour_to": 12.0,
                    "day_period": "morning",
                }) for d in range(5)
            ],
        })
        emp_vals = {
            "name": "Jana Kratka",
            "company_id": self.company.id,
            "resource_calendar_id": pt_cal.id,
            "date_version": date(2026, 1, 1),
            "contract_date_start": date(2026, 1, 1),
            "birthday": date(2005, 5, 20),
            "wage": wage,
        }
        if self.engine == "oca":
            emp_vals["struct_id"] = self.structure.id
        else:
            emp_vals["structure_type_id"] = self.structure.type_id.id
        employee = self.env["hr.employee"].with_company(
            self.company).create(emp_vals)
        employee.version_id.write({
            "l10n_cz_tax_declaration": True,
            "l10n_cz_social_discount_category": "over55",
        })
        slip = self.env["hr.payslip"].with_company(self.company).create({
            "name": "Payslip PT",
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

    def test_discount_annex(self):
        """A §7a discount line -> slevaZamestnavatele + slevaZamestnanci annex,
        pojistneUhrada reduced, and the XML still validates against PVPOJ25.xsd."""
        employee, slip = self._discount_employee_payslip()
        totals = {line.code: line.total for line in slip.line_ids}
        self.assertAlmostEqual(totals.get("SOCIAL_DISCOUNT", 0.0), -1000.0, 2)

        decl = self.env["l10n.cz.pvpoj"].with_company(self.company).create({
            "company_id": self.company.id, "year": "2026", "month": "3"})
        decl.action_generate()
        self.assertEqual(decl.state, "generated")

        import base64
        xml_bytes = base64.b64decode(decl.xml_attachment_id.datas)
        schema = etree.XMLSchema(etree.parse(
            file_path("l10n_cz_hr_payroll_pvpoj/data/PVPOJ25.xsd")))
        root = etree.fromstring(xml_bytes)
        schema.assertValid(root)  # annex must keep the document schema-valid

        ns = {"p": "http://schemas.cssz.cz/POJ/PVPOJ2025"}
        # Aggregate employer discount block.
        self.assertEqual(
            int(root.find(".//p:slevaZamestnavatele/p:pocetZamestnancu", ns).text), 1)
        self.assertEqual(
            int(root.find(".//p:slevaZamestnavatele/p:pojistneSleva", ns).text), 1000)
        self.assertEqual(
            int(root.find(".//p:slevaZamestnavatele/p:uhrnVymerovacichZakladu", ns).text),
            20000)
        # pojistneUhrada = pojistneCelkem - discount.
        celkem = int(root.find(".//p:pojistneCelkem", ns).text)
        uhrada = int(root.find(".//p:pojistneUhrada", ns).text)
        self.assertEqual(uhrada, celkem - 1000)
        # Per-employee annex row.
        zam = root.findall(".//p:slevaZamestnanci/p:zamestnanec", ns)
        self.assertEqual(len(zam), 1)
        self.assertEqual(zam[0].find("p:duvodSlevy", ns).text, "a")  # over55
        self.assertEqual(
            int(zam[0].find("p:vymerovaciZaklad", ns).text), 20000)

    def test_no_discount_omits_annex(self):
        """No eligible employee -> optional discount blocks omitted, still valid."""
        self._employee_payslip()
        decl = self.env["l10n.cz.pvpoj"].with_company(self.company).create({
            "company_id": self.company.id, "year": "2026", "month": "3"})
        decl.action_generate()
        import base64
        xml_bytes = base64.b64decode(decl.xml_attachment_id.datas)
        schema = etree.XMLSchema(etree.parse(
            file_path("l10n_cz_hr_payroll_pvpoj/data/PVPOJ25.xsd")))
        root = etree.fromstring(xml_bytes)
        schema.assertValid(root)
        ns = {"p": "http://schemas.cssz.cz/POJ/PVPOJ2025"}
        self.assertIsNone(root.find(".//p:slevaZamestnavatele", ns))
        self.assertIsNone(root.find(".//p:slevaZamestnanci", ns))
        celkem = int(root.find(".//p:pojistneCelkem", ns).text)
        self.assertEqual(
            int(root.find(".//p:pojistneUhrada", ns).text), celkem)

    def test_submit_locks(self):
        self._employee_payslip()
        decl = self.env["l10n.cz.pvpoj"].with_company(self.company).create({
            "company_id": self.company.id, "year": "2026", "month": "3"})
        decl.action_generate()
        decl.action_submit()
        self.assertEqual(decl.state, "submitted")
        self.assertTrue(decl.submitted_attachment_id)
