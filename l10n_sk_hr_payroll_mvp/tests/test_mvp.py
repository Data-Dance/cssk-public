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
from odoo import Command
from odoo.exceptions import UserError

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
        cls.company = cls.env["res.company"].create(
            {
                "name": "SK MVP Co",
                "country_id": cls.env.ref("base.sk").id,
                "company_registry": "12345679",
                "l10n_sk_sp_vs": "1234567890",
            }
        )
        cls.env.user.company_ids |= cls.company
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=cls.company.ids)
        )
        if cls.engine == "oca":
            cls.env.user.group_ids |= cls.env.ref("payroll.group_payroll_manager")
            cls.structure = cls.env.ref(
                "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_employee_salary"
            )
        else:
            cls.env.user.group_ids |= cls.env.ref("hr_payroll.group_hr_payroll_manager")
            cls.structure = cls.env.ref(
                "l10n_sk_hr_payroll.hr_payroll_structure_sk_employee_salary"
            )
        cls.calendar = cls.env["resource.calendar"].create(
            {"name": "SK 40h", "company_id": cls.company.id}
        )

    @classmethod
    def _detect_engine(cls):
        if cls.env.ref(
            "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_employee_salary",
            raise_if_not_found=False,
        ):
            return "oca"
        return "ee"

    def _employee_payslip(
        self,
        wage=2000.0,
        agreement="none",
        regular=None,
        identification="8501011234",
        version_values=None,
        confirm=True,
        worked=False,
        worked_hours=None,
    ):
        emp_vals = {
            "name": "Jozko Mrkvicka",
            "company_id": self.company.id,
            "resource_calendar_id": self.calendar.id,
            "identification_id": identification,  # rodné číslo
            "date_version": date(2026, 1, 1),
            "contract_date_start": date(2026, 1, 1),
            "wage": wage,
        }
        # A dohoda sits on its own structure (OCA) or structure type
        # (Enterprise): the structure decides the employment form.
        structure = self.structure
        if self.engine == "oca":
            if agreement != "none":
                structure = self.env.ref(
                    "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_%s" % agreement
                )
            emp_vals["struct_id"] = structure.id
        else:
            structure_type = self.structure.type_id
            if agreement != "none":
                structure_type = self.env.ref(
                    "l10n_sk_hr_payroll_ee.structure_type_%s_sk" % agreement
                )
                structure = structure_type.default_struct_id
            emp_vals["structure_type_id"] = structure_type.id
        employee = self.env["hr.employee"].with_company(self.company).create(emp_vals)
        self.assertEqual(employee.version_id.l10n_sk_agreement_type, agreement)
        if regular is not None:
            employee.version_id.l10n_sk_income_regular = regular
        if version_values:
            employee.version_id.write(version_values)

        slip = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "name": "Payslip",
                    "employee_id": employee.id,
                    "struct_id": structure.id,
                    "company_id": self.company.id,
                    "date_from": date(2026, 3, 1),
                    "date_to": date(2026, 3, 31),
                }
            )
        )
        if self.engine == "ee":
            slip = slip.with_context(salary_simulation=True)
        if worked_hours is not None and self.engine == "oca":
            slip.contract_id = employee.version_id
            slip.worked_days_line_ids = [
                Command.create(
                    {
                        "name": "Reviewed actual agreement hours",
                        "code": "WORK100",
                        "contract_id": employee.version_id.id,
                        "number_of_hours": worked_hours,
                        "number_of_days": 20,
                    }
                )
            ]
        elif worked and self.engine == "oca":
            slip.contract_id = employee.version_id
            slip.worked_days_line_ids = [
                Command.create(values)
                for values in slip.get_worked_day_lines(
                    slip.contract_id, slip.date_from, slip.date_to
                )
            ]
        slip.compute_sheet()
        if confirm:
            confirm_payslips(slip)
        return employee, slip

    def _fund_annex(self, **kwargs):
        if self.engine != "oca":
            self.skipTest("The public retained-fund adapter is for the OCA engine")
        employee, slip = self._employee_payslip(**kwargs)
        declaration = (
            self.env["l10n.sk.mvp"]
            .with_company(self.company)
            .create({"company_id": self.company.id, "year": "2026", "month": "3"})
        )
        declaration.action_generate()
        root = etree.fromstring(base64.b64decode(declaration.xml_attachment_id.datas))
        rows = root.xpath('//*[local-name()="poistneZamestnanca"]')
        row = next(row for row in rows if row.get("rc") == employee.identification_id)
        return employee, slip, declaration, row

    def test_fund_bases_keep_uncapped_accident_separate_from_social_cap(self):
        _employee, _slip, _declaration, row = self._fund_annex(wage=25000)
        for field in (
            "vzNp",
            "vzSp",
            "vzIp",
            "vzPvn",
            "vzGp",
            "vzRfs",
            "vzZecNp",
            "vzZecSp",
            "vzZecIp",
            "vzZecPvn",
            "vzPfp",
        ):
            self.assertEqual(row.get(field), "16764.00", field)
        self.assertEqual(row.get("vzUp"), "25000.00")

    def test_fund_bases_student_oop_excludes_pension_but_not_accident(self):
        _employee, _slip, _declaration, row = self._fund_annex(
            wage=200,
            agreement="dobps",
            regular=True,
            version_values={"l10n_sk_agreement_oop": True},
        )
        for field in (
            "vzNp",
            "vzSp",
            "vzIp",
            "vzPvn",
            "vzRfs",
            "vzZecNp",
            "vzZecSp",
            "vzZecIp",
            "vzZecPvn",
        ):
            self.assertEqual(row.get(field), "0.00", field)
        self.assertEqual(row.get("vzUp"), "200.00")
        self.assertEqual(row.get("vzGp"), "200.00")
        self.assertIsNone(row.get("vzPfp"))
        self.assertIsNone(row.get("pfpZamtel"))

    def test_fund_bases_old_age_employment_has_no_disability_or_unemployment(self):
        _employee, _slip, _declaration, row = self._fund_annex(
            wage=2000,
            version_values={
                "l10n_sk_pension_type": "old_age",
                "l10n_sk_tax_declaration_signed": False,
            },
        )
        for field in ("vzIp", "vzZecIp", "vzPvn", "vzZecPvn"):
            self.assertEqual(row.get(field), "0.00", field)
        self.assertEqual(row.get("vzSp"), "2000.00")
        self.assertEqual(row.get("vzZecSp"), "2000.00")

    def test_fund_bases_oop_precedes_the_monthly_cap(self):
        _employee, slip, _declaration, row = self._fund_annex(
            wage=16900,
            agreement="dobps",
            regular=True,
            version_values={"l10n_sk_agreement_oop": True},
        )
        self.assertEqual(slip.get_salary_line_total("PENSION"), -668)
        self.assertEqual(row.get("vzSp"), "16700.00")
        self.assertEqual(row.get("vzZecSp"), "16700.00")
        self.assertEqual(row.get("vzGp"), "16764.00")
        self.assertEqual(row.get("vzUp"), "16900.00")

    def test_fund_bases_two_old_age_agreements_at_200_have_only_accident_and_guarantee(
        self,
    ):
        if self.engine != "oca":
            self.skipTest("Public OCA retained-fund adapter")
        self.calendar = self.env["resource.calendar"].create(
            {
                "name": "Reviewed agreement capacity2.5h/week",
                "company_id": self.company.id,
                "attendance_ids": [Command.clear()]
                + [
                    Command.create(
                        {
                            "name": str(day),
                            "dayofweek": str(day),
                            "hour_from": 8,
                            "hour_to": 8.5,
                            "day_period": "morning",
                        }
                    )
                    for day in range(5)
                ],
            }
        )
        values = {
            "wage": 200,
            "agreement": "dopc",
            "regular": True,
            "worked_hours": 10,
            "version_values": {
                "l10n_sk_pension_type": "old_age",
                "l10n_sk_agreement_oop": True,
                "l10n_sk_hourly_wage": 20,
                "l10n_sk_health_exempt": True,
                "l10n_sk_tax_declaration_signed": False,
            },
        }
        self._employee_payslip(identification="5601011234", **values)
        _employee, slip, declaration, row = self._fund_annex(
            identification="5601021234", **values
        )
        self.assertEqual(slip.get_salary_line_total("GROSS"), 200)
        self.assertEqual(slip.get_salary_line_total("ACCIDENT"), 1.60)
        self.assertEqual(slip.get_salary_line_total("GUARANTEEEMPLOYER"), 0.50)
        for field in (
            "vzNp",
            "vzSp",
            "vzIp",
            "vzPvn",
            "vzRfs",
            "vzZecNp",
            "vzZecSp",
            "vzZecIp",
            "vzZecPvn",
        ):
            self.assertEqual(row.get(field), "0.00", field)
        self.assertEqual(row.get("vzUp"), "200.00")
        self.assertEqual(row.get("vzGp"), "200.00")
        self.assertEqual(row.get("pocetHodin"), "10.00")
        self.assertEqual(len(row.getparent()), 2)
        root = etree.fromstring(base64.b64decode(declaration.xml_attachment_id.datas))
        self.assertEqual(
            root.findtext("m:poistne/m:spoluPoistne", namespaces=NS), "4.20"
        )

    def test_fund_bases_regular_dovp_has_sickness_and_full_employer_unemployment(self):
        _employee, slip, _declaration, row = self._fund_annex(
            wage=2000, agreement="dovp", regular=True, worked=True
        )
        for field in ("vzNp", "vzZecNp", "vzPvn", "vzZecPvn"):
            self.assertEqual(row.get(field), "2000.00", field)
        self.assertEqual(slip.get_salary_line_total("SICK"), -28)
        self.assertEqual(slip.get_salary_line_total("UNEMPLOYMENTEMPLOYER"), 20)
        self.assertIsNone(row.get("pfpZamtel"))

    def test_fund_bases_partial_month_preserves_distinct_caps_and_days(self):
        _employee, slip, _declaration, row = self._fund_annex(
            wage=110000,
            worked=True,
            version_values={
                "date_version": date(2026, 3, 16),
                "contract_date_start": date(2026, 3, 16),
                "contract_date_end": date(2026, 3, 20),
            },
        )
        self.assertEqual(slip.get_salary_line_total("GROSS"), 25000)
        self.assertEqual(row.get("vzNp"), "16764.00")
        self.assertEqual(row.get("vzZecNp"), "2703.87")
        self.assertEqual(row.get("pocDni"), "5")

    def test_fund_bases_frozen_profile_keeps_mvp_and_vpp_disjoint(self):
        employee, slip, declaration, row = self._fund_annex(
            wage=2000, agreement="dopc", regular=True
        )
        before = dict(row.attrib)
        employee.version_id.write(
            {"l10n_sk_income_regular": False, "l10n_sk_pension_type": "old_age"}
        )
        self.assertIn(slip, declaration._get_period_payslips())
        self.assertEqual(declaration._build_annex()[0]["typ_zec"], "ZECD2")
        self.assertEqual(
            declaration._build_annex()[0]["fund_bases"]["vzNp"], before["vzNp"]
        )
        vpp = (
            self.env["l10n.sk.vpp"]
            .with_company(self.company)
            .create({"company_id": self.company.id, "year": "2026", "month": "3"})
        )
        self.assertNotIn(slip, vpp._get_period_payslips())

    def test_fund_bases_stale_skip_compute_requires_recalculation(self):
        if self.engine != "oca":
            self.skipTest("OCA confirmation controls")
        for mode in ("context", "checkbox"):
            self.env["ir.config_parameter"].sudo().set_param(
                "payroll.prevent_compute_on_confirm", False
            )
            employee, slip = self._employee_payslip(confirm=False)
            employee.version_id.l10n_sk_guarantee_exempt = True
            if mode == "checkbox":
                self.env["ir.config_parameter"].sudo().set_param(
                    "payroll.prevent_compute_on_confirm", True
                )
                slip.invalidate_recordset(["prevent_compute_on_confirm"])
            operated = slip.with_context(without_compute_sheet=mode == "context")
            with self.assertRaisesRegex(UserError, "sources changed"):
                operated.action_payslip_done()
            self.assertNotEqual(slip.state, "done")
            slip.compute_sheet()
            operated.action_payslip_done()
            self.assertEqual(slip.state, "done")
        self.env["ir.config_parameter"].sudo().set_param(
            "payroll.prevent_compute_on_confirm", False
        )

    def test_fund_bases_generated_inputs_and_posted_recalculation_are_protected(self):
        if self.engine != "oca":
            self.skipTest("OCA retained-fund controls")
        _employee, slip = self._employee_payslip()
        before = sorted(slip.line_ids.ids), slip.l10n_sk_social_assessment
        with self.assertRaisesRegex(UserError, "generated by payroll"):
            slip.write({"l10n_sk_social_assessment": {}})
        with self.assertRaisesRegex(UserError, "confirmed payroll"):
            slip.compute_sheet()
        slip.action_payslip_done()
        self.assertEqual(
            (sorted(slip.line_ids.ids), slip.l10n_sk_social_assessment), before
        )
        with self.assertRaisesRegex(UserError, "generated by payroll"):
            slip.with_context(default_l10n_sk_social_assessment={}).copy()

    def test_fund_bases_legacy_missing_evidence_does_not_guess_from_gross(self):
        _employee, slip, declaration, _row = self._fund_annex()
        archived = declaration.xml_attachment_id.datas
        self.env.cr.execute(
            "UPDATE hr_payslip SET l10n_sk_social_assessment=NULL WHERE id=%s",
            [slip.id],
        )
        slip.invalidate_recordset(["l10n_sk_social_assessment"])
        with self.assertRaisesRegex(UserError, "missing retained"):
            declaration._build_annex()
        self.assertEqual(declaration.xml_attachment_id.datas, archived)

    def test_fund_bases_posted_children_cannot_be_changed_or_reparented(self):
        if self.engine != "oca":
            self.skipTest("OCA source controls")
        employee, slip = self._employee_payslip()
        other = slip.copy()
        line = slip.line_ids.filtered(lambda row: row.code == "PENSION")
        for change in ({"amount": 1}, {"slip_id": other.id}):
            with self.assertRaisesRegex(
                UserError, "confirmed social-insurance sources"
            ):
                line.write(change)
        with self.assertRaisesRegex(UserError, "confirmed social-insurance sources"):
            line.unlink()
        with self.assertRaisesRegex(UserError, "confirmed social-insurance sources"):
            self.env["hr.payslip.input"].with_context(
                default_payslip_id=slip.id
            ).create(
                {
                    "name": "Changed source",
                    "code": "PN_DVZ",
                    "contract_id": employee.version_id.id,
                    "amount": 20,
                }
            )
        with self.assertRaisesRegex(UserError, "confirmed social-insurance sources"):
            self.env["hr.payslip.worked_days"].create(
                {
                    "payslip_id": slip.id,
                    "name": "Changed source",
                    "code": "WORK100",
                    "contract_id": employee.version_id.id,
                    "number_of_days": 1,
                    "number_of_hours": 8,
                }
            )

    def test_fund_bases_confirmation_stamp_survives_cancellation(self):
        if self.engine != "oca":
            self.skipTest("OCA source controls")
        _employee, slip = self._employee_payslip()
        self.assertTrue(slip.l10n_sk_social_confirmed_at)
        self.env["ir.config_parameter"].sudo().set_param(
            "payroll.allow_cancel_payslips", True
        )
        slip.invalidate_recordset(["allow_cancel_payslips"])
        slip.action_payslip_cancel()
        self.assertEqual(slip.state, "cancel")
        with self.assertRaisesRegex(UserError, "confirmed social-insurance sources"):
            slip.action_payslip_draft()
        with self.assertRaisesRegex(UserError, "confirmed social-insurance sources"):
            slip.unlink()
        with self.assertRaisesRegex(UserError, "confirmed social-insurance sources"):
            slip.line_ids[0].amount = 0

    def test_fund_bases_changed_worked_time_cannot_skip_recalculation(self):
        if self.engine != "oca":
            self.skipTest("OCA source controls")
        employee, slip = self._employee_payslip(confirm=False)
        self.env["hr.payslip.worked_days"].create(
            {
                "payslip_id": slip.id,
                "name": "Changed attendance",
                "code": "WORK100",
                "contract_id": employee.version_id.id,
                "number_of_days": 1,
                "number_of_hours": 8,
            }
        )
        with self.assertRaisesRegex(UserError, "sources changed"):
            slip.with_context(without_compute_sheet=True).action_payslip_done()

    def test_fund_bases_native_refund_preserves_original_and_needs_declaration_correction(
        self,
    ):
        _employee, slip, declaration, _row = self._fund_annex()
        before = sorted(slip.line_ids.ids), slip.l10n_sk_social_assessment
        slip.refund_sheet()
        refund = slip.refunded_id
        self.assertTrue(refund.credit_note)
        self.assertEqual(refund.state, "done")
        self.assertEqual(refund.get_salary_line_total("GROSS"), 2000)
        self.assertEqual(
            (sorted(slip.line_ids.ids), slip.l10n_sk_social_assessment), before
        )
        # A bookkeeping refund is not itself a reviewed monthly correction.
        # Do not silently add the original positive bases a second time.
        with self.assertRaisesRegex(UserError, "missing retained|Consolidate"):
            declaration._build_annex()

    def test_fund_bases_prorated_income_matches_the_recorded_currency_amount(self):
        if self.engine != "oca":
            self.skipTest("OCA retained monthly source")
        _, slip = self._employee_payslip(wage=2200, worked_hours=61.2175)
        self.assertEqual(slip.get_salary_line_total("GROSS"), 765.22)
        bases = slip._l10n_sk_mvp_fund_bases()
        self.assertEqual(bases["vzSp"], 765.22)
        self.assertEqual(slip.get_salary_line_total("PENSIONEMPLOYER"), 107.13)

    def test_fund_bases_second_independent_monthly_calculation_is_not_confirmed(self):
        if self.engine != "oca":
            self.skipTest("OCA retained monthly source")
        _, original = self._employee_payslip(
            agreement="dopc",
            wage=200,
            version_values={
                "l10n_sk_pension_type": "old_age",
                "l10n_sk_agreement_oop": True,
            },
        )
        duplicate = original.copy(
            {"name": "Second independent monthly wage", "state": "draft"}
        )
        duplicate.compute_sheet()
        with self.assertRaisesRegex(UserError, "Consolidate"):
            confirm_payslips(duplicate)
        self.assertEqual(original.state, "done")
        self.assertNotEqual(duplicate.state, "done")
        self.assertEqual(original._l10n_sk_mvp_fund_bases()["vzSp"], 0)

    def test_fund_bases_export_does_not_sum_independent_monthly_deductions(self):
        if self.engine != "oca":
            self.skipTest("OCA retained monthly source")
        _, original = self._employee_payslip(wage=25000)
        duplicate = original.copy(
            {"name": "Second capped monthly wage", "state": "draft"}
        )
        duplicate.compute_sheet()
        report = self.env["l10n.sk.mvp"]
        with self.assertRaisesRegex(UserError, "Consolidate"):
            report._l10n_sk_mvp_employee_fund_bases(original | duplicate)

    def test_generate_and_validate(self):
        employee, slip = self._employee_payslip()
        totals = {line.code: line.total for line in slip.line_ids}
        social_er = abs(round(totals.get("SOCIALEMPLOYERTOTAL", 0.0), 2))
        social_ee = abs(round(totals.get("SOCIALEMPLOYEETOTAL", 0.0), 2))
        self.assertGreater(social_er, 0.0, "employer social must be computed")

        decl = (
            self.env["l10n.sk.mvp"]
            .with_company(self.company)
            .create(
                {
                    "company_id": self.company.id,
                    "year": "2026",
                    "month": "3",
                    "payment_date": date(2026, 3, 31),
                }
            )
        )
        self.assertTrue(decl.version_id, "MVP version should default")
        decl.action_generate()
        self.assertEqual(decl.state, "generated")

        xml_bytes = base64.b64decode(decl.xml_attachment_id.datas)
        schema = etree.XMLSchema(
            etree.parse(file_path("l10n_sk_hr_payroll_mvp/data/MVPP-v2026.xsd"))
        )
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
            if etree.QName(el).localname.endswith(("Zamtel", "Zamnec")) and el.text
        )
        spolu = float(root.find(".//m:poistne/m:spoluPoistne", NS).text)
        self.assertAlmostEqual(
            spolu, round(rows, 2), 2, "spoluPoistne must be the sum of the fund rows"
        )
        # ...and it must exclude health, i.e. fall short of the payslip's
        # health-contaminated social categories by exactly the health premium.
        health = abs(round(totals.get("HEALTH", 0.0), 2)) + abs(
            round(totals.get("HEALTHEMPLOYER", 0.0), 2)
        )
        self.assertAlmostEqual(
            spolu,
            round(social_er + social_ee - health, 2),
            2,
            "the social premium must exclude health insurance",
        )

        # Per-employee annex present with the employee's rodné číslo.
        annex = root.findall(".//m:poistneZamestnanca", NS)
        self.assertEqual(len(annex), 1)
        self.assertEqual(annex[0].get("rc"), "8501011234")

    def test_missing_rc_raises(self):
        from odoo.exceptions import UserError

        employee, slip = self._employee_payslip()
        employee.identification_id = False
        decl = (
            self.env["l10n.sk.mvp"]
            .with_company(self.company)
            .create({"company_id": self.company.id, "year": "2026", "month": "3"})
        )
        with self.assertRaises(UserError):
            decl.action_generate()

    def _mvp(self):
        return (
            self.env["l10n.sk.mvp"]
            .with_company(self.company)
            .create({"company_id": self.company.id, "year": "2026", "month": "3"})
        )

    def test_dohody_follow_income_regularity(self):
        """A dohoda with regular income is reported here, under its own
        relationship code; one with irregular income goes to the VPP and
        must not be reported here as well (cssk-public#12)."""
        _e1, regular = self._employee_payslip(
            wage=1000.0, agreement="dopc", regular=True
        )
        _e2, irregular = self._employee_payslip(
            wage=1000.0, agreement="dovp", regular=False, identification="9001011236"
        )
        decl = self._mvp()
        self.assertEqual(decl._get_period_payslips(), regular)
        self.assertNotIn(irregular, decl._get_period_payslips())
        decl.action_generate()
        root = etree.fromstring(base64.b64decode(decl.xml_attachment_id.datas))
        etree.XMLSchema(
            etree.parse(file_path("l10n_sk_hr_payroll_mvp/data/MVPP-v2026.xsd"))
        ).assertValid(root)
        codes = {
            row.get("rc"): row.get("typZec")
            for row in root.findall(".//m:poistneZamestnanca", NS)
        }
        self.assertEqual(codes, {"8501011234": "ZECD2"})

    def test_later_contract_change_keeps_the_past_period(self):
        """The payslip's own contract version decides, not today's: a DoPČ
        irregular in March and re-agreed as regular from April stays off the
        March MVP."""
        employee, slip = self._employee_payslip(
            wage=1000.0, agreement="dopc", regular=False
        )
        march = employee.version_id
        employee.create_version(
            {
                "date_version": date(2026, 4, 1),
                "l10n_sk_income_regular": True,
            }
        )
        self.assertNotEqual(employee.version_id, march)
        self.assertTrue(employee.version_id.l10n_sk_income_regular)
        self.assertNotIn(slip, self._mvp()._get_period_payslips())

    def test_sp_vs_is_editable_on_the_form(self):
        """The variable symbol is required by the preflight but was on no
        form at all; it is edited on the declaration form now."""
        arch = self.env["l10n.sk.mvp"].get_views([(False, "form")])["views"]["form"][
            "arch"
        ]
        self.assertIn('name="sp_vs"', arch)
        decl = (
            self.env["l10n.sk.mvp"]
            .with_company(self.company)
            .create({"company_id": self.company.id, "year": "2026", "month": "3"})
        )
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
                if (
                    len(parts) == 3
                    and parts[0].endswith(".xsd")
                    and "/" not in parts[0]
                ):
                    pins[parts[0]] = (parts[1], int(parts[2]))
        return pins

    def test_bundled_schemas_match_the_pinned_digests(self):
        import hashlib
        import os

        pins = self._pins()
        self.assertTrue(pins, "SCHEMA_VERSION lists no schemas")
        for name, (digest, size) in pins.items():
            path = os.path.join(self._data_dir(), name)
            self.assertTrue(os.path.exists(path), "%s is pinned but missing" % name)
            with open(path, "rb") as fh:
                blob = fh.read()
            self.assertEqual(len(blob), size, "%s size moved" % name)
            self.assertEqual(
                hashlib.md5(blob).hexdigest(),
                digest,
                "%s does not match its pin — if this is a deliberate "
                "refresh, update data/SCHEMA_VERSION" % name,
            )

    def test_every_bundled_schema_is_pinned(self):
        import os

        on_disk = {f for f in os.listdir(self._data_dir()) if f.endswith(".xsd")}
        self.assertEqual(
            on_disk,
            set(self._pins()),
            "unpinned schema(s): %s" % sorted(on_disk - set(self._pins())),
        )
