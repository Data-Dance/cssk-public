# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from itertools import permutations

from odoo.tests.common import BaseCase

from ..models.income_claims import exceeded_income_capacity


class TestDatedIncomeClaims(BaseCase):
    def claim(self, day, amount, capacity, key="income:1:1"):
        return {"key": key, "paid_on": day, "amount": amount, "capacity": capacity}

    def test_credit_capacity_is_checked_at_each_payment_date(self):
        early = self.claim("2026-05-10", 750, 1500)
        late = self.claim("2026-05-20", 750, 1350)
        for rows in permutations([early, late]):
            self.assertEqual(exceeded_income_capacity(rows, [])["paid_on"], "2026-05-20")
            self.assertIsNotNone(exceeded_income_capacity([rows[0]], [[[rows[1]]]]))

    def test_later_reversal_cannot_cure_an_earlier_overallocation(self):
        early = self.claim("2026-05-20", 1400, 1350)
        restored = self.claim("2026-05-26", 100, 1500)
        self.assertEqual(exceeded_income_capacity([early, restored], [])["paid_on"], "2026-05-20")
        self.assertIsNone(exceeded_income_capacity([
            self.claim("2026-05-20", 1300, 1350),
            self.claim("2026-05-26", 200, 1500),
        ], []))

    def test_complete_replacement_reserves_prefix_max_without_counting_twice(self):
        filed = [self.claim("2026-05-10", 700, 1500)]
        working = [self.claim("2026-06-20", 650, 1350)]
        current = [self.claim("2026-06-20", 650, 1350)]
        self.assertIsNone(exceeded_income_capacity(current, [[filed, working]]))
        self.assertIsNotNone(exceeded_income_capacity(current, [[filed], [working]]))
        current[0]["amount"] = 650.01
        self.assertIsNotNone(exceeded_income_capacity(current, [[filed, working]]))

    def test_other_pools_do_not_change_the_current_claim(self):
        current = [self.claim("2026-05-20", 1350, 1350)]
        unrelated = [self.claim("2026-05-20", 1500, 100, key="income:2:1")]
        self.assertIsNone(exceeded_income_capacity(current, [[unrelated]]))

    def test_legacy_claim_keeps_amount_without_inventing_historical_capacity(self):
        legacy = [self.claim("2026-05-20", 1500, None)]
        self.assertIsNone(exceeded_income_capacity(legacy, []))
        modern = [self.claim("2026-06-20", 100, 1500)]
        self.assertIsNotNone(exceeded_income_capacity(modern, [[legacy]]))

    def test_retained_timeline_bounds_a_future_legacy_claim(self):
        earlier = [self.claim("2026-05-10", 600, 1500)]
        legacy = [self.claim("2026-06-20", 750, None)]
        checkpoint = self.claim("2026-06-20", 0, 1350)
        self.assertIsNone(exceeded_income_capacity(earlier, [[legacy]], [checkpoint]))
        imported = [self.claim("2026-06-20", 50, None)]
        self.assertIsNotNone(exceeded_income_capacity(
            imported, [[earlier], [legacy]], [checkpoint],
        ))
