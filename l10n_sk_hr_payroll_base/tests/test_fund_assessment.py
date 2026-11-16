# Copyright 2026 Data Dance s.r.o., votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from decimal import Decimal, localcontext
import json

from odoo.tests import BaseCase, tagged

from ..fund_assessment import fund_assessment, index_assessments


@tagged("post_install", "-at_install")
class TestRecordedFundAssessment(BaseCase):
    def row(self, **changes):
        values = {
            "fund": "pension",
            "side": "employee",
            "base": "200",
            "rate": "4",
            "amount": "8",
        }
        values.update(changes)
        return fund_assessment(**values)

    def test_rounded_zero_premium_does_not_erase_its_real_base(self):
        row = self.row(base="0.06", amount=0)
        self.assertEqual((row["base"], row["amount"]), ("0.06", "0"))
        self.assertIn(("pension", "employee"), index_assessments([row]))
        self.assertNotIn(("pension", "employer"), index_assessments([row]))

    def test_health_employee_and_employer_retain_their_different_op_bases(self):
        employee = self.row(
            fund="health",
            base=360,
            rate=5,
            amount=18,
            facts={"income": 500, "op": 140, "topup": 0},
        )
        employer = self.row(
            fund="health", side="employer", base=500, rate=11, amount=55
        )
        rows = index_assessments([employee, employer])
        self.assertEqual(rows[("health", "employee")]["base"], "360")
        self.assertEqual(rows[("health", "employer")]["base"], "500")

    def test_minimum_topup_is_a_fact_not_an_invented_assessment_base(self):
        row = self.row(
            fund="health",
            base=100,
            rate=5,
            amount="34.45",
            facts={"regular_premium": 5, "topup": Decimal("29.45")},
        )
        self.assertEqual(
            (row["base"], row["rate"], row["amount"]), ("100", "5", "34.45")
        )
        self.assertEqual(row["facts"]["topup"], "29.45")

    def test_storage_preserves_precision_even_under_a_small_decimal_context(self):
        value = Decimal("123456789012345678901234567890.1234")
        with localcontext() as context:
            context.prec = 6
            row = self.row(base=value)
        self.assertEqual(row["base"], str(value))
        self.assertEqual(json.loads(json.dumps(row)), row)

    def test_negative_correction_keeps_actual_base_and_charge_signs(self):
        row = self.row(base="-200.123", amount="-8.0049")
        self.assertEqual((row["base"], row["amount"]), ("-200.123", "-8.0049"))
        self.assertEqual(index_assessments([row])[("pension", "employee")], row)

    def test_later_caller_edits_cannot_change_the_recorded_extra_facts(self):
        facts = {"periods": [{"month": "2026-06", "days": 30}]}
        row = self.row(facts=facts)
        facts["periods"][0]["days"] = 1
        self.assertEqual(row["facts"]["periods"][0]["days"], 30)

    def test_duplicate_fund_sides_do_not_silently_replace_a_prior_charge(self):
        with self.assertRaises(ValueError):
            index_assessments([self.row(), self.row(base=300, amount=12)])

    def test_missing_fields_and_unknown_top_level_facts_are_not_accepted(self):
        for change in ("remove_amount", "extra_currency"):
            row = self.row()
            if change == "remove_amount":
                del row["amount"]
            else:
                row["currency"] = "EUR"
            with self.subTest(change=change), self.assertRaises(ValueError):
                index_assessments([row])

    def test_invalid_money_percentages_and_sides_cannot_enter_the_snapshot(self):
        cases = [
            {"rate": -1},
            {"rate": 101},
            {"amount": "NaN"},
            {"base": "Infinity"},
            {"rate": True},
            {"fund": " health"},
            {"side": "Employee"},
            {"side": []},
            {"facts": {"bad": float("inf")}},
            {"facts": {1: "not a JSON key"}},
        ]
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.row(**changes)
