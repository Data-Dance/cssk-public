# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Runtime test — proves MVP generation + XSD validation on BOTH payroll
engines. Detects whichever SK payroll engine is installed (the ``payroll`` engine
``l10n_sk_hr_payroll_oca`` or the ``l10n_sk_hr_payroll``), drives it to a
computed payslip, generates the MVP declaration and validates the produced XML
against the shipped ``MVPP-v2026.xsd``."""
import base64
from datetime import date

from lxml import etree

from odoo.addons.l10n_cssk_payroll_declaration_base.tests.common import (
    confirm_payslips,
)
from odoo.tests import TransactionCase, tagged
from odoo.tools import file_path

NS = {"m": "http://socpoist.sk/xsd/mvpp2026"}


@tagged("post_install", "-at_install")
class TestMvp(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.engine = cls._detect_engine()
        cls.company = cls.env["res.company"].create({
            "name": "SK MVP Co",
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

    def _employee_payslip(self, wage=2000.0):
        emp_vals = {
            "name": "Jozko Mrkvicka",
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
        social_er = abs(round(totals.get("SOCIALEMPLOYERTOTAL", 0.0), 2))
        social_ee = abs(round(totals.get("SOCIALEMPLOYEETOTAL", 0.0), 2))
        self.assertGreater(social_er, 0.0, "employer social must be computed")

        decl = self.env["l10n.sk.mvp"].with_company(self.company).create({
            "company_id": self.company.id,
            "year": "2026",
            "month": "3",
            "payment_date": date(2026, 3, 31),
        })
        self.assertTrue(decl.version_id, "MVP version should default")
        decl.action_generate()
        self.assertEqual(decl.state, "generated")

        xml_bytes = base64.b64decode(decl.xml_attachment_id.datas)
        schema = etree.XMLSchema(etree.parse(
            file_path("l10n_sk_hr_payroll_mvp/data/MVPP-v2026.xsd")))
        root = etree.fromstring(xml_bytes)
        schema.assertValid(root)

        # Aggregate total matches the payslip.
        # spoluPoistne must equal the sum of the fund rows this form reports,
        # and NOTHING else. It used to be asserted against the payslip's
        # SOCIALEMPLOYERTOTAL + SOCIALEMPLOYEETOTAL categories — but those
        # carry the HEALTH premiums as well (HEALTH and HEALTHDOPLATOK sit in
        # SOCIALEMPLOYEE, HEALTHEMPLOYER in SOCIALEMPLOYER), which are owed to
        # the health insurers and reported on dávka 514. Asserting against the
        # categories made this test ratify an over-stated social premium and
        # an internally inconsistent form.
        poistne = root.find(".//m:poistne", NS)
        rows = sum(
            float(el.text)
            for el in poistne.iter()
            if etree.QName(el).localname.endswith(("Zamtel", "Zamnec"))
            and el.text
        )
        spolu = float(root.find(".//m:poistne/m:spoluPoistne", NS).text)
        self.assertAlmostEqual(
            spolu, round(rows, 2), 2,
            "spoluPoistne must be the sum of the fund rows")
        # ...and it must exclude health, i.e. fall short of the payslip's
        # health-contaminated social categories by exactly the health premium.
        health = abs(round(totals.get("HEALTH", 0.0), 2)) + abs(
            round(totals.get("HEALTHEMPLOYER", 0.0), 2))
        self.assertAlmostEqual(
            spolu, round(social_er + social_ee - health, 2), 2,
            "the social premium must exclude health insurance")

        # Per-employee annex present with the employee's rodné číslo.
        annex = root.findall(".//m:poistneZamestnanca", NS)
        self.assertEqual(len(annex), 1)
        self.assertEqual(annex[0].get("rc"), "8501011234")

    def test_missing_rc_raises(self):
        from odoo.exceptions import UserError
        employee, slip = self._employee_payslip()
        employee.identification_id = False
        decl = self.env["l10n.sk.mvp"].with_company(self.company).create({
            "company_id": self.company.id, "year": "2026", "month": "3"})
        with self.assertRaises(UserError):
            decl.action_generate()

    def test_sp_vs_is_editable_on_the_form(self):
        """The variable symbol is required by the preflight but was on no
        form at all; it is edited on the declaration form now."""
        arch = self.env["l10n.sk.mvp"].get_views(
            [(False, "form")])["views"]["form"]["arch"]
        self.assertIn('name="sp_vs"', arch)
        decl = self.env["l10n.sk.mvp"].with_company(self.company).create({
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
