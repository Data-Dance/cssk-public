# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import TransactionCase, tagged

from ..meal_days import count_meal_days, shift_earns_meal, whole_days


@tagged("post_install", "-at_install")
class TestMealDays(TransactionCase):
    def test_more_than_four_hours_earn_a_meal(self):
        for hours, expected in (
            (0.0, False),
            (4.0, False),  # exactly four hours is not more than four
            (4.01, True),
            (5.0, True),
            (8.0, True),
            (12.0, True),  # one meal: the second is the employer's option
            (-8.0, False),
        ):
            with self.subTest(hours=hours):
                self.assertIs(shift_earns_meal(hours, 4.0), expected)

    def test_binary_noise_around_four_hours_is_four_hours(self):
        for hours in (
            3.9999999999,
            4.0000000001,
            8.0 - 4.0,
            0.1 * 40,
            1.1 + 2.9,
            4.4 - 0.4,
            2.2 + 1.8,
            8.0 - 3.7 - 0.3,
        ):
            with self.subTest(hours=hours):
                self.assertFalse(shift_earns_meal(hours, 4.0))
        # A minute over is over.
        self.assertTrue(shift_earns_meal(4.0 + 1 / 60, 4.0))

    def test_each_day_is_decided_alone(self):
        # Two half days do not add up to a meal day.
        self.assertEqual(count_meal_days([4.0, 4.0], 4.0), 0.0)
        self.assertEqual(count_meal_days([8.0, 4.0, 6.0, 0.0, 5.0], 4.0), 3.0)
        self.assertEqual(count_meal_days([], 4.0), 0.0)
        # Twenty-one days of eight hours and one of four.
        self.assertEqual(count_meal_days([8.0] * 21 + [4.0], 4.0), 21.0)
        # A schedule of four hours a day earns none.
        self.assertEqual(count_meal_days([4.0] * 22, 4.0), 0.0)

    def test_the_threshold_is_an_argument(self):
        self.assertEqual(count_meal_days([4.0, 5.0, 6.0], 5.0), 1.0)

    def test_any_work_earns_the_meal_of_an_employer_who_gives_more(self):
        # § 152 ods. 9: the meal also for a shift of four hours or less.
        for hours, expected in (
            (0.0, False),  # a day of leave or a public holiday
            (0.0000000001, False),  # noise is not work
            (-4.0, False),
            (0.5, True),
            (4.0, True),
            (3.9999999999, True),
            (8.0, True),
        ):
            with self.subTest(hours=hours):
                self.assertIs(shift_earns_meal(hours, 4.0, any_work=True), expected)
        # Without it nothing changes.
        self.assertFalse(shift_earns_meal(4.0, 4.0, any_work=False))
        self.assertEqual(count_meal_days([4.0] * 22, 4.0, any_work=True), 22.0)
        self.assertEqual(count_meal_days([8.0] * 21 + [4.0], 4.0, any_work=True), 22.0)
        self.assertEqual(count_meal_days([8.0] * 21 + [0.0], 4.0, any_work=True), 21.0)
        # Still one meal a day, whatever the hours.
        self.assertEqual(count_meal_days([12.0, 2.0], 4.0, any_work=True), 2.0)

    def test_whole_days_of_typed_worked_day_lines(self):
        for days, expected in (
            (22.0, 22.0),
            (16.5, 16.0),
            (21.75, 21.0),
            (20.999999999, 21.0),
            (21.000000001, 21.0),
            (0.5, 0.0),
            (0.0, 0.0),
            (-3.0, 0.0),
        ):
            with self.subTest(days=days):
                self.assertEqual(whole_days(days), expected)
