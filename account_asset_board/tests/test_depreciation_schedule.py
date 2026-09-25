# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Tests for account.asset.get_schedule() (dynamic depreciation schedule)."""

from datetime import date

from odoo import fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestDepreciationSchedule(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.asset_model = cls.env["account.asset"]
        cls.profile_model = cls.env["account.asset.profile"]

        def make_profile(name, years, company_data=None):
            company_data = company_data or cls.company_data
            return cls.profile_model.create(
                {
                    "name": name,
                    "account_expense_depreciation_id": company_data[
                        "default_account_expense"
                    ].id,
                    "account_asset_id": company_data["default_account_assets"].id,
                    "account_depreciation_id": company_data[
                        "default_account_assets"
                    ].id,
                    "journal_id": company_data["default_journal_purchase"].id,
                    "method_time": "year",
                    "method_number": years,
                    "method_period": "year",
                    "company_id": company_data["company"].id,
                }
            )

        cls.make_profile = staticmethod(make_profile)
        cls.profile_it = make_profile("Board IT 5Y", 5)
        cls.profile_car = make_profile("Board Cars 4Y", 4)

        def make_asset(name, profile, value, date_start, validate=True):
            asset = cls.asset_model.create(
                {
                    "name": name,
                    "profile_id": profile.id,
                    "purchase_value": value,
                    "salvage_value": 0,
                    "date_start": date_start,
                    "method_time": "year",
                    "method_number": profile.method_number,
                    "method_period": "year",
                    "prorata": False,
                    "company_id": profile.company_id.id,
                }
            )
            asset.compute_depreciation_board()
            if validate:
                asset.validate()
            return asset

        cls.make_asset = staticmethod(make_asset)
        # 1500 over 5 years from 2024 -> 300/year at each fiscal-year end
        cls.asset1 = make_asset("Board Server", cls.profile_it, 1500, "2024-01-01")
        # 4000 over 4 years from 2025 -> 1000/year
        cls.asset2 = make_asset("Board Car", cls.profile_car, 4000, "2025-01-01")

    # -- helpers ------------------------------------------------------------

    def _expected(self, asset, date_from, date_to):
        """Independently compute expected sums from the asset board lines."""
        lines = asset.depreciation_line_ids.filtered(
            lambda line: line.type == "depreciate"
        )
        date_from = fields.Date.to_date(date_from)
        date_to = fields.Date.to_date(date_to)
        opening = sum(lines.filtered(lambda l: l.line_date < date_from).mapped("amount"))
        period = sum(
            lines.filtered(
                lambda l: date_from <= l.line_date <= date_to
            ).mapped("amount")
        )
        return opening, period

    def _row(self, schedule, asset):
        for group in schedule["groups"]:
            for row in group["assets"]:
                if row["id"] == asset.id:
                    return group, row
        return None, None

    def _get_schedule(self, date_from, date_to, company=None):
        model = self.asset_model
        if company:
            model = model.with_company(company)
        return model.get_schedule(date_from=date_from, date_to=date_to)

    # -- tests --------------------------------------------------------------

    def test_01_math_two_windows(self):
        """Opening / period / closing / residual at two different windows."""
        for date_from, date_to in (
            ("2025-01-01", "2025-12-31"),
            ("2024-01-01", "2026-12-31"),
        ):
            schedule = self._get_schedule(date_from, date_to)
            self.assertEqual(schedule["date_from"], date_from)
            self.assertEqual(schedule["date_to"], date_to)
            for asset in self.asset1 | self.asset2:
                opening, period = self._expected(asset, date_from, date_to)
                group, row = self._row(schedule, asset)
                self.assertTrue(row, f"{asset.name} missing in {date_from}..{date_to}")
                self.assertEqual(group["profile_id"], asset.profile_id.id)
                self.assertAlmostEqual(row["acquisition_value"], asset.purchase_value)
                self.assertAlmostEqual(row["opening_depreciated"], opening, places=2)
                self.assertAlmostEqual(row["period_depreciation"], period, places=2)
                self.assertAlmostEqual(row["disposal"], 0.0, places=2)
                self.assertAlmostEqual(
                    row["closing_depreciated"], opening + period, places=2
                )
                self.assertAlmostEqual(
                    row["residual"],
                    asset.depreciation_base - opening - period,
                    places=2,
                )
        # sanity of the known board: full 2024-2028 window depreciates all
        schedule = self._get_schedule("2024-01-01", "2028-12-31")
        _group, row = self._row(schedule, self.asset1)
        self.assertAlmostEqual(row["opening_depreciated"], 0.0, places=2)
        self.assertAlmostEqual(row["period_depreciation"], 1500.0, places=2)
        self.assertAlmostEqual(row["residual"], 0.0, places=2)

    def test_02_grouping_and_totals(self):
        """One group per profile; group and grand totals add up."""
        schedule = self._get_schedule("2025-01-01", "2025-12-31")
        profile_ids = [g["profile_id"] for g in schedule["groups"]]
        self.assertIn(self.profile_it.id, profile_ids)
        self.assertIn(self.profile_car.id, profile_ids)
        self.assertEqual(len(profile_ids), len(set(profile_ids)))
        keys = (
            "acquisition_value",
            "opening_depreciated",
            "period_depreciation",
            "disposal",
            "closing_depreciated",
            "residual",
        )
        for group in schedule["groups"]:
            for key in keys:
                self.assertAlmostEqual(
                    group["totals"][key],
                    sum(row[key] for row in group["assets"]),
                    places=2,
                    msg=f"group subtotal {key}",
                )
        for key in keys:
            self.assertAlmostEqual(
                schedule["totals"][key],
                sum(g["totals"][key] for g in schedule["groups"]),
                places=2,
                msg=f"grand total {key}",
            )

    def test_03_window_scope(self):
        """Assets outside the window are excluded."""
        # asset2 starts 2025 -> absent from a 2024 window
        schedule = self._get_schedule("2024-01-01", "2024-12-31")
        _group, row = self._row(schedule, self.asset2)
        self.assertFalse(row)
        _group, row = self._row(schedule, self.asset1)
        self.assertTrue(row)
        # draft assets never show
        draft = self.make_asset(
            "Board Draft", self.profile_it, 999, "2024-01-01", validate=False
        )
        schedule = self._get_schedule("2024-01-01", "2025-12-31")
        _group, row = self._row(schedule, draft)
        self.assertFalse(row)

    def test_04_disposal(self):
        """Removed asset: written-off residual in the disposal column."""
        asset = self.make_asset("Board Disposed", self.profile_it, 1000, "2024-01-01")
        # OCA's removal wizard refuses early removal while depreciation lines
        # of previous periods are unposted — post them first.
        asset.depreciation_line_ids.filtered(
            lambda l: l.type == "depreciate" and not l.move_id
            and l.line_date < date(2025, 6, 30)
        ).create_move()
        wiz = (
            self.env["account.asset.remove"]
            .with_context(active_id=asset.id, early_removal=True)
            .create(
                {
                    "date_remove": "2025-06-30",
                    "sale_value": 0.0,
                    "posting_regime": "gain_loss_on_sale",
                    "account_plus_value_id": self.company_data[
                        "default_account_revenue"
                    ].id,
                    "account_min_value_id": self.company_data[
                        "default_account_expense"
                    ].id,
                }
            )
        )
        wiz.remove()
        asset.invalidate_recordset()
        self.assertEqual(asset.state, "removed")
        remove_amount = sum(
            asset.depreciation_line_ids.filtered(
                lambda l: l.type == "remove"
            ).mapped("amount")
        )
        self.assertGreater(remove_amount, 0.0)

        schedule = self._get_schedule("2025-01-01", "2025-12-31")
        _group, row = self._row(schedule, asset)
        self.assertTrue(row)
        self.assertAlmostEqual(row["disposal"], remove_amount, places=2)
        self.assertAlmostEqual(row["residual"], 0.0, places=2)
        self.assertAlmostEqual(
            row["closing_depreciated"] + row["disposal"],
            asset.depreciation_base,
            places=2,
        )
        # removed before the window -> excluded
        schedule = self._get_schedule("2026-01-01", "2026-12-31")
        _group, row = self._row(schedule, asset)
        self.assertFalse(row)

    def test_05_company_isolation(self):
        """get_schedule only reports assets of env.company."""
        other = self.setup_other_company()
        other_profile = self.make_profile("Board Other 5Y", 5, company_data=other)
        other_asset = self.make_asset(
            "Board Other Asset", other_profile, 2500, "2024-01-01"
        )
        # company 1: no company-2 asset
        schedule = self._get_schedule("2024-01-01", "2025-12-31")
        _group, row = self._row(schedule, other_asset)
        self.assertFalse(row)
        _group, row = self._row(schedule, self.asset1)
        self.assertTrue(row)
        # company 2: only its own asset
        schedule = self._get_schedule(
            "2024-01-01", "2025-12-31", company=other["company"]
        )
        _group, row = self._row(schedule, other_asset)
        self.assertTrue(row)
        _group, row = self._row(schedule, self.asset1)
        self.assertFalse(row)

    def test_06_default_window_is_fiscal_year(self):
        """No dates -> current fiscal year of env.company."""
        fy = self.env.company.compute_fiscalyear_dates(
            fields.Date.context_today(self.asset_model)
        )
        schedule = self.asset_model.get_schedule()
        self.assertEqual(schedule["date_from"], fields.Date.to_string(fy["date_from"]))
        self.assertEqual(schedule["date_to"], fields.Date.to_string(fy["date_to"]))
