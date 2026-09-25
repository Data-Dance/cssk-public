# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Runtime test — proves HOZ generation + XSD validation. HOZ is employee-
lifecycle driven (no payslip), so it is exercised on a single engine/harness.
Builds an employee, notifies an enrol (P) and a terminate (O) event, and
validates the produced XML against the shipped ``HOZ_2025_v8.xsd``."""
import base64
from datetime import date

from lxml import etree

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged
from odoo.tools import file_path

NS = {"h": "http://xmlns.vzp.cz/hromadneOznameniZamestnavatele/v1"}


@tagged("post_install", "-at_install")
class TestHoz(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create({
            "name": "CZ HOZ Co",
            "country_id": cls.env.ref("base.cz").id,
            "company_registry": "12345678",
            "street": "Dlouhá 5",
            "city": "Praha",
            "zip": "11000",
            "l10n_cz_health_insurer_code": "111",
        })
        cls.env.user.company_ids |= cls.company
        cls.env = cls.env(context=dict(
            cls.env.context, allowed_company_ids=cls.company.ids))
        cls.employee = cls.env["hr.employee"].with_company(cls.company).create({
            "name": "Jan Pokusny",
            "company_id": cls.company.id,
            "identification_id": "8001011117",  # rodné číslo
            "private_street": "Krátká 3",
            "private_city": "Brno",
            "private_zip": "60200",
            "private_country_id": cls.env.ref("base.cz").id,
            "date_version": date(2026, 5, 4),
            "contract_date_start": date(2026, 5, 4),
        })

    def _validate(self, decl):
        xml_bytes = base64.b64decode(decl.xml_attachment_id.datas)
        schema = etree.XMLSchema(etree.parse(
            file_path("l10n_cz_hr_payroll_health/data/HOZ_2025_v8.xsd")))
        root = etree.fromstring(xml_bytes)
        schema.assertValid(root)
        return root

    def test_enroll(self):
        decl = self.env["l10n.cz.hoz"].with_company(self.company).create({
            "company_id": self.company.id,
            "insurer_code": "111",
            "event_type": "enroll",
            "employee_ids": [(6, 0, self.employee.ids)],
        })
        self.assertTrue(decl.version_id, "HOZ version should default")
        decl.action_generate()
        self.assertEqual(decl.state, "generated")
        root = self._validate(decl)

        self.assertEqual(
            root.find(".//h:kodZdravotniPojistovny", NS).text, "111")
        changes = root.findall(".//h:zmenaZamestance", NS)
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].find("h:kodzmeny", NS).text, "P")
        self.assertEqual(changes[0].find("h:datumZmeny", NS).text, "2026-05-04")
        self.assertEqual(
            changes[0].find("h:cisloPojistence", NS).text, "8001011117")
        self.assertEqual(changes[0].find("h:prijmeni", NS).text, "Pokusny")
        self.assertEqual(changes[0].find("h:jmeno", NS).text, "Jan")

    def test_terminate(self):
        self.employee.version_id.write({"contract_date_end": date(2026, 6, 30)})
        decl = self.env["l10n.cz.hoz"].with_company(self.company).create({
            "company_id": self.company.id,
            "insurer_code": "111",
            "event_type": "terminate",
            "employee_ids": [(6, 0, self.employee.ids)],
        })
        decl.action_generate()
        root = self._validate(decl)
        change = root.find(".//h:zmenaZamestance", NS)
        self.assertEqual(change.find("h:kodzmeny", NS).text, "O")
        self.assertEqual(change.find("h:datumZmeny", NS).text, "2026-06-30")

    def test_no_employee_raises(self):
        decl = self.env["l10n.cz.hoz"].with_company(self.company).create({
            "company_id": self.company.id, "insurer_code": "111",
            "event_type": "enroll"})
        with self.assertRaises(UserError):
            decl.action_generate()
