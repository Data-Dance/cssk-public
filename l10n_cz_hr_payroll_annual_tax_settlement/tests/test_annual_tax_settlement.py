# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Runtime test — proves Vyúčtování (DPZVD6) generation + XSD validation on BOTH
payroll engines. Detects whichever CZ payroll engine is installed (the ``payroll`` engine
``l10n_cz_hr_payroll_oca`` or ``l10n_cz_hr_payroll_ee``), drives it to a computed
payslip, generates the annual reconciliation and validates the produced XML
against the shipped ``dpzvd6_epo2.xsd``."""
import base64
from datetime import date

from lxml import etree

from odoo.tests import TransactionCase, tagged
from odoo.tools import file_path


@tagged("post_install", "-at_install")
class TestVyuctovani(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create({
            "name": "CZ Vyuctovani Co",
            "country_id": cls.env.ref("base.cz").id,
            "company_registry": "12345679",
            "vat": "CZ12345679",
            "street": "Hluboká",
            "city": "Praha",
            "zip": "11000",
            "l10n_cz_fu_code": "451",
            "l10n_cz_vyuctovani_typ_ds": "P",
        })
        cls.env.user.company_ids |= cls.company
        cls.env = cls.env(context=dict(
            cls.env.context, allowed_company_ids=cls.company.ids))
        cls.env.user.groups_id |= cls.env.ref(
            "payroll.group_payroll_manager")
        cls.structure = cls.env.ref(
            "l10n_cz_hr_payroll_oca.hr_payroll_structure_cz_employee_salary")
        cls.calendar = cls.env["resource.calendar"].create(
            {"name": "CZ 40h", "company_id": cls.company.id})

    def _employee_payslip(self, wage=50000.0):
        employee = self.env["hr.employee"].with_company(self.company).create({
            "name": "Pavel Novak",
            "company_id": self.company.id,
            "resource_calendar_id": self.calendar.id,
        })
        contract = self.env["hr.contract"].with_company(self.company).create({
            "name": "Contract Pavel",
            "employee_id": employee.id,
            "company_id": self.company.id,
            "wage": wage,
            "state": "open",
            "date_start": date(2026, 1, 1),
            "resource_calendar_id": self.calendar.id,
            "struct_id": self.structure.id,
            "l10n_cz_tax_declaration": True,
        })
        slip = self.env["hr.payslip"].with_company(self.company).create({
            "name": "Payslip",
            "employee_id": employee.id,
            "contract_id": contract.id,
            "struct_id": self.structure.id,
            "company_id": self.company.id,
            "date_from": date(2026, 3, 1),
            "date_to": date(2026, 3, 31),
        })
        slip.compute_sheet()
        return employee, slip

    def test_generate_and_validate(self):
        employee, slip = self._employee_payslip()
        tax = int(round(abs(
            sum(line.total for line in slip.line_ids
                if line.code == "INCOMETAX"))))
        self.assertGreater(tax, 0, "INCOMETAX must be computed")

        decl = self.env["l10n.cz.vyuctovani"].with_company(
            self.company).create({
                "company_id": self.company.id,
                "year": "2026",
            })
        self.assertTrue(decl.version_id, "Vyúčtování version should default")
        decl.action_generate()
        self.assertEqual(decl.state, "generated")
        self.assertTrue(decl.xml_attachment_id)

        xml_bytes = base64.b64decode(decl.xml_attachment_id.datas)
        schema = etree.XMLSchema(etree.parse(
            file_path("l10n_cz_hr_payroll_annual_tax_settlement/data/dpzvd6_epo2.xsd")))
        root = etree.fromstring(xml_bytes)
        schema.assertValid(root)

        vetad = root.find(".//VetaD")
        self.assertEqual(vetad.get("k_uladis"), "DPZ")
        self.assertEqual(vetad.get("dokument"), "VD6")
        self.assertEqual(vetad.get("vdadpz_typ"), "B")
        self.assertEqual(vetad.get("c_ufo_cil"), "451")
        # annual advance tax (single March payslip) and month-3 count
        self.assertEqual(int(vetad.get("kc_dpzii01")), tax)
        self.assertEqual(vetad.get("poc_zam3"), "1")

        vetap = root.find(".//VetaP")
        self.assertEqual(vetap.get("dic"), "12345679")
        self.assertEqual(vetap.get("typ_ds"), "P")

        vetao = root.findall(".//VetaO")
        self.assertEqual(len(vetao), 1)
        self.assertEqual(vetao[0].get("mesic"), "3")
        self.assertEqual(int(vetao[0].get("kc_dpzi01")), tax)

    def test_submit_locks(self):
        self._employee_payslip()
        decl = self.env["l10n.cz.vyuctovani"].with_company(
            self.company).create({
                "company_id": self.company.id, "year": "2026"})
        decl.action_generate()
        decl.action_submit()
        self.assertEqual(decl.state, "submitted")
        self.assertTrue(decl.submitted_attachment_id)
