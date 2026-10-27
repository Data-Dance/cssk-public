# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Runtime test — proves Vyúčtování (DPZVD6) generation + XSD validation on BOTH
payroll engines. Detects whichever CZ payroll engine is installed (the ``payroll`` engine
``l10n_cz_hr_payroll_oca`` or ``l10n_cz_hr_payroll_ee``), drives it to a computed
payslip, generates the annual reconciliation and validates the produced XML
against the shipped ``dpzvd6_epo2.xsd``."""
import base64
import calendar
from datetime import date

from lxml import etree

from odoo.addons.l10n_cssk_payroll_declaration_base.tests.common import (
    confirm_payslips,
)
from odoo.tests import TransactionCase, tagged
from odoo.tools import file_path


@tagged("post_install", "-at_install")
class TestVyuctovani(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.engine = cls._detect_engine()
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
            "l10n_cz_zuj_code": "554782",
            "l10n_cz_zuj_name": "Praha",
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

    def _employee_payslip(self, wage=50000.0, name="Pavel Novak",
                          version_vals=None, month=3, confirm=True):
        emp_vals = {
            "name": name,
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
        employee.version_id.write(dict(
            {"l10n_cz_tax_declaration": True}, **(version_vals or {})))

        slip = self.env["hr.payslip"].with_company(self.company).create({
            "name": "Payslip",
            "employee_id": employee.id,
            "struct_id": self.structure.id,
            "company_id": self.company.id,
            "date_from": date(2026, month, 1),
            "date_to": date(2026, month, calendar.monthrange(2026, month)[1]),
        })
        if self.engine == "ee":
            slip = slip.with_context(salary_simulation=True)
        slip.compute_sheet()
        if confirm:
            # Declarations report confirmed payroll only.
            confirm_payslips(slip)
        return employee, slip

    @staticmethod
    def _total(slip, *codes):
        return sum(line.total for line in slip.line_ids if line.code in codes)

    def test_generate_and_validate(self):
        employee, slip = self._employee_payslip()
        before_credits = -self._total(slip, "INCOMETAX")
        credits = self._total(slip, "TAXCREDIT", "CHILDBEN")
        self.assertGreater(before_credits, 0, "INCOMETAX must be computed")
        self.assertGreater(credits, 0, "the taxpayer credit must apply")
        # Column 1 is the advance AFTER the monthly credits (pokyny k
        # vyplnění, sloupec 1: "úhrn záloh na daň po měsíčních slevách").
        tax = int(round(before_credits - credits))

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
        self.assertEqual(int(vetao[0].get("kc_dpzi02")), tax)
        self.assertLess(tax, int(round(before_credits)))
        self.assertFalse(vetao[0].get("kc_dpzi05"), "no child bonus here")

    def test_submit_locks(self):
        self._employee_payslip()
        decl = self.env["l10n.cz.vyuctovani"].with_company(
            self.company).create({
                "company_id": self.company.id, "year": "2026"})
        decl.action_generate()
        decl.action_submit()
        self.assertEqual(decl.state, "submitted")
        self.assertTrue(decl.submitted_attachment_id)

    def _generate(self):
        decl = self.env["l10n.cz.vyuctovani"].with_company(
            self.company).create({"company_id": self.company.id,
                                  "year": "2026"})
        decl.action_generate()
        root = etree.fromstring(base64.b64decode(decl.xml_attachment_id.datas))
        etree.XMLSchema(etree.parse(file_path(
            "l10n_cz_hr_payroll_annual_tax_settlement/data/dpzvd6_epo2.xsd"
        ))).assertValid(root)
        return decl, root

    def test_child_bonus_in_column_5_and_row_4(self):
        """A low wage with a child: the benefit wipes the advance out and the
        surplus is paid as a bonus — column 1 is 0, column 5 the bonus, and
        Part II row 4 (kc_dpzii03a) their annual sum."""
        _employee, slip = self._employee_payslip(
            wage=25000.0, version_vals={"l10n_cz_children_t1": 1})
        bonus = int(round(self._total(slip, "CHILDBONUS")))
        self.assertGreater(bonus, 0, "the child bonus must be paid")
        after = -self._total(slip, "INCOMETAX", "TAXCREDIT", "CHILDBEN")
        _decl, root = self._generate()
        vetao = root.find(".//VetaO")
        self.assertEqual(int(vetao.get("kc_dpzi01")), int(round(after)))
        self.assertEqual(int(vetao.get("kc_dpzi05")), bonus)
        vetad = root.find(".//VetaD")
        self.assertEqual(int(vetad.get("kc_dpzii03a")), bonus)
        self.assertEqual(int(vetad.get("kc_dpzii01")), int(round(after)))

    def test_employee_count_is_at_month_end(self):
        """poc_zam: "počet zaměstnanců k poslednímu dni měsíce". Someone who
        left mid-month is not counted for that month."""
        self._employee_payslip()
        leaver, _slip = self._employee_payslip(
            name="Petr Odchazejici", version_vals={})
        leaver.version_id.write({"contract_date_end": date(2026, 3, 15)})
        _decl, root = self._generate()
        self.assertEqual(root.find(".//VetaD").get("poc_zam3"), "1")

    def test_prior_submission_found_across_months(self):
        """An annual filing ignores the month field; a second record prepared
        in another month still finds the submitted one to amend."""
        self._employee_payslip()
        first = self.env["l10n.cz.vyuctovani"].with_company(
            self.company).create({"company_id": self.company.id,
                                  "year": "2026", "month": "3"})
        first.action_generate()
        first.action_submit()
        later = self.env["l10n.cz.vyuctovani"].with_company(
            self.company).create({"company_id": self.company.id,
                                  "year": "2026", "month": "6"})
        self.assertEqual(later._prior_submitted(), first)
        self.assertEqual(str(later.date_from), "2026-01-01")
        self.assertEqual(str(later.date_to), "2026-12-31")

    def test_draft_payslip_is_not_reported(self):
        """A draft payslip is a calculation, not payroll that was run."""
        self._employee_payslip()
        self._employee_payslip(name="Jana Navrhova", month=4, confirm=False)
        _decl, root = self._generate()
        months = [o.get("mesic") for o in root.findall(".//VetaO")]
        self.assertEqual(months, ["3"])

    def test_attachment_1_counts_employees_on_1_december_per_place(self):
        """Příloha č. 1 (§ 38j odst. 1 ZDP, VetaB): employees on the payroll
        on 1 December, per municipality (ZÚJ) of their place of work. One at
        the seat, one at a branch work address, one who left in June."""
        self._employee_payslip(name="Pavel Novak")
        branch = self.env["res.partner"].create({
            "name": "Pobočka Brno", "city": "Brno",
            "country_id": self.env.ref("base.cz").id,
            "l10n_cz_zuj_code": "582786", "l10n_cz_zuj_name": "Brno"})
        self._employee_payslip(
            name="Eva Brnenska", version_vals={"address_id": branch.id})
        leaver, _slip = self._employee_payslip(name="Petr Odesel")
        leaver.version_id.write({"contract_date_end": date(2026, 6, 30)})
        _decl, root = self._generate()
        rows = {b.get("c_obce_zuj"): b for b in root.findall(".//VetaB")}
        self.assertEqual(sorted(rows), ["554782", "582786"])
        self.assertEqual(rows["554782"].get("poc_zam"), "1")
        self.assertEqual(rows["582786"].get("poc_zam"), "1")
        self.assertEqual(rows["582786"].get("naz_obce_zuj"), "Brno")

    def test_attachment_1_needs_a_municipality_code(self):
        from odoo.exceptions import UserError
        self._employee_payslip()
        self.company.l10n_cz_zuj_code = False
        decl = self.env["l10n.cz.vyuctovani"].with_company(
            self.company).create({"company_id": self.company.id,
                                  "year": "2026"})
        with self.assertRaisesRegex(UserError, "ZÚJ"):
            decl.action_generate()

    def test_company_form_shows_the_filing_identifiers(self):
        """The preflight sends the user to the company form for the FÚ code;
        it has to be there."""
        arch = self.env["res.company"].get_views(
            [(False, "form")])["views"]["form"]["arch"]
        for field in ("l10n_cz_fu_code", "l10n_cz_vyuctovani_typ_ds",
                      "l10n_cz_zuj_code", "l10n_cz_ossz_vs"):
            self.assertIn('name="%s"' % field, arch)
