# Copyright 2026 Data Dance s.r.o., votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from decimal import Decimal

from odoo.tests import BaseCase, tagged

from ..health_assessment import employee_assessment, minimum_assessment


@tagged("post_install", "-at_install")
class TestHealthAssessment(BaseCase):
    def test_minimum_floors_each_premium_before_prorating_the_sum(self):
        full = minimum_assessment(284.13, 5, 11, 30, 30, 5, 11)
        half = minimum_assessment(284.13, 5, 11, 15, 30, 5, 11)
        self.assertEqual(full["monthly_minimum"], Decimal("45.45"))
        self.assertEqual(full["topup"], Decimal("29.45"))
        self.assertEqual(half["minimum"], Decimal("22.72"))
        self.assertEqual(half["topup"], Decimal("6.72"))

    def test_one_irregular_day_has_only_one_day_of_minimum(self):
        facts = minimum_assessment(284.13, 5, 11, 1, 30, 0.05, 0.11)
        self.assertEqual(facts["minimum"], Decimal("1.51"))
        self.assertEqual(facts["topup"], Decimal("1.35"))

    def test_no_minimum_for_zero_days_or_written_optout(self):
        self.assertEqual(minimum_assessment(284.13, 5, 11, 0, 30, 5, 11)["topup"], 0)
        self.assertEqual(
            minimum_assessment(284.13, 5, 11, 30, 30, 5, 11, opt_out=True)["topup"], 0
        )

    def test_actual_premiums_above_minimum_do_not_become_a_refund(self):
        facts = minimum_assessment(284.13, 5, 11, 30, 30, 25, 55)
        self.assertEqual(facts["actual"], Decimal("80"))
        self.assertEqual(facts["topup"], 0)

    def test_minimum_rejects_impossible_day_counts_and_nonfinite_money(self):
        for days, month in [(-1, 30), (31, 30), (1.5, 30), (True, 30), (1, 27)]:
            with self.assertRaises(ValueError):
                minimum_assessment(284.13, 5, 11, days, month, 0, 0)
        with self.assertRaises(ValueError):
            minimum_assessment("NaN", 5, 11, 30, 30, 0, 0)

    def assess(self, income, op_income=None, **changes):
        values = dict(
            claim=True,
            employment_ratio=1,
            rate=5,
            maximum=380,
            phaseout_end=570,
            exempt=False,
        )
        values.update(changes)
        return employee_assessment(
            income, income if op_income is None else op_income, **values
        )

    def test_published_420_example_preserves_employer_income(self):
        facts = self.assess(420)
        self.assertEqual(facts["op"], Decimal("300.00"))
        self.assertEqual(facts["base"], Decimal("120.00"))
        self.assertEqual(facts["employee"], Decimal("6.00"))
        self.assertEqual(facts["income"], Decimal("420"))

    def test_low_income_and_partial_month_round_op_up_before_premium_down(self):
        facts = self.assess(160, employment_ratio=Decimal(16) / 31)
        self.assertEqual(facts["op"], Decimal("82.59"))
        self.assertEqual(facts["base"], Decimal("77.41"))
        self.assertEqual(facts["employee"], Decimal("3.87"))

    def test_monthly_phaseout_boundaries(self):
        for income, expected in [
            ("0", "0"),
            ("379.99", "379.99"),
            ("380", "380"),
            ("500", "140"),
            ("569.99", ".02"),
            ("570", "0"),
            ("1000", "0"),
        ]:
            with self.subTest(income=income):
                self.assertEqual(self.assess(income)["op"], Decimal(expected))

    def test_other_income_affects_phaseout_but_has_no_op_itself(self):
        facts = self.assess(600, 420)
        self.assertEqual(facts["op"], 0)
        self.assertEqual(facts["op_income"], 420)
        self.assertEqual(facts["other_income"], 180)
        self.assertEqual(facts["employee"], 30)
        self.assertEqual(self.assess(500, 0)["op"], 0)

    def test_unclaimed_op_keeps_eligible_income_classification(self):
        facts = self.assess(420, claim=False)
        self.assertEqual(facts["op_income"], 420)
        self.assertEqual(facts["other_income"], 0)
        self.assertEqual(facts["op"], 0)
        self.assertEqual(facts["employee"], 21)

    def test_reduced_rate_does_not_change_op_or_income(self):
        facts = self.assess(420, rate="2.5")
        self.assertEqual(facts["op"], 300)
        self.assertEqual(facts["base"], 120)
        self.assertEqual(facts["employee"], 3)

    def test_exemption_and_signed_refund_do_not_become_positive_premiums(self):
        facts = self.assess(500, exempt=True)
        self.assertEqual((facts["op"], facts["base"], facts["employee"]), (0, 0, 0))
        refund = self.assess(-500, claim=False)
        self.assertEqual(
            (refund["income"], refund["base"], refund["employee"]), (-500, -500, -25)
        )

    def test_dated_rate_and_parameter_change_is_not_hardcoded(self):
        self.assertEqual(self.assess(500, rate=4)["employee"], Decimal("14.40"))
        # Test parameters, not a claim that a future law has these values.
        self.assertEqual(self.assess(500, maximum=400, phaseout_end=600)["op"], 200)

    def test_cent_floor_is_not_mathematical_rounding(self):
        self.assertEqual(
            self.assess("100.39", claim=False)["employee"], Decimal("5.01")
        )
        self.assertEqual(self.assess(".01", claim=False)["employee"], 0)

    def test_invalid_profile_inputs_cannot_silently_be_clamped(self):
        for values in [
            dict(employment_ratio=-1),
            dict(employment_ratio=2),
            dict(rate=-1),
            dict(maximum=0),
            dict(phaseout_end=380),
            dict(rate="NaN"),
            dict(claim=1),
            dict(exempt=1),
        ]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                self.assess(500, **values)
        with self.assertRaises(ValueError):
            self.assess(100, 200)
