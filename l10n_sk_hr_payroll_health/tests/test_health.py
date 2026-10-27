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
from odoo.addons.l10n_cssk_payroll_declaration_base.tests.common import (
    confirm_payslips,
)
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
        confirm_payslips(slip)
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

    # ------------------------------------------------------------------
    # One insurer per dávka (2026-10-27)
    # ------------------------------------------------------------------
    def _insured(self, name, rc, insurer):
        employee, slip = self._employee_payslip()
        employee.write({"name": name, "identification_id": rc,
                        "l10n_sk_health_insurer_code": insurer})
        return employee

    def _rows(self, insurer):
        decl = self.env["l10n.sk.health"].with_company(self.company).create({
            "company_id": self.company.id, "year": "2026", "month": "3",
            "insurer_code": insurer})
        decl.action_generate()
        root = etree.fromstring(base64.b64decode(decl.xml_attachment_id.datas))
        return decl, [p.findtext("IdentificationNumberOfInsured")
                      for p in root.findall("PersonData")]

    def test_each_insurer_gets_only_its_insurees(self):
        """Every employee went into every insurer's dávka 514: the insurer
        was a property of the record, never of the employee."""
        self._insured("Dovera Poistenec", "8501011234", "24")
        self._insured("Vszp Poistenec", "9002022345", "25")
        decl24, rows24 = self._rows("24")
        decl25, rows25 = self._rows("25")
        self.assertEqual(rows24, ["8501011234"])
        self.assertEqual(rows25, ["9002022345"])
        self.assertEqual(decl24.lines_count, 1)
        self.assertEqual(decl25.lines_count, 1)

    def test_employee_without_insurer_uses_the_company_default(self):
        self._insured("Bez Poistovne", "8501011234", False)
        _decl, rows = self._rows("24")  # the company default
        self.assertEqual(rows, ["8501011234"])
        decl = self.env["l10n.sk.health"].with_company(self.company).create({
            "company_id": self.company.id, "year": "2026", "month": "3",
            "insurer_code": "25"})
        with self.assertRaises(UserError):
            decl.action_generate()  # nobody is insured with VšZP

    def test_company_fields_are_on_the_forms(self):
        """The payer number is required by the preflight but was on no form;
        the employee's insurer has to be visible to be set."""
        arch = self.env["l10n.sk.health"].get_views(
            [(False, "form")])["views"]["form"]["arch"]
        self.assertIn('name="payer_number"', arch)
        emp_arch = self.env["hr.employee"].get_views(
            [(False, "form")])["views"]["form"]["arch"]
        self.assertIn('name="l10n_sk_health_insurer_code"', emp_arch)
        decl = self.env["l10n.sk.health"].with_company(self.company).create({
            "company_id": self.company.id, "year": "2026", "month": "3"})
        decl.payer_number = "1122334455"
        self.assertEqual(self.company.l10n_sk_health_payer_number,
                         "1122334455")

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
