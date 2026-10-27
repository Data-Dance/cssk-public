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

from odoo.addons.l10n_cssk_payroll_declaration_base.tests.common import (
    confirm_payslips,
)
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
            "company_registry": "12345679",
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
        # The structure decides the employment form and a contract may not
        # disagree with it, so a dohoda sits on the dohoda's own structure
        # (OCA) or structure type (Enterprise) rather than having its
        # agreement type set underneath the employment one.
        structure = self.structure
        if self.engine == "oca":
            if agreement != "none":
                structure = self.env.ref(
                    "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_%s"
                    % agreement)
            emp_vals["struct_id"] = structure.id
        else:
            structure_type = self.structure.type_id
            if agreement != "none":
                structure_type = self.env.ref(
                    "l10n_sk_hr_payroll_ee.structure_type_%s_sk" % agreement)
                structure = structure_type.default_struct_id
            emp_vals["structure_type_id"] = structure_type.id
        employee = self.env["hr.employee"].with_company(
            self.company).create(emp_vals)
        self.assertEqual(employee.version_id.l10n_sk_agreement_type, agreement)

        slip = self.env["hr.payslip"].with_company(self.company).create({
            "name": "Payslip",
            "employee_id": employee.id,
            "struct_id": structure.id,
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
        employee, slip = self._dohodar_payslip()
        totals = {line.code: line.total for line in slip.line_ids}
        social_er = abs(round(totals.get("SOCIALEMPLOYERTOTAL", 0.0), 2))
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

        # spoluPoistne is the sum of the social fund rows the form reports.
        # It used to be asserted against SOCIALEMPLOYERTOTAL +
        # SOCIALEMPLOYEETOTAL, which on the OCA engine include health
        # insurance — the test ratified the over-statement.
        funds = (
            "SICKEMPLOYER", "SICK", "PENSIONEMPLOYER", "PENSION",
            "DISABILITYEMPLOYER", "DISABILITY", "UNEMPLOYMENTEMPLOYER",
            "UNEMPLOYMENT", "ACCIDENT", "GUARANTEEEMPLOYER",
            "RESERVEFUNDEMPLOYER",
        )
        expected = round(sum(abs(round(totals.get(c, 0.0), 2)) for c in funds), 2)
        self.assertGreater(expected, 0.0)
        spolu = float(root.find(".//v:poistne/v:spoluPoistne", NS).text)
        self.assertAlmostEqual(spolu, expected, 2)

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

    def test_sp_vs_is_editable_on_the_form(self):
        """The variable symbol is required by the preflight but was on no
        form at all; it is edited on the declaration form now."""
        arch = self.env["l10n.sk.vpp"].get_views(
            [(False, "form")])["views"]["form"]["arch"]
        self.assertIn('name="sp_vs"', arch)
        decl = self.env["l10n.sk.vpp"].with_company(self.company).create({
            "company_id": self.company.id, "year": "2026", "month": "3"})
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
