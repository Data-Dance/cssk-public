# Copyright 2026 Data Dance s.r.o., votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import date

from odoo import Command
from odoo.exceptions import UserError

from .test_sk_payroll import TestSkPayroll


class TestHealthAssessmentPayroll(TestSkPayroll):
    def _review_health_calendar(self, contract, rows):
        calendar = self.env["l10n.sk.health.calendar"].create(
            {
                "employee_id": contract.employee_id.id,
                "company_id": contract.company_id.id,
                "month": "2026-06-01",
                "complete": True,
                "evidence": "Synthetic work dates and notices",
                "interval_ids": [
                    Command.create({"kind": kind, "date_start": start, "date_end": end})
                    for kind, start, end in rows
                ],
            }
        )
        calendar.action_review()
        return calendar

    def test_partial_state_status_reduces_the_minimum_not_actual_premiums(self):
        contract, employee = self._tiny_part_timer()
        self._review_health_calendar(
            contract,
            [
                ("2", "2026-06-01", "2026-06-30"),
                ("state", "2026-06-16", "2026-06-30"),
            ],
        )
        slip = self._make_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30)
        )
        self.assertEqual(slip.get_salary_line_total("HEALTH"), -5)
        self.assertEqual(slip.get_salary_line_total("HEALTHEMPLOYER"), 11)
        self.assertEqual(slip.get_salary_line_total("HEALTHDOPLATOK"), -6.72)
        facts = slip._l10n_sk_health_assessment_facts()
        self.assertEqual((facts["insured_days"], facts["minimum_days"]), (30, 15))
        self.assertEqual(facts["minimum_opt_out"], 0)

    def test_self_employed_concurrency_disables_monthly_op_without_changing_base_category(
        self,
    ):
        contract, employee = self._make_low_earner(l10n_sk_health_oop_claim=True)
        self._review_health_calendar(
            contract,
            [
                ("2", "2026-06-01", "2026-06-30"),
                ("self_employed", "2026-06-30", "2026-06-30"),
            ],
        )
        slip = self._make_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30)
        )
        facts = slip._l10n_sk_health_assessment_facts()
        self.assertEqual(
            (facts["op_income"], facts["op"], facts["employee"]), (500, 0, 25)
        )
        self.assertEqual(slip.get_salary_line_total("HEALTH"), -25)

    def test_one_disability_day_changes_both_rates_and_exempts_the_minimum(self):
        contract, employee = self._tiny_part_timer()
        self._review_health_calendar(
            contract,
            [
                ("2", "2026-06-01", "2026-06-30"),
                ("disabled", "2026-06-30", "2026-06-30"),
            ],
        )
        slip = self._make_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30)
        )
        self.assertEqual(slip.get_salary_line_total("HEALTH"), -2.5)
        self.assertEqual(slip.get_salary_line_total("HEALTHEMPLOYER"), 5.5)
        self.assertEqual(slip.get_salary_line_total("HEALTHDOPLATOK"), 0)
        facts = slip._l10n_sk_health_assessment_facts()
        self.assertTrue(facts["disabled"])
        self.assertEqual((facts["rate_employee"], facts["rate_employer"]), (2.5, 5.5))

    def test_agreement_two_days_use_the_same_source_for_minimum_and_statement(self):
        contract, employee = self._make_dohodar(l10n_sk_agreement_type="dopc")
        contract.wage = 10
        self._review_health_calendar(
            contract,
            [
                ("2D", "2026-06-02", "2026-06-02"),
                ("2D", "2026-06-12", "2026-06-12"),
            ],
        )
        slip = self._make_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30)
        )
        self.assertEqual(slip.get_salary_line_total("HEALTH"), -0.5)
        self.assertEqual(slip.get_salary_line_total("HEALTHEMPLOYER"), 1.1)
        self.assertEqual(slip.get_salary_line_total("HEALTHDOPLATOK"), -1.43)
        facts = slip._l10n_sk_health_assessment_facts()
        self.assertEqual((facts["insured_days"], facts["minimum_days"]), (2, 2))
        self.assertEqual(facts["other_income"], 10)

    def test_unreviewed_revision_blocks_new_calculation_but_not_old_evidence(self):
        contract, employee = self._make_low_earner()
        calendar = self._review_health_calendar(
            contract, [("2", "2026-06-01", "2026-06-30")]
        )
        slip = self._make_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30)
        )
        old = slip._l10n_sk_health_assessment_facts()
        calendar.action_create_revision()
        self.assertEqual(slip._l10n_sk_health_assessment_facts(), old)
        with self.assertRaises(UserError):
            slip.compute_sheet()

    def test_extra_health_line_cannot_hide_behind_the_first_matching_code(self):
        contract, employee = self._make_low_earner()
        slip = self._make_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30)
        )
        original = slip.line_ids.filtered(lambda line: line.code == "HEALTH")
        original.copy({"amount": -1})
        # OCA's legacy accessor returns only the first matching line. The
        # declaration evidence must verify the full monetary source instead.
        self.assertEqual(
            sum(
                slip.line_ids.filtered(lambda line: line.code == "HEALTH").mapped(
                    "total"
                )
            ),
            original.total - 1,
        )
        with self.assertRaises(UserError):
            slip._l10n_sk_health_assessment_facts()

    def test_income_after_employment_is_other_income_for_the_insurer(self):
        contract, _employee = self._make_low_earner(l10n_sk_health_oop_claim=True)
        contract.contract_date_end = date(2026, 5, 31)
        facts = contract.l10n_sk_health_employee_assessment(
            500, 5, date(2026, 6, 1), 380, 570
        )
        self.assertEqual(facts["op_income"], 0)
        self.assertEqual(facts["other_income"], 500)
        self.assertEqual(facts["op"], 0)
        self.assertEqual(facts["employee"], 25)

    def test_concurrent_minimum_optout_requires_the_retained_written_notice(self):
        contract, employee = self._tiny_part_timer(l10n_sk_health_minimum_opt_out=True)
        with self.assertRaises(UserError):
            self._make_payslip(contract, employee, date(2026, 6, 1), date(2026, 6, 30))

    def test_concurrent_minimum_optout_changes_only_the_topup(self):
        contract, employee = self._tiny_part_timer(
            l10n_sk_health_minimum_opt_out=True,
            l10n_sk_health_minimum_evidence="Synthetic written notice of concurrent employment",
        )
        slip = self._make_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30)
        )
        self.assertEqual(slip.get_salary_line_total("HEALTH"), -5)
        self.assertEqual(slip.get_salary_line_total("HEALTHEMPLOYER"), 11)
        self.assertEqual(slip.get_salary_line_total("HEALTHDOPLATOK"), 0)
        self.assertEqual(slip._l10n_sk_health_assessment_facts()["minimum_opt_out"], 1)

    def test_retained_assessment_does_not_follow_a_later_hr_profile_edit(self):
        contract, employee = self._make_low_earner(l10n_sk_health_oop_claim=True)
        slip = self._make_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30)
        )
        facts = slip._l10n_sk_health_assessment_facts()
        self.assertEqual(facts["base"], 360)
        self.assertEqual(facts["insured_days"], 30)
        contract.l10n_sk_health_oop_claim = False
        employee.identification_id = "9001010007"
        self.assertEqual(slip._l10n_sk_health_assessment_facts(), facts)

    def test_retained_assessment_is_not_a_public_writable_override(self):
        contract, employee = self._make_low_earner()
        slip = self._make_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30)
        )
        with self.assertRaises(UserError):
            slip.write({"l10n_sk_health_assessment_snapshot": {}})
        with self.assertRaises(UserError):
            self.env["hr.payslip"].with_context(
                default_l10n_sk_health_assessment_snapshot={"employee": 999}
            ).create({})
        self.assertFalse(slip.copy().l10n_sk_health_assessment_snapshot)

    def test_retained_assessment_checks_actual_salary_lines(self):
        contract, employee = self._make_low_earner()
        slip = self._make_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30)
        )
        slip.line_ids.filtered(lambda line: line.code == "HEALTH").amount = -99
        with self.assertRaises(UserError):
            slip._l10n_sk_health_assessment_facts()

    def test_rule_uses_the_same_explicit_assessment_as_the_report_adapter(self):
        contract, employee = self._make_low_earner(l10n_sk_health_oop_claim=True)
        slip = self._make_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30)
        )
        facts = contract.l10n_sk_health_employee_assessment(
            slip.get_salary_line_total("GROSS"), 5, slip.date_from, 380, 570
        )
        self.assertEqual(facts["op_income"], 500)
        self.assertEqual(facts["op"], 140)
        self.assertEqual(facts["base"], 360)
        self.assertEqual(facts["employee"], 18)
        self.assertEqual(slip.get_salary_line_total("HEALTH"), -18)
        self.assertEqual(slip.get_salary_line_total("HEALTHEMPLOYER"), 55)

    def test_agreement_income_is_other_income_even_if_op_checkbox_is_set(self):
        contract, employee = self._make_dohodar(
            l10n_sk_agreement_type="dopc", l10n_sk_health_oop_claim=True
        )
        slip = self._make_payslip(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30)
        )
        facts = contract.l10n_sk_health_employee_assessment(
            1000, 5, slip.date_from, 380, 570
        )
        self.assertEqual(facts["op_income"], 0)
        self.assertEqual(facts["other_income"], 1000)
        self.assertEqual(facts["op"], 0)
        self.assertEqual(slip.get_salary_line_total("HEALTH"), -50)

    def test_pn_days_do_not_shrink_monthly_op_employment_ratio(self):
        contract, employee = self._make_low_earner(l10n_sk_health_oop_claim=True)
        slip = self._payslip_with_inputs(
            contract, employee, date(2026, 6, 1), date(2026, 6, 30), [("PN_DAYS", 10)]
        )
        facts = contract.l10n_sk_health_employee_assessment(
            slip.get_salary_line_total("GROSS"), 5, slip.date_from, 380, 570
        )
        self.assertEqual(facts["op"], 140)
        self.assertEqual(slip.get_salary_line_total("HEALTH"), -18)
