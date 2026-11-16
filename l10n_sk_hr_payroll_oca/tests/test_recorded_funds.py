# Copyright 2026 Data Dance s.r.o., votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Signed capture, frozen native-formula parity and declaration policy."""

import ast
import json
from copy import deepcopy
from decimal import Decimal
from html import unescape
from pathlib import Path
from unittest.mock import patch

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from ..models.fund_capture import FundCapturePayslip


@tagged("post_install", "-at_install")
class TestRecordedFundPayroll(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, lang="en_US"))
        cls.company = cls.env["res.company"].create(
            {
                "name": "Fund parity company",
                "country_id": cls.env.ref("base.sk").id,
            }
        )
        cls.env.user.company_ids |= cls.company
        cls.structure = cls.env.ref(
            "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_employee_salary"
        )
        # Isolate reference arithmetic from the optional minimum-wage rule.
        # That rule has its own statutory tests; these cases deliberately use
        # small/sub-cent inputs and must not silently become a 915 EUR wage.
        cls.structure.rule_ids -= cls.structure.rule_ids.filtered(
            lambda rule: rule.code == "MIN_WAGE_TOPUP"
        )
        cls.adjustment = cls.env["hr.salary.rule"].create(
            {
                "name": "Synthetic signed gross adjustment",
                "code": "FUND_ADJUSTMENT",
                "sequence": 90,
                "category_id": cls.env.ref("l10n_sk_hr_payroll_oca.ALW").id,
                "condition_select": "python",
                "condition_python": "result = 'FUND_ADJUSTMENT' in inputs.dict",
                "amount_select": "code",
                "amount_python_compute": "result = inputs.FUND_ADJUSTMENT.amount",
            }
        )
        cls.structure.rule_ids |= cls.adjustment
        cls.employee = (
            cls.env["hr.employee"]
            .with_company(cls.company)
            .create(
                {
                    "name": "Fund parity employee",
                    "company_id": cls.company.id,
                    "identification_id": "8501011234",
                    "date_version": "2024-01-01",
                    "contract_date_start": "2024-01-01",
                    "struct_id": cls.structure.id,
                    "wage": 500,
                    "l10n_sk_health_oop_claim": True,
                }
            )
        )
        cls.version = cls.employee.version_id

    def _slip(self, *, wage=500.123, clawback=0, credit_note=False, **values):
        rounded_wage = self.company.currency_id.round(wage)
        self.version.wage = rounded_wage
        adjustment = float(Decimal(str(wage)) - Decimal(str(rounded_wage))) + clawback
        inputs = (
            [
                Command.create(
                    {
                        "name": "Synthetic correction",
                        "code": "FUND_ADJUSTMENT",
                        "amount": adjustment,
                        "contract_id": self.version.id,
                    }
                )
            ]
            if adjustment
            else []
        )
        slip = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "name": "Native formula parity",
                    "employee_id": self.employee.id,
                    "company_id": self.company.id,
                    "contract_id": self.version.id,
                    "struct_id": self.version.struct_id.id,
                    "date_from": "2026-06-01",
                    "date_to": "2026-06-30",
                    "credit_note": credit_note,
                    "input_line_ids": inputs,
                    **values,
                }
            )
        )
        slip.compute_sheet()
        return slip

    @staticmethod
    def _lines(slip):
        return sorted(
            (row.code, row.amount, row.quantity, row.rate, row.total)
            for row in slip.line_ids
        )

    def _funds(self, slip):
        return {
            (row["fund"], row["side"]): row
            for row in slip._cssk_recorded_fund_bases() or []
        }

    def _report(self, correction=False):
        if "cssk.payroll.declaration.mixin" not in self.env:
            self.skipTest("Shared declaration framework not installed")
        report = (
            self.env["cssk.payroll.declaration.mixin"]
            .with_company(self.company)
            .new(
                {
                    "company_id": self.company.id,
                    "year": "2026",
                    "month": "6",
                }
            )
        )
        report.is_correction = correction
        return report

    def _compare_reference_formulas(self, **values):
        observed = self._slip(**values)
        expected = self._lines(observed)
        native = json.loads(
            (Path(__file__).parent / "data/native_fund_rules.json").read_text()
        )
        rules = self.env["hr.salary.rule"].search(
            [
                ("code", "in", list(native)),
                ("id", "in", self.structure.rule_ids.ids),
            ]
        )
        saved = {rule.id: rule.amount_python_compute for rule in rules}
        try:
            for rule in rules:
                rule.amount_python_compute = unescape(native[rule.code])
            baseline = self._slip(**values)
            self.assertEqual(self._lines(baseline), expected)
            self.assertFalse(baseline.l10n_sk_fund_assessment)
        finally:
            for rule in rules:
                rule.amount_python_compute = saved[rule.id]
        return observed

    def test_arithmetic_matches_disclosed_reference_on_non_round_income(self):
        for wage in (0.06, 100.129, 379.995, 500.123, 569.999, 16764.015, 25000.129):
            with self.subTest(wage=wage):
                self.assertTrue(
                    self._compare_reference_formulas(wage=wage).l10n_sk_fund_assessment
                )

    def test_every_reference_formula_ast_matches_before_record_emission(self):
        native = json.loads(
            (Path(__file__).parent / "data/native_fund_rules.json").read_text()
        )
        rules = self.structure.rule_ids.filtered(lambda rule: rule.code in native)
        self.assertEqual(len(rules), 15)
        for rule in rules:
            original = ast.parse(unescape(native[rule.code]).strip())
            current = ast.parse(rule.amount_python_compute.strip())
            if rule.code != "HEALTHDOPLATOK":
                emission = current.body.pop()
                self.assertIsInstance(emission, ast.If)
                self.assertEqual(
                    ast.unparse(emission.test), "payslip._l10n_sk_is_recording_funds()"
                )
            self.assertEqual(ast.dump(current), ast.dump(original), rule.code)

    def test_every_emitted_base_is_the_expression_the_rule_charged_on(self):
        # The emission repeats the base only where the frozen formula has no
        # variable for it; then it must be that very expression. Where the
        # formula names a variable, the emission must use it. An exemption
        # that zeroes the premium must zero the recorded base too.
        native = json.loads(
            (Path(__file__).parent / "data/native_fund_rules.json").read_text()
        )
        rules = self.structure.rule_ids.filtered(
            lambda rule: rule.code in native and rule.code != "HEALTHDOPLATOK"
        )
        self.assertEqual(len(rules), 14)

        def is_result(node):
            return (
                isinstance(node, ast.Assign)
                and [ast.unparse(target) for target in node.targets] == ["result"]
            )

        for rule in rules:
            with self.subTest(rule=rule.code):
                body = ast.parse(rule.amount_python_compute.strip()).body
                call = body.pop().body[0].value
                fund, side, base, rate, amount = call.args
                self.assertEqual(ast.unparse(call.func), "payslip.l10n_sk_fund_record")
                self.assertIn(ast.unparse(amount), {"result", "-result"})
                charged_at = next(
                    index for index, node in enumerate(body) if is_result(node)
                )
                charged = next(
                    node.left
                    for node in ast.walk(body[charged_at].value)
                    if isinstance(node, ast.BinOp)
                    and isinstance(node.op, ast.Mult)
                    and ast.dump(node.right) == ast.dump(rate)
                )
                exemptions = [
                    node.test
                    for node in body[charged_at + 1 :]
                    if isinstance(node, ast.If)
                    and len(node.body) == 1
                    and is_result(node.body[0])
                    and ast.unparse(node.body[0].value) == "0.0"
                ]
                if exemptions:
                    (exemption,) = exemptions
                    self.assertIsInstance(base, ast.IfExp)
                    self.assertEqual(ast.dump(base.test), ast.dump(exemption))
                    self.assertEqual(ast.unparse(base.body), "0.0")
                    base = base.orelse
                self.assertEqual(ast.dump(base), ast.dump(charged))
                if isinstance(charged, ast.Name):
                    # Not reassigned between the charge and the emission.
                    self.assertFalse(
                        [
                            node
                            for node in body[charged_at + 1 :]
                            for sub in ast.walk(node)
                            if isinstance(sub, ast.Name)
                            and sub.id == charged.id
                            and isinstance(sub.ctx, ast.Store)
                        ]
                    )

    def test_guarantee_exempt_records_base_zero_and_keeps_native_amounts(self):
        self.version.l10n_sk_guarantee_exempt = True
        slip = self._compare_reference_formulas(wage=1500.123)
        row = self._funds(slip)[("guarantee", "employer")]
        self.assertEqual((row["base"], row["amount"]), ("0", "0"))
        self.assertTrue(slip.l10n_sk_fund_assessment["profile"]["guarantee_exempt"])
        # Other employer funds keep their base.
        self.assertNotEqual(self._funds(slip)[("reserve", "employer")]["base"], "0")

    def test_guarantee_insured_records_the_capped_base(self):
        row = self._funds(self._slip(wage=1500))[("guarantee", "employer")]
        self.assertEqual((row["base"], row["amount"]), ("1500", "3.75"))

    def test_topup_without_a_health_record_leaves_the_payslip_unrecorded(self):
        health = self.env.ref(
            "l10n_sk_hr_payroll_oca.l10n_sk_health_insurance_employee"
        )
        topup = self.env.ref("l10n_sk_hr_payroll_oca.l10n_sk_health_doplatok_employee")
        health.write({"condition_select": "python", "condition_python": "result = False"})
        topup.amount_python_compute = "result = -1.0"
        slip = self._slip()
        self.assertFalse(slip.line_ids.filtered(lambda row: row.code == "HEALTH"))
        self.assertEqual(
            slip.line_ids.filtered(lambda row: row.code == "HEALTHDOPLATOK").total, -1.0
        )
        self.assertFalse(slip.l10n_sk_fund_assessment)

    def test_payslip_without_contract_records_the_computed_version(self):
        slip = self._slip(contract_id=False)
        self.assertFalse(slip.contract_id)
        self.assertEqual(slip.line_ids.contract_id, self.version)
        evidence = slip.l10n_sk_fund_assessment
        self.assertTrue(evidence)
        # The identity keeps contract_id (empty here), as stored before.
        self.assertIs(evidence["identity"]["contract"], False)
        self.assertEqual(evidence["profile"]["version"], self.version.id)
        self.assertTrue(self._funds(slip))

    def test_profile_of_another_version_is_not_read(self):
        for values in ({}, {"contract_id": False}):
            with self.subTest(values=values):
                slip = self._slip(**values)
                evidence = deepcopy(slip.l10n_sk_fund_assessment)
                self.assertEqual(evidence["identity"]["contract"], slip.contract_id.id)
                evidence["profile"]["version"] = self.version.id + 1000
                slip._l10n_sk_store_fund_evidence(evidence)
                self.assertFalse(slip._cssk_recorded_fund_bases())

    def test_lines_of_another_contract_than_contract_id_are_not_read(self):
        slip = self._slip()
        self.assertTrue(slip._cssk_recorded_fund_bases())
        other = self.version.copy({"date_version": "2025-01-01"})
        slip.line_ids[:1].contract_id = other
        self.assertFalse(slip._cssk_recorded_fund_bases())

    def test_support_check_uses_the_contracts_the_engine_computes_over(self):
        # A contract_id outside the period computes no line at all; the
        # support check must say so itself rather than rely on that.
        slip = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "name": "Outside the contract",
                    "employee_id": self.employee.id,
                    "company_id": self.company.id,
                    "contract_id": self.version.id,
                    "struct_id": self.version.struct_id.id,
                    "date_from": "2023-06-01",
                    "date_to": "2023-06-30",
                }
            )
        )
        self.assertFalse(slip._get_employee_contracts())
        self.assertFalse(slip._l10n_sk_can_record_funds())
        slip.compute_sheet()
        self.assertFalse(slip.line_ids)
        self.assertFalse(slip.l10n_sk_fund_assessment)

    def test_negative_gross_and_computed_credit_note_keep_native_amounts(self):
        for credit in (False, True):
            with self.subTest(credit=credit):
                slip = self._compare_reference_formulas(
                    clawback=-1000.246, credit_note=credit
                )
                self.assertLess(
                    slip.line_ids.filtered(lambda row: row.code == "GROSS").total, 0
                )
                self.assertLess(
                    float(self._funds(slip)[("accident", "employer")]["base"]), 0
                )

    def test_subcent_input_reaches_actual_gross_without_rounding_away(self):
        slip = self._slip(wage=500.123)
        # Monetary line.total rounds for display; the rule category and the
        # uncapped accident assessment retain the actual sub-cent input.
        gross = float(self._funds(slip)[("accident", "employer")]["base"])
        self.assertAlmostEqual(gross, 500.123, places=6)
        self.assertNotEqual(gross, round(gross, 2))

    def test_non_round_premiums_pin_the_native_amounts(self):
        low = self._slip(wage=379.995)
        self.assertEqual(
            low.line_ids.filtered(lambda row: row.code == "HEALTHEMPLOYER").total, 41.79
        )
        edge = self._slip(wage=569.999)
        self.assertEqual(
            edge.line_ids.filtered(lambda row: row.code == "HEALTH").total, -28.49
        )

    def test_agreement_oop_is_applied_before_the_statutory_cap(self):
        self.version.struct_id = self.env.ref(
            "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_dopc"
        )
        self.version.struct_id.rule_ids |= self.adjustment
        self.version.write(
            {
                "l10n_sk_agreement_oop": True,
                "l10n_sk_pension_type": "old_age",
                "l10n_sk_hourly_wage": 0,
            }
        )
        slip = self._compare_reference_formulas(wage=0, clawback=17100)
        self.assertEqual(self._funds(slip)[("pension", "employee")]["base"], "16764")

    def _student_agreement(self, oop=True):
        self.version.struct_id = self.env.ref(
            "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_dobps"
        )
        self.version.struct_id.rule_ids |= self.adjustment
        self.employee.write(
            {"birthday": "2005-01-01", "identification_id": "0501011234"}
        )
        self.version.write(
            {
                "l10n_sk_agreement_oop": oop,
                "l10n_sk_pension_type": False,
                "l10n_sk_hourly_wage": 20,
                "l10n_sk_health_exempt": True,
            }
        )

    def test_all_five_eligible_funds_reduce_income_before_the_cap(self):
        self._student_agreement()
        for income in (200, 16763.995, 16764, 16900, 17100):
            with self.subTest(income=income):
                funds = self._funds(self._slip(wage=0, clawback=income))
                expected = min(max(0, income - 200), 16764)
                for key in (
                    ("pension", "employee"),
                    ("disability", "employee"),
                    ("pension", "employer"),
                    ("disability", "employer"),
                    ("reserve", "employer"),
                ):
                    self.assertAlmostEqual(
                        float(funds[key]["base"]), expected, places=6
                    )
                self.assertEqual(float(funds[("accident", "employer")]["base"]), income)
                self.assertEqual(
                    float(funds[("guarantee", "employer")]["base"]), min(income, 16764)
                )

    def test_high_income_actual_pension_charges_use_full_cap_after_oop(self):
        self._student_agreement()
        funds = self._funds(self._slip(wage=0, clawback=17100))
        self.assertEqual(funds[("pension", "employee")]["amount"], "670.56")
        self.assertEqual(funds[("disability", "employee")]["amount"], "502.92")
        self.assertEqual(funds[("pension", "employer")]["amount"], "2346.96")
        self.assertEqual(funds[("disability", "employer")]["amount"], "502.92")
        self.assertEqual(funds[("reserve", "employer")]["amount"], "796.29")

    def test_without_oop_the_existing_maximum_still_applies(self):
        self._student_agreement(oop=False)
        funds = self._funds(self._slip(wage=0, clawback=17100))
        self.assertEqual(funds[("pension", "employee")]["base"], "16764")

    def test_year_boundary_uses_2026_and_2027_dated_oop_and_maximum(self):
        self._student_agreement()
        for start, end, oop, maximum in (
            ("2026-12-01", "2026-12-31", 200, 16764),
            ("2027-01-01", "2027-01-31", 300, 17820),
        ):
            with self.subTest(start=start):
                slip = self._slip(wage=0, clawback=19000, date_from=start, date_to=end)
                self.assertEqual(slip.rule_parameter("l10n_sk_dohoda_oop"), oop)
                self.assertEqual(
                    slip.rule_parameter("l10n_sk_monthly_taxable_max"), maximum
                )
                funds = self._funds(slip)
                self.assertEqual(float(funds[("pension", "employee")]["base"]), maximum)
                self.assertEqual(float(funds[("reserve", "employer")]["base"]), maximum)

    def test_positive_base_with_zero_rounded_premium_is_not_missing(self):
        row = self._funds(self._slip(wage=0.06))[("sickness", "employee")]
        self.assertEqual((row["base"], row["amount"]), ("0.06", "0"))

    def test_profile_is_stored_once_without_restricted_birth_number(self):
        evidence = self._slip().l10n_sk_fund_assessment
        serialized = json.dumps(evidence, sort_keys=True)
        self.assertIn("profile", evidence)
        self.assertNotIn(self.employee.identification_id, serialized)
        self.assertTrue(
            all(
                set(row["facts"]) <= {"rule_code", "topup"}
                for row in evidence["records"]
            )
        )
        self.assertLess(len(serialized.encode()), 8000)

    def test_rule_evaluation_cannot_rewrite_confirmed_evidence(self):
        slip = self._slip()
        slip.with_context(without_compute_sheet=True).action_payslip_done()
        before = deepcopy(slip.l10n_sk_fund_assessment)
        slip.get_lines_dict()
        slip._get_payslip_lines(slip.contract_id.ids, slip.id)
        for spoofed in (True, {"supported": slip.ids}):
            slip.with_context(_l10n_sk_fund_capture=spoofed).get_lines_dict()
        self.assertEqual(slip.l10n_sk_fund_assessment, before)

    def test_structure_without_country_records_emitted_funds(self):
        self.version.struct_id = self.structure.copy(
            {"name": "Custom structure", "country_id": False}
        )
        self.assertTrue(self._slip().l10n_sk_fund_assessment)

    def test_cross_month_calculates_and_stays_unrecorded(self):
        self.assertFalse(
            self._compare_reference_formulas(
                date_to="2026-07-31"
            ).l10n_sk_fund_assessment
        )

    def test_invalid_optional_metadata_does_not_block_native_payroll(self):
        rule = self.env.ref(
            "l10n_sk_hr_payroll_oca.l10n_sk_sickness_insurance_employee"
        )
        rule.amount_python_compute += '\nl10n_sk_fund_record = {"invalid": True}\n'
        slip = self._slip()
        self.assertTrue(slip.line_ids)
        self.assertFalse(slip.l10n_sk_fund_assessment)

    def test_custom_quantity_does_not_store_a_charge_different_from_native_line(self):
        rule = self.env.ref(
            "l10n_sk_hr_payroll_oca.l10n_sk_sickness_insurance_employee"
        )
        rule.amount_python_compute += "\nresult_qty = 2.0\n"
        slip = self._slip()
        self.assertTrue(slip.line_ids.filtered(lambda row: row.code == "SICK"))
        self.assertFalse(slip.l10n_sk_fund_assessment)

    def test_generated_field_and_context_default_cannot_be_supplied(self):
        slip = self._slip()
        with self.assertRaisesRegex(UserError, "generated"):
            slip.write({"l10n_sk_fund_assessment": False})
        with self.assertRaisesRegex(UserError, "generated"):
            slip.with_context(default_l10n_sk_fund_assessment={}).copy()

    def test_corrupt_source_warns_for_original_and_refuses_correction(self):
        slip = self._slip()
        slip.line_ids.filtered(lambda row: row.code == "HEALTH").amount = -17
        report = self._report()
        with patch.object(type(report), "message_post", create=True) as post:
            report._collect_payslip_fund_bases(slip)
            report._collect_payslip_fund_bases(slip)
            self.assertIn(slip.display_name, report.fund_bases_warning)
            self.assertEqual(post.call_count, 1)
        correction = self._report(correction=True)
        with self.assertRaisesRegex(UserError, "Precise recorded"):
            correction._collect_payslip_fund_bases(slip)

    def test_framework_policy_runs_during_totals_without_caller_flag(self):
        slip = self._slip()
        super(FundCapturePayslip, slip).write({"l10n_sk_fund_assessment": False})
        report = self._report()
        with (
            patch.object(type(report), "_report_code", "sk_mvp"),
            patch.object(type(report), "message_post", create=True),
        ):
            result = report._collect_payslip_totals(slip)
            self.assertIs(result["recorded_funds"][slip.id], False)
            self.assertIn(slip.display_name, report.fund_bases_warning)
        correction = self._report(correction=True)
        with (
            patch.object(type(correction), "_report_code", "sk_vpp"),
            self.assertRaisesRegex(UserError, "Precise recorded"),
        ):
            correction._collect_payslip_totals(slip)

    def test_missing_insurance_records_do_not_block_a_tax_report_correction(self):
        slip = self._slip()
        super(FundCapturePayslip, slip).write({"l10n_sk_fund_assessment": False})
        report = self._report(correction=True)
        with patch.object(type(report), "_report_code", "sk_monthly_tax_overview"):
            self.assertNotIn("recorded_funds", report._collect_payslip_totals(slip))

    def test_native_refund_adapter_and_pairing_are_owned_by_bridge(self):
        slip = self._slip()
        slip.with_context(without_compute_sheet=True).action_payslip_done()
        original = self._funds(slip)
        self.version.wage = 1500
        slip.refund_sheet()
        refund = slip.refunded_id
        self.assertTrue(refund.credit_note)
        for key, row in self._funds(refund).items():
            self.assertEqual(
                (row["base"], row["amount"]),
                (original[key]["base"], original[key]["amount"]),
            )
        self.assertFalse((slip | refund)._cssk_effective_fund_payslips())
