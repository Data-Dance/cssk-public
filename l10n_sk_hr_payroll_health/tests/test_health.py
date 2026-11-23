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

    def _employee_payslip(self, wage=2000.0, agreement="none", pension=False):
        structure = self.structure
        if agreement != "none" and self.engine == "oca":
            structure = self.env.ref(
                "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_" + agreement)
        elif agreement != "none":
            # Enterprise: one structure, a structure type per agreement.
            structure_type = self.env.ref(
                "l10n_sk_hr_payroll_ee.structure_type_%s_sk" % agreement)
        elif self.engine == "ee":
            structure_type = structure.type_id
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
            emp_vals["struct_id"] = structure.id
        else:
            emp_vals["structure_type_id"] = structure_type.id
        employee = self.env["hr.employee"].with_company(
            self.company).create(emp_vals)
        if pension:
            employee.version_id.write({"l10n_sk_pension_type": pension,
                                       "l10n_sk_health_exempt": agreement != "none"})

        slip = self.env["hr.payslip"].with_company(self.company).create({
            "name": "Payslip",
            "employee_id": employee.id,
            "struct_id": structure.id,
            "company_id": self.company.id,
            "date_from": date(2026, 3, 1),
            "date_to": date(2026, 3, 31),
        })
        slip.compute_sheet()
        confirm_payslips(slip)
        return employee, slip

    def test_old_age_agreement_is_not_health_employment(self):
        for agreement in ("dopc", "dovp"):
            with self.subTest(agreement=agreement):
                _, slip = self._employee_payslip(200, agreement, "old_age")
                declaration = self.env["l10n.sk.health"].with_company(self.company).create({
                    "company_id": self.company.id, "year": "2026", "month": "3"})
                self.assertNotIn(slip, declaration._get_period_payslips())

    def test_old_age_employment_stays_in_health_report(self):
        _, slip = self._employee_payslip(2000, "none", "old_age")
        declaration = self.env["l10n.sk.health"].with_company(self.company).create({
            "company_id": self.company.id, "year": "2026", "month": "3"})
        self.assertIn(slip, declaration._get_period_payslips())

    def test_all_statutory_pension_agreements_are_excluded(self):
        for pension in ("old_age", "early_old_age", "disability_over_70",
                        "disability", "disability_at_age", "service_at_age",
                        "disability_service"):
            for agreement in ("dopc", "dovp"):
                with self.subTest(pension=pension, agreement=agreement):
                    _, slip = self._employee_payslip(200, agreement, pension)
                    declaration = self.env["l10n.sk.health"].with_company(self.company).create({
                        "company_id": self.company.id, "year": "2026", "month": "3"})
                    self.assertNotIn(slip, declaration._get_period_payslips())
                    declaration._preflight()

    def test_health_switch_must_match_statutory_pension_fact(self):
        for pension, exempt in (("disability", False), ("old_age", False)):
            with self.subTest(pension=pension, exempt=exempt):
                _, slip = self._employee_payslip(200, "dopc", pension)
                self._version(slip).l10n_sk_health_exempt = exempt
                declaration = self.env["l10n.sk.health"].with_company(self.company).create({
                    "company_id": self.company.id, "year": "2026", "month": "3"})
                with self.assertRaises(UserError):
                    declaration.action_generate()

    def test_foreign_insured_agreement_without_pension_is_excluded(self):
        for agreement in ("dopc", "dovp"):
            _, slip = self._employee_payslip(200, agreement)
            self._version(slip).l10n_sk_health_exempt = True
            slip.state = "draft"
            slip.compute_sheet()
            confirm_payslips(slip)
            declaration = self.env["l10n.sk.health"].with_company(self.company).create({
                "company_id": self.company.id, "year": "2026", "month": "3"})
            declaration._preflight()
            self.assertNotIn(slip, declaration._get_period_payslips())
            self.assertEqual(self._line(slip, "HEALTH"), 0)
            self.assertEqual(self._line(slip, "HEALTHEMPLOYER"), 0)

    def test_mismatch_at_another_insurer_does_not_block_this_insurer(self):
        _, broken = self._employee_payslip(200, "dopc", "disability")
        broken.employee_id.l10n_sk_health_insurer_code = "25"
        self._version(broken).l10n_sk_health_exempt = False
        good_employee, good = self._employee_payslip()
        good_employee.l10n_sk_health_insurer_code = "24"
        declaration = self.env["l10n.sk.health"].with_company(self.company).create({
            "company_id": self.company.id, "year": "2026", "month": "3", "insurer_code": "24"})
        declaration._preflight()
        self.assertIn(good, declaration._get_period_payslips())
        self.assertNotIn(broken, declaration._get_period_payslips())
        declaration.insurer_code = "25"
        with self.assertRaises(UserError): declaration._preflight()

    def _version(self, slip):
        return self.env["l10n.sk.health"]._payslip_version(slip)

    def test_later_contract_cannot_add_old_age_agreement_to_health(self):
        employee, slip = self._employee_payslip(200, "dopc", "old_age")
        employee.create_version({"date_version": date(2026, 4, 1),
                                 "l10n_sk_pension_type": False,
                                 "l10n_sk_health_exempt": False})
        self.assertFalse(employee.version_id.l10n_sk_pension_type)
        self.assertEqual(self.env['l10n.sk.health']._payslip_version(slip).l10n_sk_pension_type, 'old_age')
        declaration = self.env["l10n.sk.health"].with_company(self.company).create({
            "company_id": self.company.id, "year": "2026", "month": "3"})
        self.assertNotIn(slip, declaration._get_period_payslips())

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

    # ------------------------------------------------------------------
    # The figures of the statement (vyhláška 159/2018 Z. z. § 1 ods. 3)
    # ------------------------------------------------------------------
    def _short_calendar(self):
        """Five hours a week: the minimum wage stays below the test wages."""
        return self.env["resource.calendar"].create({
            "name": "SK 5h", "company_id": self.company.id,
            "full_time_required_hours": 40.0, "hours_per_day": 1.0,
            "attendance_ids": [(5, 0, 0)] + [(0, 0, {
                "name": "d%d" % day, "dayofweek": str(day), "hour_from": 8.0,
                "hour_to": 9.0, "day_period": "morning"}) for day in range(5)],
        })

    def _figures_payslip(self, rc, wage, agreement="none", leaves=(),
                         inputs=None, **version_vals):
        """A confirmed March 2026 payslip of a new employee on a 5-hour week."""
        calendar = self._short_calendar()
        start = date(2026, 1, 1)
        oca = self.engine == "oca"
        module = "l10n_sk_hr_payroll_oca." if oca else "l10n_sk_hr_payroll_ee."
        values = {"name": "Zamestnanec %s" % rc, "company_id": self.company.id,
                  "resource_calendar_id": calendar.id, "identification_id": rc}
        version = dict(version_vals, l10n_sk_agreement_type=agreement)
        if oca:
            suffix = "employee_salary" if agreement == "none" else agreement
            version.update({
                "contract_date_start": start, "date_version": start,
                "wage": wage, "resource_calendar_id": calendar.id,
                "struct_id": self.env.ref(
                    module + "hr_payroll_structure_sk_" + suffix).id})
        else:
            structure_type = (
                self.structure.type_id if agreement == "none" else
                self.env.ref(module + "structure_type_%s_sk" % agreement))
            values.update({"date_version": start, "contract_date_start": start,
                           "wage": wage, "structure_type_id": structure_type.id})
        employee = self.env["hr.employee"].with_company(
            self.company).create(values)
        employee.version_id.write(version)
        self.env.user.group_ids |= self.env.ref(
            "hr_holidays.group_hr_holidays_manager")
        for leave_type, first, last, *extra in leaves:
            if isinstance(leave_type, str):
                leave_type = self.env.ref(module + leave_type)
            self.env["hr.leave"].with_company(self.company).create(dict({
                "name": leave_type.name, "employee_id": employee.id,
                "holiday_status_id": leave_type.id,
                "request_date_from": first, "request_date_to": last,
            }, **(extra[0] if extra else {}))).action_approve()
        slip_vals = {"name": "Payslip %s" % rc, "employee_id": employee.id,
                     "company_id": self.company.id,
                     "date_from": date(2026, 3, 1), "date_to": date(2026, 3, 31)}
        Payslip = self.env["hr.payslip"].with_company(self.company)
        if oca:
            slip_vals.update({"contract_id": employee.version_id.id,
                              "struct_id": employee.version_id.struct_id.id})
            slip = Payslip.create(slip_vals)
            slip.worked_days_line_ids = [(0, 0, line) for line in (
                slip.get_worked_day_lines(
                    employee.version_id, slip.date_from, slip.date_to))]
        else:
            slip_vals.update({"version_id": employee.version_id.id,
                              "struct_id": self.structure.id})
            slip = Payslip.create(slip_vals)
        for code, amount in (inputs or {}).items():
            if oca:
                self.env["hr.payslip.input"].create({
                    "payslip_id": slip.id, "name": code, "code": code,
                    "amount": amount, "contract_id": employee.version_id.id})
            else:
                self.env["hr.payslip.input"].create({
                    "payslip_id": slip.id, "amount": amount,
                    "input_type_id": self.env["hr.payslip.input.type"].search(
                        [("code", "=", code)], limit=1).id})
        slip.compute_sheet()
        confirm_payslips(slip)
        return slip

    def _statement(self):
        declaration = self.env["l10n.sk.health"].with_company(
            self.company).create({
                "company_id": self.company.id, "year": "2026", "month": "3",
                "payment_date": date(2026, 4, 8)})
        declaration.action_generate()
        root = etree.fromstring(
            base64.b64decode(declaration.xml_attachment_id.datas))
        rows = {row.findtext("IdentificationNumberOfInsured"): row
                for row in root.findall("PersonData")}
        return root.find("InsuranceBody"), rows

    def _line(self, slip, *codes):
        return round(sum(abs(line.total) for line in slip.line_ids
                         if line.code in codes), 2)

    def _amounts(self, node, *names):
        return [node.findtext(name) for name in names]

    def test_disabled_employee_is_reported_in_the_disabled_group(self):
        """§ 12 ods. 1 zákona 580/2004 Z. z.: 2.5 % and 5.5 % in 2026."""
        plain = self._figures_payslip("8501011201", 1000.0)
        disabled = self._figures_payslip("8501011202", 1000.0, l10n_sk_ztp=True)
        self.assertEqual(self._line(plain, "HEALTH"), 50.0)
        self.assertEqual(self._line(disabled, "HEALTH"), 25.0)
        self.assertEqual(self._line(disabled, "HEALTHEMPLOYER"), 55.0)
        body, rows = self._statement()
        self.assertEqual(self._amounts(
            body, "TotalNumberOfInsurancePersons",
            "NumberOfInsurancePersons1", "NumberOfInsurancePersons2",
            "NumberOfDays1", "NumberOfDays2"), ["2", "1", "1", "31", "31"])
        self.assertEqual(self._amounts(
            body, "TotalReceipt1", "TotalReceipt2", "BaseOfAssess1",
            "BaseOfAssess2"), ["1000.00", "1000.00", "1000.00", "1000.00"])
        self.assertEqual(self._amounts(
            body, "DepositOfInsurance1", "DepositOfInsurance2",
            "DepositOfInsurance3", "DepositOfInsurance4",
            "TotalDepositOfInsurance"),
            ["110.00", "50.00", "55.00", "25.00", "240.00"])
        self.assertEqual(self._amounts(
            rows["8501011202"], "TariffOfDeposit1", "TariffOfDeposit2",
            "NotAppliedMinimum"), ["5.50", "2.50", "1"])
        self.assertEqual(self._amounts(
            rows["8501011201"], "TariffOfDeposit1", "TariffOfDeposit2",
            "NotAppliedMinimum"), ["11.00", "5.00", "0"])

    def test_minimum_top_up_is_part_of_the_employee_advance(self):
        """§ 16a ods. 4: the top-up raises the employee's advance."""
        slip = self._figures_payslip("8501011203", 200.0)
        self.assertEqual(
            self._line(slip, "HEALTHDOPLATOK", "HEALTH_DOPLATOK"), 13.45)
        body, rows = self._statement()
        self.assertEqual(self._amounts(
            body, "DepositOfInsurance1", "DepositOfInsurance2",
            "DepositOfInsurance3", "DepositOfInsurance4",
            "TotalDepositOfInsurance"),
            ["22.00", "23.45", "0.00", "0.00", "45.45"])
        self.assertEqual(self._amounts(
            rows["8501011203"], "DepositOfEmployer", "DepositOfEmployee",
            "DepositOffEmployeeAdd", "DepositOfTotal"),
            ["22.00", "10.00", "13.45", "45.45"])

    def test_days_are_the_days_the_advance_is_paid_for(self):
        """§ 11 ods. 3 and ods. 7 písm. m): not the days of sickness, of
        maternity or of unpaid leave."""
        sick = self._figures_payslip("8501011205", 300.0, leaves=[
            ("l10n_sk_leave_type_pn", date(2026, 3, 2), date(2026, 3, 11))])
        self._figures_payslip("8501011207", 300.0, leaves=[
            ("l10n_sk_leave_type_neplatene", date(2026, 3, 16),
             date(2026, 3, 20))])
        self._figures_payslip("8501011208", 300.0, leaves=[
            ("l10n_sk_leave_type_materska", date(2026, 3, 23),
             date(2026, 3, 31))])
        absent = self._figures_payslip("8501011212", 300.0, leaves=[
            ("l10n_sk_leave_type_pn", date(2026, 3, 1), date(2026, 3, 31))])
        self._figures_payslip("8501011209", 300.0)
        self.assertEqual(self._line(sick, "GROSS"), 190.91)
        self.assertEqual(self._line(
            absent, "GROSS", "HEALTH", "HEALTHEMPLOYER", "HEALTHDOPLATOK",
            "HEALTH_DOPLATOK"), 0.0)
        body, rows = self._statement()
        self.assertEqual(rows["8501011205"].findtext("NumberOfDays"), "21")
        self.assertEqual(rows["8501011207"].findtext("NumberOfDays"), "26")
        self.assertEqual(rows["8501011208"].findtext("NumberOfDays"), "22")
        self.assertEqual(rows["8501011212"].findtext("NumberOfDays"), "0")
        self.assertEqual(rows["8501011209"].findtext("NumberOfDays"), "31")
        self.assertEqual(body.findtext("NumberOfDays1"), "100")
        # The employee who was sick all month is listed, and is not one of
        # those an advance is paid for.
        self.assertEqual(self._amounts(
            body, "TotalNumberOfInsurancePersons",
            "NumberOfInsurancePersons1"), ["5", "4"])
        self.assertEqual(
            rows["8501011212"].findtext("NotAppliedMinimum"), "1")

    def test_a_day_of_leave_taken_in_part_stays(self):
        """A morning of unpaid leave leaves income for the day (§ 11 ods. 3);
        the two whole days after it do not."""
        module = ("l10n_sk_hr_payroll_oca." if self.engine == "oca"
                  else "l10n_sk_hr_payroll_ee.")
        half_days = self.env.ref(
            module + "l10n_sk_leave_type_neplatene").copy(
                {"name": "Unpaid, half days", "request_unit": "half_day"})
        self._figures_payslip("8501011213", 300.0, leaves=[
            (half_days, date(2026, 3, 17), date(2026, 3, 17),
             {"request_date_from_period": "am",
              "request_date_to_period": "am"}),
            (half_days, date(2026, 3, 18), date(2026, 3, 19),
             {"request_date_from_period": "am",
              "request_date_to_period": "pm"})])
        _body, rows = self._statement()
        self.assertEqual(rows["8501011213"].findtext("NumberOfDays"), "29")

    def test_sick_days_typed_on_the_payslip_reduce_the_days(self):
        """The payslip takes the sick days from PN_DAYS when it is given."""
        self._figures_payslip("8501011210", 300.0, inputs={"PN_DAYS": 10.0})
        _body, rows = self._statement()
        self.assertEqual(rows["8501011210"].findtext("NumberOfDays"), "21")

    def test_deductible_item_is_reported_with_the_statutory_rate(self):
        """§ 13 ods. 1 and 4, § 16 ods. 16 and 17: 380 - 2 x (400 - 380) =
        340 off the employee's base only; 5 % of 60 is 3.00."""
        slip = self._figures_payslip(
            "8501011204", 400.0, l10n_sk_health_oop_claim=True)
        self.assertEqual(self._line(slip, "HEALTH"), 3.0)
        self.assertEqual(self._line(slip, "HEALTHEMPLOYER"), 44.0)
        body, rows = self._statement()
        self.assertEqual(self._amounts(
            rows["8501011204"], "TotalReceiptOfEmployee",
            "BaseOfAssessOfEmployee", "ReceiptOfEmployee",
            "TotalReceiptOfOther", "OP", "TariffOfDeposit1",
            "TariffOfDeposit2", "DepositOfEmployer", "DepositOfEmployee"),
            ["400.00", "60.00", "400.00", "0.00", "340.00", "11.00", "5.00",
             "44.00", "3.00"])
        self.assertEqual(self._amounts(
            body, "TotalReceipt1", "BaseOfAssess1"), ["400.00", "60.00"])

    def test_month_without_recorded_bases_is_reported_on_gross_and_named(self):
        """A payslip computed before the fund bases were recorded has no
        base after the deductible item to read: the row is reported on its
        gross and the statement names the payslip."""
        slip = self._figures_payslip(
            "8501011214", 400.0, l10n_sk_health_oop_claim=True)
        if not callable(getattr(slip, "_cssk_recorded_fund_bases", None)):
            self.skipTest("this payroll engine has no fund records to read")
        slip._l10n_sk_store_fund_evidence(False)
        declaration = self.env["l10n.sk.health"].with_company(
            self.company).create({
                "company_id": self.company.id, "year": "2026", "month": "3"})
        declaration.action_generate()
        self.assertIn(slip.display_name, declaration.fund_bases_warning)
        row = etree.fromstring(base64.b64decode(
            declaration.xml_attachment_id.datas)).find("PersonData")
        self.assertEqual(self._amounts(
            row, "TotalReceiptOfEmployee", "BaseOfAssessOfEmployee", "OP",
            "DepositOfEmployee"), ["400.00", "400.00", "0.00", "3.00"])

    def test_agreement_income_is_other_income(self):
        """§ 13a ods. 1: the income for the deductible item is that of an
        employment relationship, not of an agreement."""
        self._figures_payslip("8501011206", 300.0, agreement="dovp")
        self._figures_payslip("8501011211", 1000.0)
        _body, rows = self._statement()
        self.assertEqual(self._amounts(
            rows["8501011206"], "TotalReceiptOfEmployee", "ReceiptOfEmployee",
            "TotalReceiptOfOther", "OP", "BaseOfAssessOfEmployee"),
            ["300.00", "0.00", "300.00", "0.00", "300.00"])
        self.assertEqual(self._amounts(
            rows["8501011211"], "TotalReceiptOfEmployee", "ReceiptOfEmployee",
            "TotalReceiptOfOther"), ["1000.00", "1000.00", "0.00"])


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
