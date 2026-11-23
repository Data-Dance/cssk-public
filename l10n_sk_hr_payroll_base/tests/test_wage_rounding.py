# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import TransactionCase, tagged

from ..wage_rounding import round_wage_component


@tagged("post_install", "-at_install")
class TestWageRounding(TransactionCase):
    def test_any_fraction_of_a_cent_rounds_up(self):
        for amount, expected in (
            (2000.0 * 160 / 168, 1904.77),  # 1 904.7619
            (1000.0 * 128 / 176, 727.28),  # 727.2727
            (900.0 * 160 / 168, 857.15),  # 857.142857
            (8 * 11.5385, 92.31),  # 92.308
            (24 * 11.5385, 276.93),  # 276.924
            (727.2727272727, 727.28),
            (92.308, 92.31),
            (92.3000001, 92.31),
            (100.000000001, 100.01),
            (0.001, 0.01),
        ):
            with self.subTest(amount=amount):
                self.assertEqual(round_wage_component(amount), expected)

    def test_a_whole_cent_stays_that_cent(self):
        for amount, expected in (
            (0.0, 0.0),
            (2000.0, 2000.0),
            (1000, 1000.0),
            (857.14, 857.14),
            (2000.0 * 88 / 176, 1000.0),
            (0.1 + 0.2, 0.3),  # 0.30000000000000004
            (1.1 * 3, 3.3),  # 3.3000000000000003
            (4.35 * 100 / 100, 4.35),
            (1000.0000000001, 1000.0),
            (999.9999999999, 1000.0),
            (16764.0, 16764.0),
        ):
            with self.subTest(amount=amount):
                self.assertEqual(round_wage_component(amount), expected)

    def test_every_cent_amount_is_kept(self):
        for cents in range(0, 300000, 37):
            amount = cents / 100.0
            self.assertEqual(round_wage_component(amount), amount)
            self.assertEqual(round_wage_component(amount * 3 / 3), amount)

    def test_the_whole_is_rounded_once_not_its_parts(self):
        part = 2000.0 / 3  # 666.6667 on paper
        self.assertEqual(round_wage_component(part), 666.67)
        self.assertEqual(round_wage_component(part + part + part), 2000.0)
        self.assertEqual(round_wage_component(part * 3), 2000.0)

    def test_a_refund_mirrors_the_component(self):
        self.assertEqual(round_wage_component(-727.2727), -727.28)
        self.assertEqual(round_wage_component(-92.308), -92.31)
        self.assertEqual(round_wage_component(-1000.0), -1000.0)
        self.assertEqual(round_wage_component(-1000.0000000001), -1000.0)

    def test_payslip_rule_helper_uses_it(self):
        mixin = self.env["l10n.sk.payslip.fund.mixin"]
        self.assertEqual(mixin.l10n_sk_round_wage_component(92.308), 92.31)
        self.assertEqual(mixin.l10n_sk_round_wage_component(2000.0), 2000.0)
