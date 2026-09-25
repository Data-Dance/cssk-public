# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Runtime test — proves ONZ generation + XSD validation. ONZ is employee-
lifecycle driven (no payslip), so it is exercised on a single engine/harness.
Builds an employee, registers a nástup and a skončení event, and validates the
produced XML against the shipped ``ONZ2022_20230616.xsd`` (+ ``baseTypes2.xsd``)."""
import base64
from datetime import date

from lxml import etree

from odoo.tests import TransactionCase, tagged
from odoo.tools import file_path

NS = {"o": "http://schemas.cssz.cz/ONZ2022"}


@tagged("post_install", "-at_install")
class TestOnz(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create({
            "name": "CZ ONZ Co",
            "country_id": cls.env.ref("base.cz").id,
            "company_registry": "12345678",
            "l10n_cz_ossz_vs": "9992001215",
            "l10n_cz_ossz_code": "222",
        })
        cls.env.user.company_ids |= cls.company
        cls.env = cls.env(context=dict(
            cls.env.context, allowed_company_ids=cls.company.ids))
        cls.employee = cls.env["hr.employee"].with_company(cls.company).create({
            "name": "Jan Pokusny",
            "company_id": cls.company.id,
            "identification_id": "8001011117",  # rodné číslo
            "birthday": date(1980, 1, 1),
            "place_of_birth": "Praha",
            "private_street": "Dlouhá 1",
            "private_city": "Praha",
            "private_zip": "11000",
            "private_country_id": cls.env.ref("base.cz").id,
            "date_version": date(2022, 5, 4),
            "contract_date_start": date(2022, 5, 4),
        })

    def _validate(self, decl):
        xml_bytes = base64.b64decode(decl.xml_attachment_id.datas)
        schema = etree.XMLSchema(etree.parse(
            file_path("l10n_cz_hr_payroll_onz/data/ONZ2022_20230616.xsd")))
        root = etree.fromstring(xml_bytes)
        schema.assertValid(root)
        return root

    def test_nastup(self):
        decl = self.env["l10n.cz.onz"].with_company(self.company).create({
            "company_id": self.company.id,
            "event_type": "nastup",
            "employee_ids": [(6, 0, self.employee.ids)],
        })
        self.assertTrue(decl.version_id, "ONZ version should default")
        decl.action_generate()
        self.assertEqual(decl.state, "generated")
        root = self._validate(decl)

        emps = root.findall(".//o:employee", NS)
        self.assertEqual(len(emps), 1)
        self.assertEqual(emps[0].get("act"), "1")  # nástup
        self.assertEqual(emps[0].get("dep"), "222")
        client = emps[0].find("o:client", NS)
        self.assertEqual(client.get("bno"), "8001011117")
        job = emps[0].find("o:job", NS)
        self.assertEqual(job.get("fro"), "2022-05-04")
        self.assertFalse(job.get("to"))  # no end date on nástup
        comp = emps[0].find("o:comp", NS)
        self.assertEqual(comp.get("vs"), "9992001215")

    def test_skonceni(self):
        self.employee.version_id.write({"contract_date_end": date(2026, 6, 30)})
        decl = self.env["l10n.cz.onz"].with_company(self.company).create({
            "company_id": self.company.id,
            "event_type": "skonceni",
            "employee_ids": [(6, 0, self.employee.ids)],
        })
        decl.action_generate()
        root = self._validate(decl)
        emp = root.find(".//o:employee", NS)
        self.assertEqual(emp.get("act"), "2")  # skončení
        job = emp.find("o:job", NS)
        self.assertEqual(job.get("to"), "2026-06-30")

    def test_no_employee_raises(self):
        from odoo.exceptions import UserError
        decl = self.env["l10n.cz.onz"].with_company(self.company).create({
            "company_id": self.company.id, "event_type": "nastup"})
        with self.assertRaises(UserError):
            decl.action_generate()
