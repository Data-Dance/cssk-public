# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Unit tests for the pure-Python garnishment allocator.

No database is touched: the allocator is deliberately Odoo-free so the legal
rules can be pinned down here, in isolation from the payroll engines.
"""

import unittest

# TransactionCase, not a bare unittest.TestCase: Odoo's loader only collects
# classes carrying its test tags, so plain unittest classes are silently
# skipped by ``--test-enable``. These tests never touch the cursor.
from odoo.tests import TransactionCase

from odoo.addons.l10n_cssk_hr_payroll_garnishment_base.models.garnishment_calc import (
    CLASS_FINE,
    CLASS_MAINTENANCE,
    CLASS_ORDINARY,
    CLASS_PRIORITY,
    Claim,
    compute_cz,
    compute_sk,
    cz_protected_amount,
    sk_protected_amount,
)

# 2026 figures, NV 595/2006 Sb.: 4 860 + 9 430 + 2 300 = 16 590 Kč.
CZ_RATES = {
    "subsistence": 4860.0,
    "normative_rent": 9430.0,
    "energy": 2300.0,
    "base_pct": 85.0,
    "dependent_fraction": 0.25,
    "unlimited_limit": 31521.0,
}

# ŽM 284.13 € valid 1.7.2025 – 30.6.2026, NV 268/2006 Z. z.
SK_RATES = {
    "zivotne_minimum": 284.13,
    "basic_coeff": 1.40,
    "priority_coeff": 1.00,
    "maintenance_outer_coeff": 0.70,
    "maintenance_inner_coeff": 0.60,
    "fine_coeff": 0.50,
    "dependent_coeff": 0.25,
    "dependent_coeff_pensioner": 0.50,
    "unlimited_mult": 3.0,
}


def _claim(key, claim_class, day, due, monthly=0.0, seq=10):
    return Claim(key, claim_class, (day, seq, key), due, monthly)


class TestCzechAllocator(TransactionCase):
    def test_protected_amount(self):
        """85 % of the three-component sum, plus a quarter per dependent,
        rounded up to whole crowns as a total (NV 595/2006 § 3)."""
        self.assertEqual(cz_protected_amount(CZ_RATES, 0), 14102)  # 14 101,50
        # 14 101,50 + 2 × 3 525,375 = 21 152,25 → 21 153
        self.assertEqual(cz_protected_amount(CZ_RATES, 2), 21153)

    def test_below_protected_amount_deducts_nothing(self):
        result = compute_cz(
            12000.0, CZ_RATES, 0, [_claim(1, CLASS_ORDINARY, "2026-01-10", 50000.0)]
        )
        self.assertEqual(result.total, 0.0)

    def test_single_ordinary_claim_takes_one_third(self):
        # zbytek 39 270 − 14 102 = 25 168 → down to 25 167 (divisible by 3)
        # → third = 8 389; the 1 Kč rounding remainder stays with the employee.
        result = compute_cz(
            39270.0, CZ_RATES, 0, [_claim(1, CLASS_ORDINARY, "2026-01-10", 50000.0)]
        )
        self.assertEqual(result.third, 8389.0)
        self.assertEqual(result.allocations[1], 8389.0)

    def test_single_priority_claim_takes_two_thirds(self):
        result = compute_cz(
            39270.0, CZ_RATES, 0, [_claim(1, CLASS_PRIORITY, "2026-01-10", 50000.0)]
        )
        self.assertEqual(result.allocations[1], 16778.0)

    def test_claim_capped_by_outstanding_debt(self):
        result = compute_cz(
            39270.0, CZ_RATES, 0, [_claim(1, CLASS_PRIORITY, "2026-01-10", 500.0)]
        )
        self.assertEqual(result.allocations[1], 500.0)

    def test_above_limit_ordinary_gets_the_fully_seizable_part(self):
        """With no priority claim in sight, the whole above-limit part joins
        the first third (official methodology, exekuce.justice.cz)."""
        # zbytek 60 000 − 14 102 = 45 898; limit 31 521 → unlimited 14 377,
        # third 10 507.
        result = compute_cz(
            60000.0, CZ_RATES, 0, [_claim(1, CLASS_ORDINARY, "2026-01-10", 90000.0)]
        )
        self.assertEqual(result.unlimited, 14377.0)
        self.assertEqual(result.allocations[1], 10507.0 + 14377.0)

    def test_above_limit_priority_gets_two_thirds_plus_unlimited(self):
        result = compute_cz(
            60000.0, CZ_RATES, 0, [_claim(1, CLASS_PRIORITY, "2026-01-10", 90000.0)]
        )
        self.assertEqual(result.allocations[1], 2 * 10507.0 + 14377.0)

    def test_waterfall_across_three_claims(self):
        """§ 279(1) + § 280: maintenance first out of the second third, other
        priority next, then everyone competes in the first third by pořadí."""
        claims = [
            _claim(1, CLASS_MAINTENANCE, "2026-01-10", 5000.0, monthly=5000.0),
            _claim(2, CLASS_PRIORITY, "2026-02-01", 10000.0),
            _claim(3, CLASS_ORDINARY, "2025-06-01", 10000.0),
        ]
        result = compute_cz(39270.0, CZ_RATES, 0, claims)
        # second third (8 389): maintenance 5 000, then priority 3 389
        self.assertEqual(result.allocations[1], 5000.0)
        self.assertEqual(result.allocations[2], 3389.0)
        # first third (8 389) goes entirely to the oldest rank — the ordinary
        # claim delivered in June 2025 — even though it is not preferential.
        self.assertEqual(result.allocations[3], 8389.0)
        self.assertEqual(result.total, 16778.0)

    def test_second_third_leftover_stays_with_the_employee(self):
        """§ 279(1): what the priority claims do not use is NOT handed to the
        ordinary claims — it goes back to the debtor."""
        claims = [
            _claim(1, CLASS_PRIORITY, "2026-01-10", 1000.0),
            _claim(2, CLASS_ORDINARY, "2026-02-01", 50000.0),
        ]
        result = compute_cz(39270.0, CZ_RATES, 0, claims)
        self.assertEqual(result.allocations[1], 1000.0)
        self.assertEqual(result.allocations[2], 8389.0)  # first third only
        self.assertEqual(result.total, 9389.0)

    def test_maintenance_shares_second_third_pro_rata(self):
        """§ 280(2): split by CURRENT maintenance, disregarding arrears."""
        claims = [
            _claim(1, CLASS_MAINTENANCE, "2026-01-10", 20000.0, monthly=6000.0),
            _claim(2, CLASS_MAINTENANCE, "2026-03-01", 20000.0, monthly=4000.0),
        ]
        result = compute_cz(39270.0, CZ_RATES, 0, claims)
        # The second third (8 389) splits 60/40 by current maintenance — the
        # arrears (due ≫ monthly) do not shift the ratio.
        self.assertEqual(result.breakdown[1]["second"], 5033.0)
        self.assertEqual(result.breakdown[2]["second"], 3356.0)
        self.assertEqual(
            result.breakdown[1]["second"] + result.breakdown[2]["second"], 8389.0
        )
        # Both are still owed money, so they carry on into the first third by
        # pořadí (§ 280(1)) — the January claim ranks first and takes it all.
        self.assertEqual(result.breakdown[1]["first"], 8389.0)
        self.assertEqual(result.breakdown[2]["first"], 0.0)
        self.assertEqual(result.total, 16778.0)

    def test_equal_rank_shares_first_third_pro_rata(self):
        """§ 280(3): same delivery day → equal rank → proportional split."""
        claims = [
            _claim(1, CLASS_ORDINARY, "2026-01-10", 30000.0),
            _claim(2, CLASS_ORDINARY, "2026-01-10", 10000.0),
        ]
        result = compute_cz(39270.0, CZ_RATES, 0, claims)
        self.assertEqual(result.total, 8389.0)
        self.assertAlmostEqual(result.allocations[1], 6292.0, delta=1.0)
        self.assertAlmostEqual(result.allocations[2], 2097.0, delta=1.0)

    def test_dependents_raise_the_protected_amount(self):
        no_deps = compute_cz(
            39270.0, CZ_RATES, 0, [_claim(1, CLASS_ORDINARY, "2026-01-10", 50000.0)]
        )
        with_deps = compute_cz(
            39270.0, CZ_RATES, 2, [_claim(1, CLASS_ORDINARY, "2026-01-10", 50000.0)]
        )
        self.assertLess(with_deps.total, no_deps.total)
        self.assertEqual(with_deps.protected, 21153)

    def test_never_deducts_more_than_two_thirds(self):
        claims = [
            _claim(1, CLASS_MAINTENANCE, "2026-01-10", 999999.0, monthly=999999.0),
            _claim(2, CLASS_PRIORITY, "2026-01-11", 999999.0),
            _claim(3, CLASS_ORDINARY, "2026-01-12", 999999.0),
        ]
        result = compute_cz(39270.0, CZ_RATES, 0, claims)
        self.assertEqual(result.total, 2 * result.third)


class TestSlovakAllocator(TransactionCase):
    def test_protected_amounts_per_claim_class(self):
        """NV 268/2006: a priority creditor may reach deeper than an ordinary
        one, and maintenance for a minor deeper still."""
        self.assertAlmostEqual(
            sk_protected_amount(SK_RATES, 0, CLASS_ORDINARY), 397.78, places=2
        )
        self.assertAlmostEqual(
            sk_protected_amount(SK_RATES, 0, CLASS_PRIORITY), 284.13, places=2
        )
        # 70 % of 60 % of 284,13 = 119,33
        self.assertAlmostEqual(
            sk_protected_amount(SK_RATES, 0, CLASS_MAINTENANCE), 119.33, places=2
        )
        self.assertAlmostEqual(
            sk_protected_amount(SK_RATES, 0, CLASS_FINE), 142.07, places=2
        )

    def test_dependants_and_pensioner_coefficient(self):
        # ordinary + 1 dependant = 397,78 + 25 % = 397,78 + 99,45
        self.assertAlmostEqual(
            sk_protected_amount(SK_RATES, 1, CLASS_ORDINARY), 497.23, places=2
        )
        # a pension recipient gets 50 % per dependant instead of 25 %
        self.assertAlmostEqual(
            sk_protected_amount(SK_RATES, 1, CLASS_ORDINARY, is_pensioner=True),
            397.78 + 198.89,
            places=2,
        )

    def test_ordinary_claim_takes_one_third(self):
        # 693,36 − 397,78 = 295,58 → down to 295,56 → third 98,52
        result = compute_sk(
            693.36, SK_RATES, 0, [_claim(1, CLASS_ORDINARY, "2026-01-10", 500.0)]
        )
        self.assertAlmostEqual(result.allocations[1], 98.52, places=2)

    def test_priority_claim_uses_the_deeper_base(self):
        """The bug this module fixes: a priority claim is computed on 100 % ŽM,
        not on the 140 % ordinary base."""
        # 693,36 − 284,13 = 409,23 (divisible by 3) → third 136,41 → 2/3 = 272,82
        result = compute_sk(
            693.36, SK_RATES, 0, [_claim(1, CLASS_PRIORITY, "2026-01-10", 500.0)]
        )
        self.assertAlmostEqual(result.allocations[1], 272.82, places=2)

    def test_claim_capped_by_debt(self):
        result = compute_sk(
            693.36, SK_RATES, 0, [_claim(1, CLASS_PRIORITY, "2026-01-10", 50.0)]
        )
        self.assertAlmostEqual(result.allocations[1], 50.0, places=2)

    def test_above_threshold_is_seized_without_limit(self):
        # threshold = 3 × 397,78 = 1 193,34
        result = compute_sk(
            3000.0, SK_RATES, 0, [_claim(1, CLASS_ORDINARY, "2026-01-10", 99999.0)]
        )
        rest = 3000.0 - 397.78  # 2 602,22
        over = rest - 1193.34  # 1 408,88
        third = 1193.34 / 3.0
        self.assertAlmostEqual(result.allocations[1], third + over, delta=0.03)

    def test_maintenance_before_other_priority(self):
        claims = [
            _claim(1, CLASS_MAINTENANCE, "2026-03-01", 200.0, monthly=200.0),
            _claim(2, CLASS_PRIORITY, "2026-01-01", 500.0),
        ]
        result = compute_sk(900.0, SK_RATES, 0, claims)
        # maintenance is satisfied first even though it ranks later
        self.assertAlmostEqual(result.allocations[1], 200.0, places=2)
        self.assertGreater(result.allocations[2], 0.0)

    def test_employee_always_keeps_the_smallest_applicable_base(self):
        claims = [
            _claim(1, CLASS_MAINTENANCE, "2026-01-01", 99999.0, monthly=99999.0),
            _claim(2, CLASS_PRIORITY, "2026-01-02", 99999.0),
            _claim(3, CLASS_ORDINARY, "2026-01-03", 99999.0),
        ]
        result = compute_sk(900.0, SK_RATES, 0, claims)
        floor = sk_protected_amount(SK_RATES, 0, CLASS_MAINTENANCE)
        self.assertLessEqual(result.total, 900.0 - floor + 0.01)

    def test_no_claims_deducts_nothing(self):
        result = compute_sk(2000.0, SK_RATES, 0, [])
        self.assertEqual(result.total, 0.0)


class TestAllocatorInvariants(TransactionCase):
    """Randomised property tests.

    Seeded, so a failure is reproducible. These guard the properties that are
    easy to break with a plausible-looking rounding change: allocations that
    creep past a third, past a claim's outstanding balance, or below the
    amount the debtor may not be deprived of.
    """

    CASES = 4000
    SEED = 20260727

    def _random_claims(self, rnd, classes):
        claims = []
        for key in range(rnd.randint(0, 5)):
            day = "2026-%02d-%02d" % (rnd.randint(1, 12), rnd.randint(1, 28))
            due = rnd.choice(
                [0.0, 1.0, 37.5, 500.0, 5000.0, 100000.0, rnd.uniform(0, 90000)]
            )
            claims.append(
                Claim(
                    key,
                    rnd.choice(classes),
                    (day, rnd.randint(0, 3), key),
                    due,
                    rnd.choice([0.0, due / 2, rnd.uniform(0, 5000)]),
                )
            )
        return claims

    def test_czech_invariants(self):
        import random

        rnd = random.Random(self.SEED)
        classes = [CLASS_MAINTENANCE, CLASS_PRIORITY, CLASS_ORDINARY]
        for _i in range(self.CASES):
            deps = rnd.randint(0, 4)
            claims = self._random_claims(rnd, classes)
            net = rnd.choice(
                [0.0, 5000.0, 14102.0, 39270.0, 60000.0, rnd.uniform(0, 200000)]
            )
            r = compute_cz(net, CZ_RATES, deps, claims)
            ctx = "net=%s deps=%s claims=%s" % (net, deps, claims)
            for c in claims:
                got = r.allocations.get(c.key, 0.0)
                self.assertLessEqual(got, c.due + 1e-6, ctx)
                self.assertGreaterEqual(got, 0.0, ctx)
                self.assertAlmostEqual(
                    sum(r.breakdown.get(c.key, {}).values()), got, places=6, msg=ctx
                )
            # Never more than two thirds plus the fully seizable part…
            self.assertLessEqual(r.total, 2 * r.third + r.unlimited + 1e-6, ctx)
            # …and the debtor keeps the non-attachable amount whenever
            # anything at all is deducted.
            if r.total > 0:
                self.assertGreaterEqual(net - r.total, r.protected - 1e-6, ctx)
            # Ordinary claims may only draw on the first third.
            ordinary = sum(
                r.allocations.get(c.key, 0.0)
                for c in claims
                if c.claim_class == CLASS_ORDINARY
            )
            self.assertLessEqual(ordinary, r.detail.get("first_pool", 0.0) + 1e-6, ctx)

    def test_slovak_invariants(self):
        import random

        rnd = random.Random(self.SEED + 1)
        classes = [CLASS_MAINTENANCE, CLASS_PRIORITY, CLASS_FINE, CLASS_ORDINARY]
        for _i in range(self.CASES):
            deps = rnd.randint(0, 4)
            pensioner = bool(rnd.getrandbits(1))
            claims = self._random_claims(rnd, classes)
            net = rnd.choice([0.0, 300.0, 693.36, 1000.0, 3000.0, rnd.uniform(0, 9000)])
            r = compute_sk(net, SK_RATES, deps, claims, is_pensioner=pensioner)
            ctx = "net=%s deps=%s pensioner=%s" % (net, deps, pensioner)
            for c in claims:
                got = r.allocations.get(c.key, 0.0)
                self.assertLessEqual(got, c.due + 1e-6, ctx)
                self.assertGreaterEqual(got, 0.0, ctx)
            used = {
                c.claim_class
                for c in claims
                if r.allocations.get(c.key, 0.0) > 1e-9
            }
            if used:
                floor = min(r.detail["bases"][cls] for cls in used)
                self.assertGreaterEqual(net - r.total, floor - 1e-6, ctx)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
