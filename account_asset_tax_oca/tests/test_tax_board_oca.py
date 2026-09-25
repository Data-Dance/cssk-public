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

    def test_disposal_event_sk_prorata(self):
        asset = self._new_asset("linear")
        asset.compute_tax_depreciation_board()
        asset._add_tax_event("disposal", date(2028, 4, 10))
        lines = asset.tax_line_ids.sorted("year_index")
        last = lines[-1]
        self.assertEqual(last.fiscal_year, 2028)
        self.assertAlmostEqual(last.amount, 10000 * 3 / 12, 2)   # 3 months used

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
        self.assertAlmostEqual(last.amount, 10000 * 3 / 12, 2)  # SK pro-rata

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
