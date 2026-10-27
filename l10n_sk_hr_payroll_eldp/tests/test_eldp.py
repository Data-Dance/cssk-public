# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Runtime test — proves ELDP annual generation + XSD validation on BOTH
payroll engines. Detects the installed SK payroll engine, drives it to a
computed payslip inside the year, generates the annual ELDP and validates the
produced XML against the shipped ``ELDP-v2015_1.3.xsd``."""
import base64
from datetime import date

from lxml import etree

from odoo.addons.l10n_cssk_payroll_declaration_base.tests.common import (
    confirm_payslips,
)
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
            "company_registry": "12345679",
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

    def _employee_payslip(self, wage=2000.0, start=date(2026, 1, 1)):
        emp_vals = {
            "name": "Jozko Mrkvicka",
            "company_id": self.company.id,
            "resource_calendar_id": self.calendar.id,
            "identification_id": "8501011234",
            "birthday": date(1985, 1, 1),
            "date_version": start,
            "contract_date_start": start,
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
        confirm_payslips(slip)
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

    def test_start_date_is_the_contract_start(self):
        """datVzniku / datOd carry the real start of employment.

        The model read a non-existent ``first_contract_date`` and fell back to
        1 January, so an employee hired on 1 February was reported insured for
        January too.
        """
        self._employee_payslip(start=date(2026, 2, 1))
        decl = self.env["l10n.sk.eldp"].with_company(self.company).create({
            "company_id": self.company.id,
            "year": "2026",
        })
        decl.action_generate()
        root = etree.fromstring(base64.b64decode(decl.xml_attachment_id.datas))
        self.assertEqual(
            root.find(".//e:poistVztah/e:datVzniku", NS).text, "01.02.2026")
        self.assertEqual(
            root.find(".//e:vzZaObdobiePoist", NS).get("datOd"), "01.02.2026")

    def test_multi_word_first_name_is_kept(self):
        """First word = first name, last word = surname dropped the middle
        name; the surname is the last word and the rest the first name."""
        employee, _slip = self._employee_payslip()
        employee.name = "Ján Peter Novák"
        decl = self.env["l10n.sk.eldp"].with_company(self.company).create({
            "company_id": self.company.id, "year": "2026"})
        decl.action_generate()
        root = etree.fromstring(base64.b64decode(decl.xml_attachment_id.datas))
        person = root.find(".//e:eldpZec//e:poistenec", NS)
        self.assertEqual(person.find("e:meno", NS).text, "Ján Peter")
        self.assertEqual(person.find("e:priezvisko", NS).text, "Novák")

    def test_sp_vs_is_editable_on_the_form(self):
        """The variable symbol is required by the preflight but was on no
        form at all; it is edited on the ELDP form now."""
        arch = self.env["l10n.sk.eldp"].get_views(
            [(False, "form")])["views"]["form"]["arch"]
        self.assertIn('name="sp_vs"', arch)
        decl = self.env["l10n.sk.eldp"].with_company(self.company).create({
            "company_id": self.company.id, "year": "2026"})
        decl.sp_vs = "9988776655"
        self.assertEqual(self.company.l10n_sk_sp_vs, "9988776655")


@tagged("post_install", "-at_install")
class TestSchemaPins(TransactionCase):
    """The bundled schemas must match data/SCHEMA_VERSION.

    Not a check that our copies are CURRENT — nothing local can answer that,
    and a schema revised in place by the authority validates exactly as
    before. What this checks is that the bundled bytes are the ones recorded
    in SCHEMA_VERSION, and that no schema sits in data/ unpinned.
    """

    @staticmethod
    def _data_dir():
        import os
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(here, "data")

    def _pins(self):
        import os
        pins = {}
        path = os.path.join(self._data_dir(), "SCHEMA_VERSION")
        with open(path, encoding="utf-8") as fh:
            for raw in fh:
                parts = raw.split()
                if (len(parts) == 3 and parts[0].endswith(".xsd")
                        and "/" not in parts[0]):
                    pins[parts[0]] = (parts[1], int(parts[2]))
        return pins

    def test_bundled_schemas_match_the_pinned_digests(self):
        import hashlib
        import os
        pins = self._pins()
        self.assertTrue(pins, "SCHEMA_VERSION lists no schemas")
        for name, (digest, size) in pins.items():
            path = os.path.join(self._data_dir(), name)
            self.assertTrue(os.path.exists(path),
                            "%s is pinned but missing" % name)
            with open(path, "rb") as fh:
                blob = fh.read()
            self.assertEqual(len(blob), size, "%s size moved" % name)
            self.assertEqual(
                hashlib.md5(blob).hexdigest(), digest,
                "%s does not match its pin — if this is a deliberate "
                "refresh, update data/SCHEMA_VERSION" % name)

    def test_every_bundled_schema_is_pinned(self):
        import os
        on_disk = {f for f in os.listdir(self._data_dir())
                   if f.endswith(".xsd")}
        self.assertEqual(on_disk, set(self._pins()),
                         "unpinned schema(s): %s"
                         % sorted(on_disk - set(self._pins())))
