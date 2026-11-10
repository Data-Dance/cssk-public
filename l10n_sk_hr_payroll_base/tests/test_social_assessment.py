# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import TransactionCase, tagged

from ..social_assessment import assessment_base


@tagged("post_install", "-at_install")
class TestSocialAssessment(TransactionCase):
    def test_agreement_deduction_precedes_ceiling(self):
        self.assertEqual(assessment_base(25000, 16764, 200), 16764)
        self.assertEqual(assessment_base(16900, 16764, 200), 16700)
        self.assertEqual(assessment_base(25000, 17820, 300), 17820)

    def test_uncapped_accident_and_guarantee_without_oop(self):
        self.assertEqual(assessment_base(25000), 25000)
        self.assertEqual(assessment_base(25000, 16764), 16764)

    def test_zero_low_income_and_floor(self):
        self.assertEqual(assessment_base(0, 16764, 200), 0)
        self.assertEqual(assessment_base(100, 16764, 200), 0)
        self.assertEqual(assessment_base(350, 16764, 200), 150)
        self.assertEqual(assessment_base("500.009", 16764), 500)

    def test_invalid_inputs(self):
        for gross, cap, oop in (
            (float("nan"), 1, 0),
            (1, float("inf"), 0),
            (1, 1, -1),
            (1, -1, 0),
        ):
            with self.assertRaises(ValueError):
                assessment_base(gross, cap, oop)
