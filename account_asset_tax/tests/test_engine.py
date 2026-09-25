"""Unit tests for the pure tax-depreciation engine.

These tests import only the engine (no Odoo), so they run both under Odoo's test
runner and standalone::

    python3 -m pytest account_asset_tax/tests/test_engine.py
    python3 account_asset_tax/tests/test_engine.py   # __main__ harness
"""
import unittest
from dataclasses import replace
from datetime import date

try:  # under Odoo
    from odoo.addons.account_asset_tax.engine import depreciation as eng
except Exception:  # standalone
    import os
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))
    import depreciation as eng


CZ2 = eng.TaxClass(
    country=eng.CZ, group_number=2, useful_life_years=5,
    linear_rate_first=11, linear_rate_next=22.25, linear_rate_increased=20,
    accel_coeff_first=5, accel_coeff_next=6, accel_coeff_increased=5,
)
SK1 = eng.TaxClass(country=eng.SK, group_number=1, useful_life_years=4)
SK2 = eng.TaxClass(
    country=eng.SK, group_number=2, useful_life_years=6,
    accel_coeff_first=6, accel_coeff_next=7, accel_coeff_increased=6,
)


def _total(lines):
    return round(sum(l.amount for l in lines), 2)


class TestEngine(unittest.TestCase):

    def test_cz_linear_full_first_year_no_proration(self):
        lines = eng.compute_schedule(eng.TaxAssetSpec(
            eng.CZ, eng.METHOD_LINEAR, 100000, date(2026, 3, 15), CZ2))
        self.assertEqual(len(lines), 5)
        # year 1 takes the full 11% regardless of March in-service
        self.assertAlmostEqual(lines[0].amount, 11000, places=2)
        self.assertAlmostEqual(lines[1].amount, 22250, places=2)
        self.assertEqual(_total(lines), 100000)
        self.assertAlmostEqual(lines[-1].residual, 0, places=2)

    def test_cz_linear_increased_first_year(self):
        # §31 +10 % for group 2: year 1 = 21 %, subsequent = 19.75 %
        spec = eng.TaxAssetSpec(eng.CZ, eng.METHOD_LINEAR, 100000,
                                date(2026, 1, 1), CZ2, increased_first_year=10)
        lines = eng.compute_schedule(spec)
        self.assertAlmostEqual(lines[0].amount, 21000, 2)
        self.assertAlmostEqual(lines[1].amount, 19750, 2)
        self.assertEqual(_total(lines), 100000)
        # +20 % for group 2: year 1 = 31 %
        spec20 = eng.TaxAssetSpec(eng.CZ, eng.METHOD_LINEAR, 100000,
                                  date(2026, 1, 1), CZ2, increased_first_year=20)
        l20 = eng.compute_schedule(spec20)
        self.assertAlmostEqual(l20[0].amount, 31000, 2)
        self.assertEqual(_total(l20), 100000)

    def test_vehicle_base_cap(self):
        # CZ §30e: 3,000,000 entry capped at 2,000,000 -> board on the cap
        spec = eng.TaxAssetSpec(eng.CZ, eng.METHOD_LINEAR, 3000000,
                                date(2026, 1, 1), CZ2, entry_cap=2000000)
        lines = eng.compute_schedule(spec)
        self.assertEqual(_total(lines), 2000000)
        self.assertAlmostEqual(lines[0].amount, 220000, 2)   # 11% of 2,000,000
        # cap above entry value has no effect
        spec2 = eng.TaxAssetSpec(eng.CZ, eng.METHOD_LINEAR, 100000,
                                 date(2026, 1, 1), CZ2, entry_cap=2000000)
        self.assertEqual(_total(eng.compute_schedule(spec2)), 100000)

    def test_cz_accelerated_known_series(self):
        lines = eng.compute_schedule(eng.TaxAssetSpec(
            eng.CZ, eng.METHOD_ACCELERATED, 100000, date(2026, 3, 15), CZ2))
        amounts = [round(l.amount, 2) for l in lines]
        self.assertEqual(amounts, [20000, 32000, 24000, 16000, 8000])
        self.assertEqual(_total(lines), 100000)

    def test_sk_linear_monthly_proration_and_remainder(self):
        # in service March => 10 months in year 1, remainder pushed to year 5
        lines = eng.compute_schedule(eng.TaxAssetSpec(
            eng.SK, eng.METHOD_LINEAR, 12000, date(2026, 3, 15), SK1))
        self.assertEqual(len(lines), 5)  # life 4 + remainder year
        self.assertAlmostEqual(lines[0].amount, 2500, places=2)   # 3000 * 10/12
        self.assertAlmostEqual(lines[1].amount, 3000, places=2)
        self.assertAlmostEqual(lines[-1].amount, 500, places=2)   # remainder
        self.assertEqual(lines[-1].note, "§27 first-year remainder")
        self.assertEqual(_total(lines), 12000)

    def test_sk_linear_january_no_remainder(self):
        lines = eng.compute_schedule(eng.TaxAssetSpec(
            eng.SK, eng.METHOD_LINEAR, 12000, date(2026, 1, 10), SK1))
        self.assertEqual(len(lines), 4)  # full first year, no remainder line
        self.assertAlmostEqual(lines[0].amount, 3000, places=2)
        self.assertEqual(_total(lines), 12000)

    def test_sk_accelerated_uses_full_first_year_residual(self):
        lines = eng.compute_schedule(eng.TaxAssetSpec(
            eng.SK, eng.METHOD_ACCELERATED, 60000, date(2026, 3, 15), SK2))
        # year 1 actual = (60000/6) * 10/12 = 8333.33
        self.assertAlmostEqual(lines[0].amount, 8333.33, places=2)
        # year 2 = 2 * (60000 - 10000) / (7 - 1) = 16666.67  (uses FULL 10000)
        self.assertAlmostEqual(lines[1].amount, 16666.67, places=2)
        self.assertEqual(lines[-1].note, "§28 first-year remainder")
        self.assertEqual(_total(lines), 60000)

    def test_cz_extraordinary_60_40_split(self):
        lines = eng.compute_schedule(eng.TaxAssetSpec(
            eng.CZ, eng.METHOD_EXTRAORDINARY, 600000, date(2026, 3, 15),
            CZ2, monthly=True))
        self.assertEqual(len(lines), 24)
        self.assertAlmostEqual(sum(l.amount for l in lines[:12]), 360000, places=2)
        self.assertAlmostEqual(sum(l.amount for l in lines[12:]), 240000, places=2)
        self.assertEqual(_total(lines), 600000)
        # starts the month AFTER in-service (March -> April)
        self.assertEqual(lines[0].date_from, date(2026, 4, 1))

    def test_unsupported_combination_raises(self):
        with self.assertRaises(ValueError):
            eng.compute_schedule(eng.TaxAssetSpec(
                eng.SK, eng.METHOD_EXTRAORDINARY, 1000, date(2026, 1, 1), SK1))

    def test_zero_value_empty_schedule(self):
        self.assertEqual(eng.compute_schedule(eng.TaxAssetSpec(
            eng.CZ, eng.METHOD_LINEAR, 0, date(2026, 1, 1), CZ2)), [])

    # --- lifecycle events ------------------------------------------------
    def test_cz_linear_technical_improvement(self):
        spec = eng.TaxAssetSpec(eng.CZ, eng.METHOD_LINEAR, 100000, date(2026, 1, 1), CZ2)
        imp = eng.apply_technical_improvement(eng.compute_schedule(spec), spec, 3, 50000)
        self.assertEqual(_total(imp), 150000)            # base + TZ
        self.assertAlmostEqual(imp[2].amount, 30000, places=2)  # 150000 * 20%
        self.assertAlmostEqual(imp[-1].residual, 0, places=2)

    def test_cz_accelerated_technical_improvement(self):
        spec = eng.TaxAssetSpec(eng.CZ, eng.METHOD_ACCELERATED, 100000, date(2026, 1, 1), CZ2)
        imp = eng.apply_technical_improvement(eng.compute_schedule(spec), spec, 3, 50000)
        self.assertEqual(_total(imp), 150000)
        # year of TZ: 2 * (48000 + 50000) / 5
        self.assertAlmostEqual(imp[2].amount, 39200, places=2)

    def test_sk_suspension_shifts_tail(self):
        spec = eng.TaxAssetSpec(eng.SK, eng.METHOD_LINEAR, 12000, date(2026, 1, 1), SK1)
        susp = eng.apply_suspension(eng.compute_schedule(spec), [2])
        self.assertEqual(_total(susp), 12000)
        self.assertEqual(susp[1].amount, 0.0)
        self.assertEqual(susp[1].note, "suspended")
        self.assertEqual(len(susp), 5)  # 4 charges + 1 gap year

    def test_cz_disposal_half_year(self):
        spec = eng.TaxAssetSpec(eng.CZ, eng.METHOD_LINEAR, 100000, date(2026, 1, 1), CZ2)
        disp, residual = eng.apply_disposal(eng.compute_schedule(spec), spec, date(2028, 6, 15))
        self.assertAlmostEqual(disp[-1].amount, 11125, places=2)   # half of 22250
        self.assertAlmostEqual(residual, 55625, places=2)
        self.assertEqual(disp[-1].fiscal_year, 2028)

    def test_sk_disposal_prorata(self):
        spec = eng.TaxAssetSpec(eng.SK, eng.METHOD_LINEAR, 12000, date(2026, 1, 1), SK1)
        disp, residual = eng.apply_disposal(eng.compute_schedule(spec), spec, date(2028, 4, 10))
        self.assertAlmostEqual(disp[-1].amount, 750, places=2)     # 3000 * 3/12
        self.assertAlmostEqual(residual, 5250, places=2)

    def test_extraordinary_improvement_rejected(self):
        # §30a(3): a TZ on an extraordinary asset is a separate asset, not folded
        spec = eng.TaxAssetSpec(eng.CZ, eng.METHOD_EXTRAORDINARY, 600000,
                                date(2026, 1, 1), CZ2, monthly=True)
        sched = eng.compute_schedule(spec)
        with self.assertRaises(ValueError):
            eng.apply_technical_improvement(sched, spec, 1, 100000)

    def test_improvement_after_suspension_no_duplicate_fiscal_years(self):
        # Fix 1: suspend year 2, TZ later — the rebuilt tail must continue the
        # (shifted) fiscal-year sequence: strictly increasing, no duplicates.
        spec = eng.TaxAssetSpec(eng.CZ, eng.METHOD_LINEAR, 100000, date(2026, 1, 1), CZ2)
        sched = eng.apply_suspension(eng.compute_schedule(spec), [2])
        yi = next(l.year_index for l in sched if l.fiscal_year == 2029)
        imp = eng.apply_technical_improvement(sched, spec, yi, 50000)
        fys = [l.fiscal_year for l in imp]
        self.assertEqual(fys, sorted(set(fys)),
                         "fiscal years must be strictly increasing, no duplicates")
        self.assertEqual(_total(imp), 150000)
        self.assertAlmostEqual(imp[-1].residual, 0, places=2)
        # suspension gap year survives the improvement replay
        self.assertEqual(next(l.amount for l in imp if l.fiscal_year == 2027), 0.0)

    def test_improvement_on_shifted_tail_derives_fy_from_prefix(self):
        # Fix 1 (direct): a board whose tail carries shifted fiscal years
        # WITHOUT re-indexed year_index (e.g. imported history where the
        # interruption was recorded as a plain gap year). Deriving start_fy
        # from the in-service year rebuilt the tail on stale years and
        # duplicated fiscal_year values.
        spec = eng.TaxAssetSpec(eng.CZ, eng.METHOD_LINEAR, 100000, date(2026, 1, 1), CZ2)
        sched = eng.compute_schedule(spec)
        shifted = [l if l.year_index < 2 else replace(l, fiscal_year=l.fiscal_year + 1)
                   for l in sched]
        imp = eng.apply_technical_improvement(shifted, spec, 3, 50000)
        fys = [l.fiscal_year for l in imp]
        self.assertEqual(len(fys), len(set(fys)), "no duplicate fiscal years")
        self.assertEqual(fys, sorted(fys))
        # tail continues right after the kept (shifted) prefix: 2026, 2028, 2029…
        self.assertEqual(fys[:3], [2026, 2028, 2029])
        self.assertEqual(_total(imp), 150000)

    def test_extraordinary_disposal_monthly(self):
        # Fix 4b: §30a monthly board disposed mid-schedule — depreciate through
        # the disposal MONTH; no half-year branch, rest of the board dropped.
        spec = eng.TaxAssetSpec(eng.CZ, eng.METHOD_EXTRAORDINARY, 600000,
                                date(2026, 3, 15), CZ2, monthly=True)
        sched = eng.compute_schedule(spec)   # Apr 2026 .. Mar 2028, 24 lines
        disp, residual = eng.apply_disposal(sched, spec, date(2027, 2, 10))
        # Apr–Dec 2026 (9) + Jan, Feb 2027 (2) = 11 monthly lines kept
        self.assertEqual(len(disp), 11)
        self.assertEqual(disp[-1].date_from, date(2027, 2, 1))
        self.assertEqual(disp[-1].fiscal_year, 2027)
        # each of the first 12 months carries 60%/12 = 30000 — NOT halved
        self.assertAlmostEqual(disp[-1].amount, 30000, places=2)
        self.assertAlmostEqual(sum(l.amount for l in disp), 330000, places=2)
        self.assertAlmostEqual(residual, 270000, places=2)
        self.assertAlmostEqual(disp[-1].residual, 270000, places=2)

    def test_sk_linear_float_noise_no_spurious_remainder(self):
        # Fix 5a: annual*12/12.0 != annual for some floats; the exact ==0.0 /
        # >0.0 tests then appended a spurious zero "remainder" line for a
        # January in-service asset (and skipped the last-line snap).
        value = 1000.8571428571429   # annual*12/12.0 differs from annual by ~3e-14
        lines = eng.compute_schedule(eng.TaxAssetSpec(
            eng.SK, eng.METHOD_LINEAR, value, date(2026, 1, 10), SK1))
        self.assertEqual(len(lines), 4)   # life 4, NO remainder line
        self.assertEqual(lines[-1].note, "§27")
        self.assertAlmostEqual(_total(lines), round(value, 2), places=2)
        self.assertAlmostEqual(lines[-1].residual, 0, places=6)

    def test_residual_at_cutoff_for_backfill(self):
        # the backfill wizard freezes years up to a cutoff and trusts the
        # statutory residual at that point — anchor it here
        spec = eng.TaxAssetSpec(eng.CZ, eng.METHOD_LINEAR, 100000, date(2024, 1, 1), CZ2)
        schedule = eng.compute_schedule(spec)
        residual_2025 = next(l.residual for l in schedule if l.fiscal_year == 2025)
        self.assertAlmostEqual(residual_2025, 66750, places=2)  # after Y1 11% + Y2 22.25%


if __name__ == "__main__":
    unittest.main(verbosity=2)
