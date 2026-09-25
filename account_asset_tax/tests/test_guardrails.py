"""Guardrail regression tests for the tax-depreciation mixin / wizards.

These need a concrete ``account.asset`` carrying the tax mixin, so they are
edition-agnostic: they detect whether the EE (``account_asset``) or the OCA
(``account_asset_management``) bridge is installed and build the asset with the
matching fields. In a core-only install (no bridge) the whole class is skipped.

Covered fixes:

* Fix 2a — recompute refuses to move an already-FILED year.
* Fix 2b — asset write guard on the engine-determining inputs once filed.
* Fix 2c — lifecycle events dated inside/before the last filed year refused.
* Fix 2d — posted board lines immutable without the ``cssk_unfreeze`` flag.
* Fix 3  — backfill dry-run honours increased-first-year / vehicle cap.
* Fix 4a — suspension events refused on §30a (extraordinary) assets.
* Fix 5b — a pre-schedule event date clamps to year 1, not the last year.
* Fix 5c — CZ-1 no longer allows §30a; CZ-2 keeps it (when l10n_cz installed).
"""
import unittest
from datetime import date

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTaxGuardrails(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Asset = cls.env["account.asset"]
        if "tax_line_ids" not in Asset._fields:
            raise unittest.SkipTest(
                "no tax bridge (account_asset_tax_ee / _oca) installed")
        cls.is_oca = "purchase_value" in Asset._fields and "profile_id" in Asset._fields
        cls.company = cls.env.company

        def acc(code, name, atype):
            return cls.env["account.account"].create({
                "code": code, "name": name, "account_type": atype,
                "company_ids": [Command.link(cls.company.id)],
            })

        cls.acc_asset = acc("TG024000", "Guardrail fixed asset", "asset_non_current")
        cls.acc_dep = acc("TG088000", "Guardrail accumulated depreciation", "asset_non_current")
        cls.acc_exp = acc("TG655000", "Guardrail depreciation expense", "expense")
        cls.journal = cls.env["account.journal"].create({
            "name": "Guardrail Asset Journal", "code": "TGAJ", "type": "general",
            "company_id": cls.company.id,
        })
        if cls.is_oca:
            cls.profile = cls.env["account.asset.profile"].create({
                "name": "Guardrail profile",
                "journal_id": cls.journal.id,
                "account_asset_id": cls.acc_asset.id,
                "account_depreciation_id": cls.acc_dep.id,
                "account_expense_depreciation_id": cls.acc_exp.id,
                "method_time": "year",
                "method_number": 5,
                "method_period": "year",
            })
        cls.cls_cz2 = cls.env["account.asset.tax.class"].create({
            "code": "TG-CZ2",
            "name": "Guardrail CZ group 2",
            "country_code": "CZ",
            "group_number": 2,
            "useful_life_years": 5,
            "allow_linear": True,
            "allow_accelerated": True,
            "allow_extraordinary": True,
            "linear_rate_first": 11,
            "linear_rate_next": 22.25,
            "linear_rate_increased": 20,
            "accel_coeff_first": 5,
            "accel_coeff_next": 6,
            "accel_coeff_increased": 5,
        })

    def _new_asset(self, value=100000, tax_method="linear"):
        if self.is_oca:
            asset = self.env["account.asset"].create({
                "name": "Guardrail machine",
                "profile_id": self.profile.id,
                "purchase_value": value,
                "date_start": date(2026, 1, 1),
            })
        else:
            asset = self.env["account.asset"].create({
                "name": "Guardrail machine",
                "account_asset_id": self.acc_asset.id,
                "account_depreciation_id": self.acc_dep.id,
                "account_depreciation_expense_id": self.acc_exp.id,
                "journal_id": self.journal.id,
                "acquisition_date": date(2026, 1, 1),
                "original_value": value,
                "method": "linear",
                "method_number": 8,
                "method_period": "12",
            })
        asset.write({
            "tax_depreciation_enabled": True,
            "tax_class_id": self.cls_cz2.id,
            "tax_method": tax_method,
            "tax_entry_value": value,
            "tax_in_service_date_override": date(2026, 1, 1),
        })
        return asset

    # ------------------------------------------------------------------
    # Fix 2a — recompute must not move a filed year
    # ------------------------------------------------------------------
    def test_recompute_refuses_to_move_filed_year(self):
        asset = self._new_asset()
        asset.compute_tax_depreciation_board()
        asset._tax_freeze_through(2026)
        n_lines = len(asset.tax_line_ids)
        # bypass the write guard on purpose (sanctioned only for the backfill
        # wizard) — the recompute is the second line of defence
        asset.with_context(cssk_unfreeze=True).write({"tax_entry_value": 120000})
        with self.assertRaises(UserError):
            asset.compute_tax_depreciation_board()
        # the check fires BEFORE anything is unlinked — board left intact
        self.assertEqual(len(asset.tax_line_ids), n_lines)
        frozen = asset.tax_line_ids.filtered("posted")
        self.assertAlmostEqual(frozen.amount, 11000, 2)

    # ------------------------------------------------------------------
    # Fix 2b — engine-determining inputs locked once a year is filed
    # ------------------------------------------------------------------
    def test_write_guard_on_filed_inputs(self):
        asset = self._new_asset()
        asset.compute_tax_depreciation_board()
        asset._tax_freeze_through(2026)
        for vals in (
            {"tax_entry_value": 90000},
            {"tax_in_service_date_override": date(2025, 6, 1)},
            {"tax_increased_first_year": "10"},
            {"tax_vehicle_capped": True},
        ):
            with self.assertRaises(UserError, msg="changing %s must be blocked" % vals):
                asset.write(vals)
        # writing the SAME values is a no-op and must pass
        asset.write({
            "tax_entry_value": 100000,
            "tax_in_service_date_override": date(2026, 1, 1),
            "tax_vehicle_capped": False,
        })
        # sanctioned bypass (used by the backfill wizard) still works
        asset.with_context(cssk_unfreeze=True).write({"tax_vehicle_capped": True})
        self.assertTrue(asset.tax_vehicle_capped)

    # ------------------------------------------------------------------
    # Fix 2c — events reaching into filed years refused
    # ------------------------------------------------------------------
    def test_event_inside_filed_years_blocked(self):
        asset = self._new_asset()
        asset.compute_tax_depreciation_board()
        asset._tax_freeze_through(2027)
        with self.assertRaises(UserError):
            asset._add_tax_event("improvement", date(2027, 6, 1), amount=10000)
        with self.assertRaises(UserError):
            asset._add_tax_event("suspension", date(2026, 3, 1))
        self.assertFalse(asset.tax_event_ids)
        # an event after the filed window is fine
        asset._add_tax_event("improvement", date(2028, 6, 1), amount=10000)
        self.assertEqual(len(asset.tax_event_ids), 1)
        self.assertAlmostEqual(
            sum(asset.tax_line_ids.mapped("amount")), 110000, 2)

    # ------------------------------------------------------------------
    # Fix 2d — posted lines immutable without cssk_unfreeze
    # ------------------------------------------------------------------
    def test_posted_line_write_guard(self):
        asset = self._new_asset()
        asset.compute_tax_depreciation_board()
        asset._tax_freeze_through(2026)
        frozen = asset.tax_line_ids.filtered("posted")
        for vals in (
            {"amount": 999},
            {"amount_cumulative": 999},
            {"residual": 999},
            {"fiscal_year": 2030},
            {"posted": False},
        ):
            with self.assertRaises(UserError, msg="posted-line %s must be blocked" % vals):
                frozen.write(vals)
        # no-op rewrite of the same value passes (idempotent freeze wizards)
        asset._tax_freeze_through(2026)
        self.assertTrue(frozen.posted)
        # the sanctioned mass-unfreeze path
        frozen.with_context(cssk_unfreeze=True).write({"posted": False})
        self.assertFalse(asset.tax_line_ids.filtered("posted"))

    # ------------------------------------------------------------------
    # Fix 3 — backfill dry-run must use the full engine spec
    # ------------------------------------------------------------------
    def test_backfill_dry_run_honours_increased_first_year(self):
        asset = self._new_asset()
        asset.tax_increased_first_year = "10"   # §31 +10 %: year 1 = 21 %
        wiz = self.env["account.asset.tax.backfill"].with_context(
            active_model="account.asset", active_id=asset.id,
        ).create({
            "tax_class_id": self.cls_cz2.id,
            "tax_method": "linear",
            "tax_entry_value": 100000,
            "tax_in_service_date": date(2026, 1, 1),
            "filed_through_year": 2026,
            # true statutory residual WITH the election; the old hand-rolled
            # spec dropped increased_first_year and computed 89000 -> mismatch
            "expected_residual": 79000,
        })
        wiz.action_backfill()
        frozen = asset.tax_line_ids.filtered("posted")
        self.assertEqual(frozen.mapped("fiscal_year"), [2026])
        self.assertAlmostEqual(frozen.amount, 21000, 2)

    def test_backfill_rerun_on_frozen_asset(self):
        # the wizard is the sanctioned unfreeze path: re-running it on an asset
        # with filed lines must not trip the new freeze guards
        asset = self._new_asset()
        asset.compute_tax_depreciation_board()
        asset._tax_freeze_through(2027)
        wiz = self.env["account.asset.tax.backfill"].with_context(
            active_model="account.asset", active_id=asset.id,
        ).create({
            "tax_class_id": self.cls_cz2.id,
            "tax_method": "linear",
            "tax_entry_value": 100000,
            "tax_in_service_date": date(2026, 1, 1),
            "filed_through_year": 2026,
        })
        wiz.action_backfill()
        self.assertEqual(
            asset.tax_line_ids.filtered("posted").mapped("fiscal_year"), [2026])

    # ------------------------------------------------------------------
    # Fix 4a — no suspension of §30a extraordinary depreciation
    # ------------------------------------------------------------------
    def test_suspension_blocked_on_extraordinary(self):
        asset = self._new_asset(value=600000, tax_method="extraordinary")
        asset.compute_tax_depreciation_board()
        with self.assertRaises(UserError):
            asset._add_tax_event("suspension", date(2027, 1, 1))
        self.assertFalse(asset.tax_event_ids)

    # ------------------------------------------------------------------
    # Fix 5b — pre-schedule event dates clamp to year 1, not the last year
    # ------------------------------------------------------------------
    def test_early_event_date_clamps_to_first_year(self):
        asset = self._new_asset()
        asset.compute_tax_depreciation_board()
        asset._add_tax_event("suspension", date(2020, 5, 1))
        lines = asset.tax_line_ids.sorted("year_index")
        first = lines.filtered(lambda l: l.fiscal_year == 2026)
        self.assertAlmostEqual(first.amount, 0, 2)   # year 1 suspended
        self.assertEqual(first.note, "suspended")
        self.assertAlmostEqual(sum(lines.mapped("amount")), 100000, 2)
        # pre-fix the LAST year was suspended instead
        self.assertNotEqual(lines[-1].note, "suspended")

    # ------------------------------------------------------------------
    # Fix 5c — CZ-1 must not offer §30a; CZ-2 keeps it
    # ------------------------------------------------------------------
    def test_cz_group_extraordinary_eligibility(self):
        cz1 = self.env.ref("l10n_cz_account_asset_tax.cz_group_1",
                           raise_if_not_found=False)
        if not cz1:
            self.skipTest("l10n_cz_account_asset_tax not installed")
        cz2 = self.env.ref("l10n_cz_account_asset_tax.cz_group_2")
        self.assertFalse(cz1.allow_extraordinary,
                         "§30a targets emission-free vehicles (group 2), not group 1")
        self.assertTrue(cz2.allow_extraordinary)
        self.assertNotIn("extraordinary", cz1.allowed_methods())
        self.assertIn("extraordinary", cz2.allowed_methods())
