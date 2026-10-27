# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Runtime test — proves PVPOJ generation + XSD validation on BOTH payroll
engines. The test detects whichever CZ payroll engine is installed (the ``payroll`` engine
``l10n_cz_hr_payroll_oca`` or the ``l10n_cz_hr_payroll_ee``) and drives it
to a computed payslip, then generates the PVPOJ declaration and validates the
produced XML against the shipped ``PVPOJ25.xsd``."""
from datetime import date

from lxml import etree

from odoo.addons.l10n_cssk_payroll_declaration_base.tests.common import (
    confirm_payslips,
)
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

    def _confirm(self, slip):
        """Declarations report confirmed payroll only (OCA ``done``,
        Enterprise ``validated``); a computed draft is not enough."""
        confirm_payslips(slip)

    def _employee_payslip(self, wage=50000.0, year=2025, end=None,
                          name="Pavel Novak", date_from=None, date_to=None,
                          confirm=True):
        emp_vals = {
            "name": name,
            "company_id": self.company.id,
            "resource_calendar_id": self.calendar.id,
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

        slip = self.env["hr.payslip"].with_company(self.company).create({
            "name": "Payslip",
            "employee_id": employee.id,
            "struct_id": self.structure.id,
            "company_id": self.company.id,
            "date_from": date_from or date(year, 3, 1),
            "date_to": date_to or date(year, 3, 31),
        })
        if self.engine == "ee":
            slip = slip.with_context(salary_simulation=True)
        slip.compute_sheet()
        if confirm:
            self._confirm(slip)
        return employee, slip

    def test_generate_and_validate(self):
        employee, slip = self._employee_payslip()
        totals = {line.code: line.total for line in slip.line_ids}
        self.assertAlmostEqual(totals.get("SOCIALEETOT", 0.0), -3550.0, 2)
        self.assertAlmostEqual(totals.get("SOCIALERTOT", 0.0), 12400.0, 2)

        decl = self.env["l10n.cz.pvpoj"].with_company(self.company).create({
            "company_id": self.company.id,
            "year": "2025",
            "month": "3",
        })
        decl.action_generate()
        self.assertEqual(decl.version_id, self.env.ref(
            "l10n_cz_hr_payroll_pvpoj.pvpoj_version_2025"))
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
            "date_version": date(2025, 1, 1),
            "contract_date_start": date(2025, 1, 1),
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
            "date_from": date(2025, 3, 1),
            "date_to": date(2025, 3, 31),
        })
        if self.engine == "ee":
            slip = slip.with_context(salary_simulation=True)
        slip.compute_sheet()
        self._confirm(slip)
        return employee, slip

    def test_discount_annex(self):
        """A §7a discount line -> slevaZamestnavatele + slevaZamestnanci annex,
        pojistneUhrada reduced, and the XML still validates against PVPOJ25.xsd."""
        employee, slip = self._discount_employee_payslip()
        totals = {line.code: line.total for line in slip.line_ids}
        self.assertAlmostEqual(totals.get("SOCIAL_DISCOUNT", 0.0), -1000.0, 2)

        decl = self.env["l10n.cz.pvpoj"].with_company(self.company).create({
            "company_id": self.company.id, "year": "2025", "month": "3"})
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
            "company_id": self.company.id, "year": "2025", "month": "3"})
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
            "company_id": self.company.id, "year": "2025", "month": "3"})
        decl.action_generate()
        decl.action_submit()
        self.assertEqual(decl.state, "submitted")
        self.assertTrue(decl.submitted_attachment_id)

    def test_2026_refused_while_still_an_employer(self):
        """ČSSZ: "PVPOJ se zasílali zaměstnavatelé naposledy za prosinec
        2025". An employer that still employs on 1 April 2026 reports
        January-March 2026 through JMHZ."""
        from odoo.exceptions import UserError
        self._employee_payslip(year=2026)
        decl = self.env["l10n.cz.pvpoj"].with_company(self.company).create({
            "company_id": self.company.id, "year": "2026", "month": "3"})
        with self.assertRaisesRegex(UserError, "JMHZ"):
            decl.action_generate()
        self.assertFalse(decl.xml_attachment_id)

    def test_2026_allowed_for_an_employer_that_ceased(self):
        """Zákon č. 360/2025 Sb., čl. IX bod 3: an employer that is no longer
        one on 1 April 2026 still files PVPOJ for January-March 2026."""
        self._employee_payslip(year=2026, end=date(2026, 3, 31))
        decl = self.env["l10n.cz.pvpoj"].with_company(self.company).create({
            "company_id": self.company.id, "year": "2026", "month": "3"})
        decl.action_generate()
        self.assertEqual(decl.state, "generated")

    def test_april_2026_onwards_is_refused(self):
        from odoo.exceptions import UserError
        self._employee_payslip(year=2026, end=date(2026, 3, 31))
        decl = self.env["l10n.cz.pvpoj"].with_company(self.company).create({
            "company_id": self.company.id, "year": "2026", "month": "4"})
        with self.assertRaisesRegex(UserError, "discontinued"):
            decl.action_generate()

    def _generate_root(self, year="2025", month="3"):
        import base64
        decl = self.env["l10n.cz.pvpoj"].with_company(self.company).create({
            "company_id": self.company.id, "year": year, "month": month})
        decl.action_generate()
        root = etree.fromstring(base64.b64decode(decl.xml_attachment_id.datas))
        return decl, root

    def test_draft_payslip_is_not_reported(self):
        """Only confirmed payroll is declared: a computed draft payslip is a
        calculation that may still change, so it must not reach the ČSSZ."""
        from odoo.exceptions import UserError
        self._employee_payslip(confirm=False)
        decl = self.env["l10n.cz.pvpoj"].with_company(self.company).create({
            "company_id": self.company.id, "year": "2025", "month": "3"})
        with self.assertRaisesRegex(UserError, "No payslips found"):
            decl.action_generate()

    def test_payslip_across_a_month_boundary_is_reported(self):
        """A payslip for 15 February - 14 March belongs to March (its end
        date). Requiring the whole payslip inside March dropped it."""
        self._employee_payslip(
            date_from=date(2025, 2, 15), date_to=date(2025, 3, 14))
        decl, root = self._generate_root()
        self.assertEqual(decl.lines_count, 1)

    def test_premiums_are_rounded_up_on_the_company_total(self):
        """§ 7 odst. 1 písm. a) and odst. 3 zák. 589/1992 Sb.: the employer
        pays 24.8 % of the TOTAL of its employees' bases, rounded UP once;
        each employee's 7.1 % is rounded up on its own. Two wages of
        30 001 Kč: employer 60 002 x 24.8 % = 14 880.496 -> 14 881 (the old
        rounding of the summed payslip premiums gave 14 880); employee
        2 130.071 -> 2 131 each, 4 262 in total (old: 4 260)."""
        self._employee_payslip(wage=30001.0, name="Pavel Novak")
        self._employee_payslip(wage=30001.0, name="Petr Svoboda")
        decl, root = self._generate_root()
        ns = {"p": "http://schemas.cssz.cz/POJ/PVPOJ2025"}
        self.assertEqual(
            int(root.find(".//p:zakladZamestnavateleA", ns).text), 60002)
        self.assertEqual(
            int(root.find(".//p:pojistneZamestnavateleA", ns).text), 14881)
        self.assertEqual(
            int(root.find(".//p:pojistneZamestnavateleCelkem", ns).text),
            14881)
        self.assertEqual(
            int(root.find(".//p:pojistneZamestnance", ns).text), 4262)
        self.assertEqual(
            int(root.find(".//p:pojistneCelkem", ns).text), 14881 + 4262)
