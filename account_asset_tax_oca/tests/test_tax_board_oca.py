"""Integration tests for the OCA (Community) bridge.

Run in a dev DB with OCA ``account_asset_management`` installed::

    odoo -d <db> -i account_asset_tax_oca --test-enable \
         --test-tags /account_asset_tax_oca

Mirrors the EE bridge tests against the OCA asset model (``purchase_value`` /
``date_start`` / ``account.asset.profile``).
"""
from datetime import date

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTaxBoardOCA(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        def acc(code, name, atype):
            return cls.env["account.account"].create({
                "code": code, "name": name, "account_type": atype,
                "company_ids": [Command.link(cls.company.id)],
            })

        cls.acc_asset = acc("T024000", "Test fixed asset", "asset_non_current")
        cls.acc_dep = acc("T088000", "Test accumulated depreciation", "asset_non_current")
        cls.acc_exp = acc("T655000", "Test depreciation expense", "expense")
        cls.journal = cls.env["account.journal"].create({
            "name": "Test Asset Journal", "code": "TASJ", "type": "general",
            "company_id": cls.company.id,
        })
        cls.profile = cls.env["account.asset.profile"].create({
            "name": "Test profile",
            "journal_id": cls.journal.id,
            "account_asset_id": cls.acc_asset.id,
            "account_depreciation_id": cls.acc_dep.id,
            "account_expense_depreciation_id": cls.acc_exp.id,
            "method_time": "year",
            "method_number": 5,
            "method_period": "year",
        })
        cls.cls_group = cls.env["account.asset.tax.class"].create({
            "code": "T-SK2",
            "name": "Test SK group 2",
            "country_code": "SK",
            "group_number": 2,
            "useful_life_years": 6,
            "allow_linear": True,
            "allow_accelerated": True,
            "accel_coeff_first": 6,
            "accel_coeff_next": 7,
            "accel_coeff_increased": 6,
        })

    def _new_asset(self, method="linear"):
        asset = self.env["account.asset"].create({
            "name": "Machine",
            "profile_id": self.profile.id,
            "purchase_value": 60000,
            "date_start": date(2026, 1, 1),
        })
        asset.write({
            "tax_depreciation_enabled": True,
            "tax_class_id": self.cls_group.id,
            "tax_method": method,
            "tax_entry_value": 60000,
            "tax_in_service_date_override": date(2026, 1, 1),
        })
        return asset

    # ------------------------------------------------------------------
    def test_board_sk_linear_january(self):
        asset = self._new_asset("linear")
        asset.compute_tax_depreciation_board()
        lines = asset.tax_line_ids.sorted("year_index")
        # SK linear, in service January -> full first year, no remainder line
        self.assertEqual(len(lines), 6)
        self.assertAlmostEqual(lines[0].amount, 10000, 2)   # 60000 / 6
        self.assertAlmostEqual(sum(lines.mapped("amount")), 60000, 2)

    def test_board_sk_accelerated(self):
        asset = self._new_asset("accelerated")
        asset.compute_tax_depreciation_board()
        lines = asset.tax_line_ids.sorted("year_index")
        self.assertAlmostEqual(lines[0].amount, 10000, 2)   # 60000 / k1(6), Jan = full
        self.assertAlmostEqual(sum(lines.mapped("amount")), 60000, 2)

    def test_suspension_event(self):
        asset = self._new_asset("linear")
        asset.compute_tax_depreciation_board()
        asset._add_tax_event("suspension", date(2028, 1, 1), duration_years=1)
        lines = asset.tax_line_ids.sorted("year_index")
        self.assertAlmostEqual(sum(lines.mapped("amount")), 60000, 2)
        suspended = lines.filtered(lambda l: l.fiscal_year == 2028)
        self.assertAlmostEqual(suspended.amount, 0, 2)

    def test_disposal_event_sk_no_depreciation(self):
        # § 22 ods. 11 zákona 595/2003 Z. z.: nothing in the year of disposal;
        # the residual (60000 - 2 x 10000) is the § 19 ods. 3 písm. b) expense
        asset = self._new_asset("linear")
        asset.compute_tax_depreciation_board()
        asset._add_tax_event("disposal", date(2028, 4, 10))
        lines = asset.tax_line_ids.sorted("year_index")
        last = lines[-1]
        self.assertEqual(last.fiscal_year, 2028)
        self.assertAlmostEqual(last.amount, 0.0, 2)
        self.assertAlmostEqual(asset.tax_residual_on_disposal(), 40000, 2)

    def test_disposal_event_sk_whole_months_when_flagged(self):
        # § 22 ods. 12: flagged assets keep the whole months held (Jan-Mar)
        asset = self._new_asset("linear")
        asset.tax_sk_disposal_months = True
        asset.compute_tax_depreciation_board()
        asset._add_tax_event("disposal", date(2028, 4, 10))
        last = asset.tax_line_ids.sorted("year_index")[-1]
        self.assertAlmostEqual(last.amount, 10000 * 3 / 12, 2)
        self.assertAlmostEqual(asset.tax_residual_on_disposal(), 37500, 2)

    def test_disposal_hook_on_remove(self):
        asset = self._new_asset("linear")
        asset.compute_tax_depreciation_board()
        # the OCA removal wizard sets state='removed' + date_remove; the bridge
        # write hook should record the tax disposal event
        asset.write({"state": "removed", "date_remove": date(2028, 4, 10)})
        evs = asset.tax_event_ids.filtered(lambda e: e.event_type == "disposal")
        self.assertEqual(len(evs), 1)
        last = asset.tax_line_ids.sorted("year_index")[-1]
        self.assertEqual(last.fiscal_year, 2028)
        self.assertAlmostEqual(last.amount, 0.0, 2)  # SK § 22 ods. 11

    def test_method_lock_enforced(self):
        asset = self._new_asset("linear")
        asset.tax_method_locked = True
        with self.assertRaises(UserError):
            asset.tax_method = "accelerated"

    def test_deferred_tax(self):
        asset = self._new_asset("linear")
        asset.compute_tax_depreciation_board()
        wiz = self.env["account.asset.tax.reconciliation"].create({
            "company_id": asset.company_id.id,
            "date_from": date(2026, 1, 1), "date_to": date(2026, 12, 31),
            "tax_rate": 21.0,
        })
        wiz.action_compute()
        line = wiz.line_ids.filtered(lambda l: l.asset_ref_id == asset.id)
        # accounting NBV 60000 (no posted dep) vs tax residual 50000 -> DTL on 10000
        self.assertAlmostEqual(line.temp_difference, 10000, 2)
        self.assertAlmostEqual(line.deferred_tax, 2100, 2)   # 10000 * 21%

    def test_profile_tax_defaults(self):
        self.profile.write({
            "tax_depreciation_enabled": True,
            "tax_class_id": self.cls_group.id,
            "tax_method": "accelerated",
        })
        asset = self.env["account.asset"].create({
            "name": "From profile", "profile_id": self.profile.id,
            "purchase_value": 60000, "date_start": date(2026, 1, 1),
        })
        self.assertTrue(asset.tax_depreciation_enabled)
        self.assertEqual(asset.tax_class_id, self.cls_group)
        self.assertEqual(asset.tax_method, "accelerated")

    def test_close_year_freezes(self):
        asset = self._new_asset("linear")
        asset.compute_tax_depreciation_board()
        wiz = self.env["account.asset.tax.close.year"].create({
            "company_id": asset.company_id.id, "fiscal_year": 2027,
        })
        wiz.action_close()
        frozen = asset.tax_line_ids.filtered("posted")
        self.assertTrue(frozen)
        self.assertTrue(all(l.fiscal_year <= 2027 for l in frozen))
        self.assertTrue(asset.tax_method_locked)

    def test_xlsx_export(self):
        asset = self._new_asset("linear")
        asset.compute_tax_depreciation_board()
        wiz = self.env["account.asset.tax.reconciliation"].create({
            "company_id": asset.company_id.id,
            "date_from": date(2026, 1, 1), "date_to": date(2026, 12, 31),
        })
        wiz.action_compute()
        res = wiz.action_export_xlsx()
        self.assertTrue(wiz.xlsx_file)
        self.assertTrue(res.get("url", "").endswith("download=true"))

    def test_pdf_report_renders(self):
        asset = self._new_asset("linear")
        asset.compute_tax_depreciation_board()
        wiz = self.env["account.asset.tax.reconciliation"].create({
            "company_id": asset.company_id.id,
            "date_from": date(2026, 1, 1), "date_to": date(2026, 12, 31),
        })
        wiz.action_compute()
        report = self.env.ref("account_asset_tax.action_report_reconciliation")
        html, _dummy = self.env["ir.actions.report"]._render_qweb_html(report.id, wiz.ids)
        self.assertIn(b"Tax Depreciation Reconciliation", html)

    def test_reconciliation_runs(self):
        asset = self._new_asset("linear")
        asset.compute_tax_depreciation_board()
        wiz = self.env["account.asset.tax.reconciliation"].create({
            "company_id": asset.company_id.id,
            "date_from": date(2026, 1, 1),
            "date_to": date(2026, 12, 31),
        })
        wiz.action_compute()
        line = wiz.line_ids.filtered(lambda l: l.asset_ref_id == asset.id)
        self.assertTrue(line)
        self.assertAlmostEqual(line.tax_amount, 10000, 2)

    # ------------------------------------------------------------------
    # SK § 17 ods. 34 — a car of 48 000 EUR or more
    # ------------------------------------------------------------------
    def test_sk_vehicle_board_full_and_addback_separate(self):
        self.company.tax_vehicle_cap_amount = 48000
        asset = self._new_asset("linear")
        asset.tax_vehicle_capped = True
        asset.compute_tax_depreciation_board()
        lines = asset.tax_line_ids.sorted("year_index")
        # the depreciation itself is NOT capped …
        self.assertAlmostEqual(sum(lines.mapped("amount")), 60000, 2)
        self.assertAlmostEqual(lines[0].amount, 10000, 2)
        # … the excess over § 27 on 48 000 (8000 a year) is shown apart
        self.assertEqual(lines.mapped("vehicle_addback"), [2000.0] * 6)
        diff = self.company._cssk_asset_book_tax_difference(
            date(2026, 1, 1), date(2026, 12, 31))
        self.assertAlmostEqual(diff["vehicle_addback"], 2000, 2)
        self.assertAlmostEqual(diff["tax"], 10000, 2)
        wiz = self.env["account.asset.tax.reconciliation"].create({
            "company_id": self.company.id,
            "date_from": date(2026, 1, 1), "date_to": date(2026, 12, 31),
        })
        wiz.action_compute()
        self.assertAlmostEqual(wiz.total_vehicle_addback, 2000, 2)
        # not mixed into the unconditional add-back column
        line = wiz.line_ids.filtered(lambda l: l.asset_ref_id == asset.id)
        self.assertAlmostEqual(line.addback, 0.0, 2)

    # ------------------------------------------------------------------
    # DPPO row labels follow the company's country
    # ------------------------------------------------------------------
    def test_dppo_row_labels_per_country(self):
        wiz = self.env["account.asset.tax.reconciliation"].create({
            "company_id": self.company.id,
            "date_from": date(2026, 1, 1), "date_to": date(2026, 12, 31),
        })
        self.company.write({"country_id": self.env.ref("base.sk").id,
                            "account_fiscal_country_id": self.env.ref("base.sk").id})
        wiz.invalidate_recordset(["addback_row", "deduction_row"])
        self.assertEqual((wiz.addback_row, wiz.deduction_row), ("r. 150", "r. 250"))
        self.company.write({"country_id": self.env.ref("base.cz").id,
                            "account_fiscal_country_id": self.env.ref("base.cz").id})
        wiz.invalidate_recordset(["addback_row", "deduction_row"])
        # DPPDP9: ř. 50 (kc_ii60_50) add-back, ř. 150 (kc_ii170_150) deduction
        self.assertEqual((wiz.addback_row, wiz.deduction_row), ("ř. 50", "ř. 150"))
        self._new_asset("linear").compute_tax_depreciation_board()
        wiz.action_compute()
        report = self.env.ref("account_asset_tax.action_report_reconciliation")
        html, _dummy = self.env["ir.actions.report"]._render_qweb_html(report.id, wiz.ids)
        self.assertIn("Add-back (ř. 50)", html.decode())
        self.assertIn("Deduction (ř. 150)", html.decode())
        self.assertNotIn("(250)", html.decode())

    # ------------------------------------------------------------------
    # Deferred tax true-up: the 481 balance AT THE PERIOD END
    # ------------------------------------------------------------------
    def test_deferred_tax_ignores_entries_after_period(self):
        def acc(code, atype):
            return self.env["account.account"].create({
                "code": code, "name": code, "account_type": atype,
                "company_ids": [Command.link(self.company.id)],
            })
        acc_481 = acc("T481000", "liability_non_current")
        acc_592 = acc("T592000", "expense")
        self.company.write({
            "tax_deferred_journal_id": self.journal.id,
            "account_deferred_tax_id": acc_481.id,
            "account_deferred_tax_pl_id": acc_592.id,
        })
        # a later year's entry already on 481 (e.g. next year's true-up)
        later = self.env["account.move"].create({
            "journal_id": self.journal.id, "date": date(2027, 12, 31),
            "line_ids": [
                Command.create({"account_id": acc_481.id, "name": "later",
                                "debit": 0.0, "credit": 999.0}),
                Command.create({"account_id": acc_592.id, "name": "later",
                                "debit": 999.0, "credit": 0.0}),
            ],
        })
        later.action_post()
        asset = self._new_asset("linear")
        asset.compute_tax_depreciation_board()
        wiz = self.env["account.asset.tax.reconciliation"].create({
            "company_id": self.company.id,
            "date_from": date(2026, 1, 1), "date_to": date(2026, 12, 31),
            "tax_rate": 21.0,
        })
        wiz.action_compute()
        res = wiz.action_post_deferred_tax()
        move = self.env["account.move"].browse(res["res_id"])
        line_481 = move.line_ids.filtered(lambda l: l.account_id == acc_481)
        # closing DTL 2100 (10000 x 21 %) against 0 on 481 at 31. 12. 2026
        self.assertAlmostEqual(line_481.credit, 2100, 2)

    # ------------------------------------------------------------------
    # CZ § 30a — a monthly board lined up against yearly book depreciation
    # ------------------------------------------------------------------
    def test_monthly_board_book_counted_once_per_year(self):
        cz_class = self.env["account.asset.tax.class"].create({
            "code": "T-CZ2", "name": "Test CZ group 2", "country_code": "CZ",
            "group_number": 2, "useful_life_years": 5,
            "allow_linear": True, "allow_extraordinary": True,
            "linear_rate_first": 11, "linear_rate_next": 22.25,
            "linear_rate_increased": 20,
        })
        asset = self.env["account.asset"].create({
            "name": "EV", "profile_id": self.profile.id,
            "purchase_value": 120000, "date_start": date(2026, 1, 1),
        })
        asset.compute_depreciation_board()
        book_2026 = asset._cssk_book_depreciation_by_year()[2026]["amount"]
        self.assertTrue(book_2026)
        asset.write({
            "tax_depreciation_enabled": True, "tax_class_id": cz_class.id,
            "tax_method": "extraordinary", "tax_entry_value": 120000,
            "tax_in_service_date_override": date(2026, 1, 15),
        })
        asset.compute_tax_depreciation_board()
        lines_2026 = asset.tax_line_ids.filtered(lambda l: l.fiscal_year == 2026)
        self.assertEqual(len(lines_2026), 11)   # Feb-Dec
        tax_2026 = sum(lines_2026.mapped("amount"))
        self.assertAlmostEqual(tax_2026, 66000, 2)   # 11 x 6000
        self.assertAlmostEqual(sum(lines_2026.mapped("book_amount")), book_2026, 2)
        self.assertAlmostEqual(sum(lines_2026.mapped("difference")),
                               book_2026 - tax_2026, 2)
        # the register shows the asset once for the year
        reg = self.env["account.asset.tax.register"].create({
            "company_id": self.company.id, "fiscal_year": 2026,
        })
        groups, totals = reg.get_register()
        rows = [r for g in groups for r in g["lines"] if r["asset"] == asset.display_name]
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0]["amount"], tax_2026, 2)
        self.assertAlmostEqual(rows[0]["book"], book_2026, 2)
        self.assertAlmostEqual(rows[0]["input"], 120000, 2)
        self.assertAlmostEqual(rows[0]["opening"], 120000, 2)
        self.assertAlmostEqual(rows[0]["closing"], 120000 - tax_2026, 2)
        # the per-year merge sums the months
        by_year = {r["year"]: r for r in asset._cssk_book_tax_by_year()}
        self.assertAlmostEqual(by_year[2026]["tax"], tax_2026, 2)
