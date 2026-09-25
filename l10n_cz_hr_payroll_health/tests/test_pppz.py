# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Runtime test — proves PPPZ generation + XSD validation on BOTH payroll
engines. Detects whichever CZ payroll engine is installed (the ``payroll`` engine
``l10n_cz_hr_payroll_oca`` or ``l10n_cz_hr_payroll_ee``), drives it to a computed
payslip, generates the per-insurer PPPZ health overview and validates the
produced XML against the shipped ``PPPZ_2025_v8.xsd``."""
import base64
from datetime import date

from lxml import etree

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged
from odoo.tools import file_path

NS = {"p": "http://xmlns.vzp.cz/PrehledPlatbyZamestnavatele/v1"}


@tagged("post_install", "-at_install")
class TestPppz(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.engine = cls._detect_engine()
        cls.company = cls.env["res.company"].create({
            "name": "CZ Health Co",
            "country_id": cls.env.ref("base.cz").id,
            "company_registry": "12345678",
            "street": "Hluboká 1",
            "city": "Praha",
            "zip": "11000",
            "l10n_cz_health_insurer_code": "111",
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

    def _employee_payslip(self, name, wage, insurer=False):
        emp_vals = {
            "name": name,
            "company_id": self.company.id,
            "resource_calendar_id": self.calendar.id,
            "date_version": date(2026, 1, 1),
            "contract_date_start": date(2026, 1, 1),
            "wage": wage,
        }
        if insurer:
            emp_vals["l10n_cz_health_insurer_code"] = insurer
        if self.engine == "oca":
            emp_vals["struct_id"] = self.structure.id
        else:
            emp_vals["structure_type_id"] = self.structure.type_id.id
        employee = self.env["hr.employee"].with_company(
            self.company).create(emp_vals)
        employee.version_id.write({"l10n_cz_tax_declaration": True})

        slip = self.env["hr.payslip"].with_company(self.company).create({
            "name": "Payslip %s" % name,
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
        # Employee A -> company default insurer (111); Employee B -> 205, must
        # be excluded from the 111 overview (per-insurer filtering).
        _emp_a, slip_a = self._employee_payslip("Pavel Novak", 50000.0)
        self._employee_payslip("Petra Malá", 30000.0, insurer="205")
        totals = {line.code: line.total for line in slip_a.line_ids}
        self.assertAlmostEqual(totals.get("HEALTHEE", 0.0), -2250.0, 2)
        self.assertAlmostEqual(totals.get("HEALTHER", 0.0), 4500.0, 2)

        decl = self.env["l10n.cz.pppz"].with_company(self.company).create({
            "company_id": self.company.id,
            "insurer_code": "111",
            "year": "2026",
            "month": "3",
        })
        self.assertTrue(decl.version_id, "PPPZ version should default")
        decl.action_generate()
        self.assertEqual(decl.state, "generated")
        self.assertTrue(decl.xml_attachment_id)

        # XSD-validate the produced XML against the shipped schema.
        xml_bytes = base64.b64decode(decl.xml_attachment_id.datas)
        schema = etree.XMLSchema(etree.parse(
            file_path("l10n_cz_hr_payroll_health/data/PPPZ_2025_v8.xsd")))
        root = etree.fromstring(xml_bytes)
        schema.assertValid(root)

        # Key totals: only the 111 employee (A), base = premium / 0.135.
        self.assertEqual(root.find(".//p:kodZdravotniPojistovny", NS).text,
                         "111")
        self.assertEqual(root.find(".//p:pocetZamestnancu", NS).text, "1")
        self.assertEqual(
            root.find(".//p:soucetZakladuPojistneho", NS).text, "50000.00")
        self.assertEqual(root.find(".//p:soucetPojistneho", NS).text, "6750")
        # Envelope constants.
        self.assertEqual(
            root.find(".//p:identifikacniCisloPlatce", NS).text, "1234567800")

    def test_submit_locks(self):
        self._employee_payslip("Pavel Novak", 50000.0)
        decl = self.env["l10n.cz.pppz"].with_company(self.company).create({
            "company_id": self.company.id, "insurer_code": "111",
            "year": "2026", "month": "3"})
        decl.action_generate()
        decl.action_submit()
        self.assertEqual(decl.state, "submitted")
        self.assertTrue(decl.submitted_attachment_id)

    # ------------------------------------------------------------------
    # Corrections (opravný přehled)
    # ------------------------------------------------------------------
    def _pppz(self, **vals):
        base = {
            "company_id": self.company.id,
            "insurer_code": "111",
            "year": "2026",
            "month": "3",
        }
        base.update(vals)
        return self.env["l10n.cz.pppz"].with_company(self.company).create(base)

    def test_regular_overview_emits_radny(self):
        self._employee_payslip("Radny Radek", 50000.0)
        decl = self._pppz()
        self.assertEqual(decl.correction_type, "regular")
        decl.action_generate()
        xml = base64.b64decode(decl.xml_attachment_id.datas).decode("utf-8")
        self.assertIn("<typPrehledu>radny</typPrehledu>", xml)

    def test_corrective_overview_emits_opravny(self):
        """The concept is the shared correction_type; the wire spelling stays
        Czech."""
        self._employee_payslip("Opravny Ondrej", 50000.0)
        first = self._pppz()
        first.action_generate()
        first.action_submit()

        fix = self._pppz(correction_type="corrective")
        self.assertTrue(fix.is_correction)
        fix.action_generate()
        xml = base64.b64decode(fix.xml_attachment_id.datas).decode("utf-8")
        self.assertIn("<typPrehledu>opravny</typPrehledu>", xml)

    def test_correction_needs_something_to_correct(self):
        """Shared guard: an opravný for a period never filed is refused."""
        self._employee_payslip("Nikdo Nenapsal", 50000.0)
        fix = self._pppz(correction_type="corrective")
        with self.assertRaises(UserError):
            fix.action_generate()
