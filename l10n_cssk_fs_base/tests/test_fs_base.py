from freezegun import freeze_time

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


class TestFsBase(TransactionCase):
    """Smoke tests for the shared financial-statements framework."""

    def test_models_load(self):
        for model in (
            "cssk.fs.statement.version",
            "cssk.fs.statement.line.def",
            "cssk.fs.statement",
            "cssk.fs.statement.line",
        ):
            self.assertIn(model, self.env)


@tagged("post_install", "-at_install")
class TestFsEngine(AccountTestInvoicingCommon):
    """Functional: account-code balances → line tree, comparison period,
    override."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        # Account-code evaluation is chart-agnostic; just need the SK fiscal
        # country (for the version domain) + accounts with the right codes.
        cls.company.account_fiscal_country_id = cls.env.ref("base.sk")
        cls.journal = cls.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", cls.company.id)],
            limit=1,
        )
        cls.acc_asset = cls.env["account.account"].create({
            "name": "Test DHM", "code": "022999",
            "account_type": "asset_non_current",
            "company_ids": [(6, 0, [cls.company.id])],
        })
        cls.acc_eq = cls.env["account.account"].create({
            "name": "Test equity", "code": "411999",
            "account_type": "equity",
            "company_ids": [(6, 0, [cls.company.id])],
        })
        cls.template = cls.env["ir.ui.view"].create({
            "name": "cssk fs test template",
            "type": "qweb",
            "arch": "<t t-name='cssk_fs_test_template'><FS/></t>",
        })
        cls.version = cls.env["cssk.fs.statement.version"].create({
            "name": "TST Súvaha", "country_id": cls.env.ref("base.sk").id,
            "statement_kind": "balance_sheet", "valid_from": "2025-01-01",
            "xml_template_ref_id": cls.template.id,
            "xml_root_element": "FS",
            # A fixture form has no authority and no XSD, which is the same
            # state the two prehľady are in for real — declare it, as they do.
            "xml_schema_optional": True,
            "line_def_ids": [
                (0, 0, {"code": "a022", "name": "DHM (022)", "kind": "accounts",
                        "account_formula": "022", "sequence": 10}),
                (0, 0, {"code": "total", "name": "Spolu", "kind": "aggregate",
                        "aggregate_formula": "a022", "sequence": 20}),
            ],
        })

    def _post_entry(self, date, amount):
        move = self.env["account.move"].create({
            "move_type": "entry", "journal_id": self.journal.id, "date": date,
            "line_ids": [
                (0, 0, {"account_id": self.acc_asset.id,
                        "debit": amount, "credit": 0.0}),
                (0, 0, {"account_id": self.acc_eq.id,
                        "debit": 0.0, "credit": amount}),
            ],
        })
        move.action_post()
        return move

    def _make_statement(self):
        return self.env["cssk.fs.statement"].create({
            "company_id": self.company.id, "version_id": self.version.id,
            "date_from": "2026-01-01", "date_to": "2026-12-31",
        })

    def test_balance_sheet_and_comparison(self):
        # Balance sheet is cumulative as-of the period end.
        self._post_entry("2025-06-15", 700.0)   # prior year
        self._post_entry("2026-06-15", 1000.0)  # current year
        st = self._make_statement()
        st.action_compute_lines()
        rows = {line.code: line for line in st.line_ids}
        # current = cumulative to 2026-12-31 = 1700; prior = as-of 2025 = 700
        self.assertAlmostEqual(rows["a022"].current_value, 1700.0, places=2)
        self.assertAlmostEqual(rows["a022"].prior_value, 700.0, places=2)
        self.assertAlmostEqual(rows["total"].current_value, 1700.0, places=2)

    def test_eval_accounts_negation_and_overlap(self):
        """Task-3 regression (read_group evaluator): a leading '-' negates a
        prefix's contribution and an account matched by two tokens
        contributes once PER TOKEN — identical to the historical per-prefix
        search."""
        self._post_entry("2026-06-15", 1000.0)
        st = self._make_statement()
        balances = st._cssk_account_balance_map(None, "2026-12-31")
        # bal(022999) = +1000 (debit), bal(411999) = −1000 (credit)
        self.assertAlmostEqual(
            st._eval_accounts("022", balances), 1000.0, places=2)
        self.assertAlmostEqual(
            st._eval_accounts("-411", balances), 1000.0, places=2)
        # '02' and '022' both match 022999 → it contributes once per token
        self.assertAlmostEqual(
            st._eval_accounts("02,022", balances), 2000.0, places=2)

    def test_override_flows_into_aggregate(self):
        self._post_entry("2026-06-15", 1000.0)
        st = self._make_statement()
        st.action_compute_lines()
        a022 = st.line_ids.filtered(lambda line: line.code == "a022")
        a022.write({"is_overridden": True, "manual_value": 500.0})
        st.action_compute_lines()
        rows = {line.code: line for line in st.line_ids}
        self.assertAlmostEqual(rows["a022"].current_value, 500.0, places=2)
        self.assertAlmostEqual(rows["total"].current_value, 500.0, places=2)
        self.assertTrue(rows["a022"].is_overridden)

    def test_prior_override_survives_recompute_and_feeds_aggregate(self):
        """The first year in Odoo has no prior-year ledger: the comparative
        figure is typed in, kept on recompute and summed into the totals,
        while the current column still comes from the books."""
        self._post_entry("2026-06-15", 1000.0)
        st = self._make_statement()
        st.action_compute_lines()
        a022 = st.line_ids.filtered(lambda line: line.code == "a022")
        self.assertAlmostEqual(a022.prior_value, 0.0, places=2)
        a022.write({"is_prior_overridden": True, "prior_manual_value": 640.0})
        st.action_compute_lines()
        rows = {line.code: line for line in st.line_ids}
        self.assertTrue(rows["a022"].is_prior_overridden)
        self.assertAlmostEqual(rows["a022"].prior_value, 640.0, places=2)
        self.assertAlmostEqual(rows["total"].prior_value, 640.0, places=2)
        self.assertAlmostEqual(rows["a022"].current_value, 1000.0, places=2)
        self.assertFalse(rows["a022"].is_overridden)

    def test_override_edit_requires_compute_before_export(self):
        """Totals over an edited row are stale until Compute, so the edit
        sends the statement back to draft and export refuses it."""
        self._post_entry("2026-06-15", 1000.0)
        st = self._make_statement()
        st.action_compute_lines()
        self.assertEqual(st.state, "preview")
        a022 = st.line_ids.filtered(lambda line: line.code == "a022")
        a022.write({"is_overridden": True, "manual_value": 500.0})
        self.assertEqual(st.state, "draft")
        with self.assertRaises(UserError):
            st.action_export_xml()
        st.action_compute_lines()
        self.assertEqual(st.state, "preview")
        total = st.line_ids.filtered(lambda line: line.code == "total")
        self.assertAlmostEqual(total.current_value, 500.0, places=2)

    def test_aggregate_cannot_be_overridden(self):
        """A total typed over its own rows no longer adds them up."""
        self._post_entry("2026-06-15", 1000.0)
        st = self._make_statement()
        st.action_compute_lines()
        total = st.line_ids.filtered(lambda line: line.code == "total")
        with self.assertRaises(ValidationError):
            total.write({"is_overridden": True, "manual_value": 1.0})
        with self.assertRaises(ValidationError):
            total.write({"is_prior_overridden": True})

    def test_stale_aggregate_override_is_not_carried_over(self):
        """One ticked before the constraint existed is dropped on recompute
        instead of failing it."""
        self._post_entry("2026-06-15", 1000.0)
        st = self._make_statement()
        st.action_compute_lines()
        total = st.line_ids.filtered(lambda line: line.code == "total")
        self.env.cr.execute(
            "UPDATE cssk_fs_statement_line SET is_overridden = TRUE, "
            "manual_value = 1 WHERE id = %s", [total.id])
        total.invalidate_recordset()
        st.action_compute_lines()
        total = st.line_ids.filtered(lambda line: line.code == "total")
        self.assertFalse(total.is_overridden)
        self.assertAlmostEqual(total.current_value, 1000.0, places=2)

    def test_leaf_drilldown_is_on_demand(self):
        """Leaf rows carry a re-queryable domain (not stored ids) that ties to
        the postings; aggregates carry none; the statement health roll-up is OK."""
        self._post_entry("2026-06-15", 1000.0)
        st = self._make_statement()
        st.action_compute_lines()
        rows = {line.code: line for line in st.line_ids}
        leaf, agg = rows["a022"], rows["total"]

        self.assertTrue(leaf.is_leaf)
        self.assertTrue(leaf.has_source)
        self.assertTrue(leaf.source_domain)            # a domain string, not ids
        self.assertTrue(leaf.source_reconciles)        # lines sum to the value
        # the action re-queries the domain and finds the posting
        action = leaf.action_view_source_lines()
        found = self.env["account.move.line"].search(action["domain"])
        self.assertTrue(found)
        self.assertEqual(found.mapped("account_id"), self.acc_asset)
        # an aggregate is not drillable
        self.assertFalse(agg.has_source)
        # roll-up: every drillable leaf reconciles
        self.assertEqual(st.unreconciled_count, 0)

    def test_export_preflight_requires_company_vat(self):
        """Task 3 regression: FS export without the company VAT fails early
        with a named field (the official UZ templates emit it as the filer
        identification)."""
        self._post_entry("2026-06-15", 1000.0)
        st = self._make_statement()
        st.action_compute_lines()
        self.company.vat = False
        with self.assertRaises(UserError) as cm:
            st.action_export_xml()
        self.assertIn("VAT", str(cm.exception))
        self.company.vat = "SK2023456787"
        st.action_export_xml()
        self.assertEqual(st.state, "exported")

    def test_export_runs_kontroly_hook(self):
        """Task-1 regression: the consolidated pipeline gives the FS the
        ``_cssk_check_kontroly`` stage (no-op until a country module uses
        it), run before rendering."""
        from unittest.mock import patch
        self._post_entry("2026-06-15", 1000.0)
        self.company.vat = "SK2023456787"
        st = self._make_statement()
        st.action_compute_lines()
        Model = type(self.env["cssk.fs.statement"])

        # patch with ``new=`` a plain function, NEVER a MagicMock — the
        # registry's ``_ondelete_methods`` scan would cache the mock (it
        # auto-creates an ``_ondelete`` attribute) as an unlink hook.
        calls = []

        def fake_hook(model):
            calls.append(True)
            return True

        with patch.object(Model, "_cssk_check_kontroly", new=fake_hook):
            st.action_export_xml()
        self.assertEqual(len(calls), 1)
        self.assertEqual(st.state, "exported")

    def test_reverse_drill_footprint(self):
        """A posting knows which statement rows it feeds (reverse drill)."""
        move = self._post_entry("2026-06-15", 1000.0)
        st = self._make_statement()
        st.action_compute_lines()
        asset_line = move.line_ids.filtered(
            lambda line: line.account_id == self.acc_asset)
        codes = [fp["code"] for fp in asset_line._cssk_statutory_footprint()]
        self.assertIn("a022", codes)
        # the document-level aggregation/dedup returns the same row
        wizard_action = move.action_cssk_statutory_footprint()
        wizard = self.env["cssk.statutory.footprint.wizard"].browse(
            wizard_action["res_id"])
        self.assertIn("a022", wizard.line_ids.mapped("code"))

    # ------------------------------------------------------------------
    # Income-statement coverage and the fiscal-year default
    # ------------------------------------------------------------------
    def _combined_version(self):
        """A balance sheet that also carries movement-basis P&L rows, the way
        the Slovak Úč POD does."""
        return self.env["cssk.fs.statement.version"].create({
            "name": "TST Úč POD", "country_id": self.env.ref("base.sk").id,
            "statement_kind": "balance_sheet", "valid_from": "2025-01-01",
            "xml_template_ref_id": self.template.id,
            "xml_root_element": "FS", "xml_schema_optional": True,
            "line_def_ids": [
                (0, 0, {"code": "s022", "name": "DHM", "kind": "accounts",
                        "basis": "as_of", "account_formula": "022",
                        "sequence": 10}),
                (0, 0, {"code": "r6", "name": "Výnosy", "kind": "accounts",
                        "basis": "movement", "account_formula": "6",
                        "sequence": 20}),
            ],
        })

    def test_covers_profit_loss(self):
        self.assertFalse(self.version.covers_profit_loss,
                         "a plain balance sheet is not an income statement")
        self.assertTrue(self._combined_version().covers_profit_loss)

    def test_income_statement_menu_lists_combined_statement(self):
        """On SK the Income statement menu was always empty: no profit_loss
        version exists, the výkaz lives inside the Úč POD balance sheet."""
        combined = self._combined_version()
        # Leave no profit_loss version in play for SK, as on a real SK database.
        self.env["cssk.fs.statement.version"].search([
            ("statement_kind", "=", "profit_loss"),
            ("country_id", "=", self.env.ref("base.sk").id),
        ]).write({"country_id": self.env.ref("base.cz").id})
        st = self.env["cssk.fs.statement"].create({
            "company_id": self.company.id, "version_id": combined.id,
            "date_from": "2026-01-01", "date_to": "2026-12-31",
        })
        action = self.env.ref("l10n_cssk_fs_base.cssk_fs_pl_action")
        domain = eval(action.domain)  # noqa: S307 - our own action literal
        self.assertIn(st, self.env["cssk.fs.statement"].search(domain))
        plain = self._make_statement()
        self.assertNotIn(plain, self.env["cssk.fs.statement"].search(domain))
        self.assertTrue(st.name.startswith("Financial statements"), st.name)
        # New from that menu lands on the combined version.
        defaults = self.env["cssk.fs.statement"].with_company(
            self.company).with_context(fs_create_kind="profit_loss",
                                       lang="en_US").default_get(
            ["version_id", "date_from", "date_to"])
        self.assertEqual(defaults.get("version_id"), combined.id)

    def test_default_period_is_last_fiscal_year(self):
        """A company whose year ends in March gets April-March, not Jan-Dec."""
        self.company.write({"fiscalyear_last_month": "3",
                            "fiscalyear_last_day": 31})
        Statement = self.env["cssk.fs.statement"].with_company(self.company)
        with freeze_time("2026-10-01"):
            defaults = Statement.default_get(["date_from", "date_to"])
        self.assertEqual(str(defaults["date_from"]), "2025-04-01")
        self.assertEqual(str(defaults["date_to"]), "2026-03-31")
        self.company.write({"fiscalyear_last_month": "12"})
        with freeze_time("2026-10-01"):
            defaults = Statement.default_get(["date_from", "date_to"])
        self.assertEqual(str(defaults["date_from"]), "2025-01-01")
        self.assertEqual(str(defaults["date_to"]), "2025-12-31")

    # ------------------------------------------------------------------
    # Statement account mapping and the contributor drill-down
    # ------------------------------------------------------------------
    def _account(self, code, account_type):
        return self.env["account.account"].create({
            "name": "Test %s" % code, "code": code,
            "account_type": account_type,
            "company_ids": [(6, 0, [self.company.id])],
        })

    def _post_pair(self, date, debit_acc, credit_acc, amount, journal=None):
        move = self.env["account.move"].create({
            "move_type": "entry", "journal_id": (journal or self.journal).id,
            "date": date,
            "line_ids": [
                (0, 0, {"account_id": debit_acc.id,
                        "debit": amount, "credit": 0.0}),
                (0, 0, {"account_id": credit_acc.id,
                        "debit": 0.0, "credit": amount}),
            ],
        })
        move.action_post()
        return move

    def _loan_version(self):
        return self.env["cssk.fs.statement.version"].create({
            "name": "TST loans", "country_id": self.env.ref("base.sk").id,
            "statement_kind": "balance_sheet", "valid_from": "2025-01-01",
            "xml_template_ref_id": self.template.id,
            "xml_root_element": "FS", "xml_schema_optional": True,
            "line_def_ids": [
                (0, 0, {"code": "bank", "name": "Banky", "kind": "accounts",
                        "account_formula": "221000", "sequence": 10}),
                (0, 0, {"code": "loan_long", "name": "Dlhodobé úvery",
                        "kind": "accounts", "account_formula": "-461100",
                        "sequence": 20}),
                (0, 0, {"code": "loan_short", "name": "Bežné úvery",
                        "kind": "accounts",
                        "account_formula": "-221900,-461200",
                        "sequence": 30}),
                (0, 0, {"code": "eq", "name": "VI", "kind": "accounts",
                        "account_formula": "-411", "sequence": 40}),
                # A residual token, as Úč POD has: it switches on the
                # synthetic-absorb rule that lets 221000 take 221019.
                (0, 0, {"code": "res02", "name": "Ostatný DHM",
                        "kind": "accounts", "account_formula": "02X",
                        "sequence": 50}),
            ],
        })

    def _loan_statement(self, version):
        return self.env["cssk.fs.statement"].create({
            "company_id": self.company.id, "version_id": version.id,
            "date_from": "2026-01-01", "date_to": "2026-12-31",
        })

    def test_account_mapping_reports_analytic_under_form_code(self):
        """A chart's own analytic (461002) reaches no row until mapped to the
        code the form names (461200); then it lands there, leaves the
        unmapped list, and its row drills into exactly its journal items."""
        version = self._loan_version()
        loan = self._account("461002", "liability_non_current")
        self._post_pair("2026-03-01", self.acc_asset, loan, 800.0)
        st = self._loan_statement(version)
        st.action_compute_lines()
        rows = {line.code: line for line in st.line_ids}
        self.assertAlmostEqual(rows["loan_short"].current_value, 0.0, places=2)
        self.assertIn("461002", st.unmapped_note or "")
        row = st.unmapped_line_ids.filtered(lambda r: r.code == "461002")
        self.assertEqual(row.account_ids, loan)
        self.assertEqual(row.account_name, loan.name)
        self.assertAlmostEqual(row.balance, -800.0, places=2)
        items = self.env["account.move.line"].search(
            row.action_view_journal_items()["domain"])
        self.assertEqual(items.account_id, loan)
        self.assertAlmostEqual(sum(items.mapped("balance")), -800.0, places=2)
        action = st.action_view_unmapped()
        self.assertEqual(action["target"], "new")
        self.assertEqual(action["res_id"], st.id)

        self.env["cssk.statement.account.map"].create({
            "company_id": self.company.id, "account_id": loan.id,
            "reported_code": "461200",
        })
        st.action_compute_lines()
        rows = {line.code: line for line in st.line_ids}
        self.assertAlmostEqual(rows["loan_short"].current_value, 800.0, places=2)
        self.assertNotIn("461002", st.unmapped_note or "")
        self.assertTrue(rows["loan_short"].source_reconciles)
        found = self.env["account.move.line"].search(
            rows["loan_short"].action_view_source_lines()["domain"])
        self.assertEqual(found.account_id, loan)

    def test_account_mapping_credit_side_only(self):
        """An overdrawn bank account is reported as a short-term bank loan;
        in funds it stays a bank account. The side follows the balance at
        the period end."""
        version = self._loan_version()
        bank = self._account("221019", "asset_cash")
        self.env["cssk.statement.account.map"].create({
            "company_id": self.company.id, "account_id": bank.id,
            "balance_side": "credit", "reported_code": "221900",
        })
        # in funds: +300 on the bank
        self._post_pair("2026-02-01", bank, self.acc_eq, 300.0)
        st = self._loan_statement(version)
        st.action_compute_lines()
        rows = {line.code: line for line in st.line_ids}
        self.assertAlmostEqual(rows["bank"].current_value, 300.0, places=2)
        self.assertAlmostEqual(rows["loan_short"].current_value, 0.0, places=2)
        # overdrawn: −700 by the period end
        self._post_pair("2026-11-01", self.acc_asset, bank, 1000.0)
        st.action_compute_lines()
        rows = {line.code: line for line in st.line_ids}
        self.assertAlmostEqual(rows["bank"].current_value, 0.0, places=2)
        self.assertAlmostEqual(rows["loan_short"].current_value, 700.0, places=2)
        self.assertTrue(rows["loan_short"].source_reconciles)
        # a movement window has no side: the account keeps its own code
        movement = st._cssk_account_balance_map("2026-01-01", "2026-12-31")
        self.assertIn("221019", movement)
        self.assertNotIn("221900", movement)

    def test_account_mapping_constraints(self):
        bank = self._account("221018", "asset_cash")
        Map = self.env["cssk.statement.account.map"]
        Map.create({"company_id": self.company.id, "account_id": bank.id,
                    "balance_side": "credit", "reported_code": "221900"})
        Map.create({"company_id": self.company.id, "account_id": bank.id,
                    "balance_side": "debit", "reported_code": "221000"})
        with self.assertRaises(ValidationError):
            Map.create({"company_id": self.company.id, "account_id": bank.id,
                        "balance_side": "any", "reported_code": "221000"})
        other = self._account("461003", "liability_non_current")
        with self.assertRaises(ValidationError):
            Map.create({"company_id": self.company.id, "account_id": other.id,
                        "reported_code": "-461200"})

    def test_drilldown_of_as_of_row_is_cumulative_and_skips_closing(self):
        """A balance-sheet row reports the CUMULATIVE balance without the
        year-end closing journals; its drill-down used to open only the
        period movement, in every journal, and so never reconciled once a
        prior year existed."""
        closing = self.env["account.journal"].create({
            "name": "Uzávierka", "code": "UZTS", "type": "general",
            "company_id": self.company.id,
        })
        self.company.l10n_cssk_closing_journal_ids = [(6, 0, closing.ids)]
        self._post_entry("2025-06-15", 700.0)
        self._post_entry("2026-06-15", 1000.0)
        self._post_pair("2025-12-31", self.acc_eq, self.acc_asset, 50.0,
                        journal=closing)
        st = self._make_statement()
        st.action_compute_lines()
        leaf = st.line_ids.filtered(lambda line: line.code == "a022")
        self.assertAlmostEqual(leaf.current_value, 1700.0, places=2)
        self.assertTrue(leaf.source_reconciles)
        found = self.env["account.move.line"].search(
            leaf.action_view_source_lines()["domain"])
        self.assertAlmostEqual(sum(found.mapped("balance")), 1700.0, places=2)
        self.assertNotIn(closing, found.journal_id)

    def test_footprint_follows_account_mapping(self):
        version = self._loan_version()
        loan = self._account("461004", "liability_non_current")
        self.env["cssk.statement.account.map"].create({
            "company_id": self.company.id, "account_id": loan.id,
            "reported_code": "461100",
        })
        move = self._post_pair("2026-03-01", self.acc_asset, loan, 100.0)
        self._loan_statement(version).action_compute_lines()
        line = move.line_ids.filtered(lambda ln: ln.account_id == loan)
        codes = [fp["code"] for fp in line._cssk_statutory_footprint()]
        self.assertIn("loan_long", codes)
        self.assertNotIn("loan_short", codes)

    def test_every_row_files_columns_that_add_up(self):
        """Totals and rows without a korekcia formula carry brutto and
        korekcia too: r001 SPOLU MAJETOK used to file 0 / 0 / netto."""
        version = self.env["cssk.fs.statement.version"].create({
            "name": "TST columns", "country_id": self.env.ref("base.sk").id,
            "statement_kind": "balance_sheet", "valid_from": "2025-01-01",
            "xml_template_ref_id": self.template.id,
            "xml_root_element": "FS", "xml_schema_optional": True,
            "line_def_ids": [
                (0, 0, {"code": "total", "name": "Spolu", "kind": "aggregate",
                        "aggregate_formula": "dhm + cash", "sequence": 5}),
                (0, 0, {"code": "dhm", "name": "DHM", "kind": "accounts",
                        "account_formula": "022",
                        "account_formula_correction": "082",
                        "sequence": 10}),
                (0, 0, {"code": "cash", "name": "Peniaze", "kind": "accounts",
                        "account_formula": "211", "sequence": 20}),
            ],
        })
        depreciation = self._account("082999", "asset_non_current")
        cash = self._account("211999", "asset_cash")
        self._post_entry("2026-03-01", 1000.0)
        self._post_pair("2026-06-01", self.acc_eq, depreciation, 200.0)
        self._post_pair("2026-06-02", cash, self.acc_eq, 500.0)
        st = self._loan_statement(version)
        st.action_compute_lines()
        rows = {line.code: line for line in st.line_ids}
        expected = {"dhm": (1000.0, 200.0, 800.0),
                    "cash": (500.0, 0.0, 500.0),
                    "total": (1500.0, 200.0, 1300.0)}
        for code, (brutto, korekcia, netto) in expected.items():
            row = rows[code]
            self.assertAlmostEqual(row.gross_value, brutto, places=2, msg=code)
            self.assertAlmostEqual(
                row.correction_value, korekcia, places=2, msg=code)
            self.assertAlmostEqual(row.current_value, netto, places=2, msg=code)

    def test_override_keeps_korekcia_and_derives_brutto(self):
        """An overridden netto keeps the ledger's korekcia, and brutto
        follows, so the three columns still satisfy netto = brutto -
        korekcia."""
        version = self.env["cssk.fs.statement.version"].create({
            "name": "TST brutto", "country_id": self.env.ref("base.sk").id,
            "statement_kind": "balance_sheet", "valid_from": "2025-01-01",
            "xml_template_ref_id": self.template.id,
            "xml_root_element": "FS", "xml_schema_optional": True,
            "line_def_ids": [
                (0, 0, {"code": "dhm", "name": "DHM", "kind": "accounts",
                        "account_formula": "022",
                        "account_formula_correction": "082",
                        "sequence": 10}),
            ],
        })
        depreciation = self._account("082999", "asset_non_current")
        self._post_entry("2026-03-01", 1000.0)
        self._post_pair("2026-06-01", self.acc_eq, depreciation, 200.0)
        st = self._loan_statement(version)
        st.action_compute_lines()
        row = st.line_ids.filtered(lambda line: line.code == "dhm")
        self.assertAlmostEqual(row.gross_value, 1000.0, places=2)
        self.assertAlmostEqual(row.correction_value, 200.0, places=2)
        self.assertAlmostEqual(row.current_value, 800.0, places=2)
        self.assertTrue(row.source_reconciles)
        row.write({"is_overridden": True, "manual_value": 750.0})
        st.action_compute_lines()
        row = st.line_ids.filtered(lambda line: line.code == "dhm")
        self.assertAlmostEqual(row.current_value, 750.0, places=2)
        self.assertAlmostEqual(row.correction_value, 200.0, places=2)
        self.assertAlmostEqual(row.gross_value, 950.0, places=2)
        self.assertAlmostEqual(
            row.gross_value - row.correction_value, row.current_value,
            places=2)

    def test_sections_split_combined_document(self):
        """A combined document splits by the TOP of each row's tree: a
        movement-basis row under an as-of total (A.VIII under SPOLU VLASTNÉ
        IMANIE A ZÁVÄZKY) stays in the balance-sheet part."""
        version = self.env["cssk.fs.statement.version"].create({
            "name": "TST Úč POD parts", "country_id": self.env.ref("base.sk").id,
            "statement_kind": "balance_sheet", "valid_from": "2025-01-01",
            "xml_template_ref_id": self.template.id,
            "xml_root_element": "FS", "xml_schema_optional": True,
            "line_def_ids": [
                (0, 0, {"code": "s079", "name": "Spolu pasíva",
                        "kind": "aggregate", "basis": "as_of",
                        "aggregate_formula": "s080 + s100", "sequence": 10}),
                (0, 0, {"code": "s080", "name": "VI", "kind": "accounts",
                        "basis": "as_of", "account_formula": "-411",
                        "sequence": 20}),
                (0, 0, {"code": "s100", "name": "A.VIII VH",
                        "kind": "accounts", "basis": "movement",
                        "account_formula": "-5,-6", "sequence": 30}),
                (0, 0, {"code": "r61", "name": "VH po zdanení",
                        "kind": "aggregate", "basis": "movement",
                        "aggregate_formula": "r01", "sequence": 40}),
                (0, 0, {"code": "r01", "name": "Výnosy", "kind": "accounts",
                        "basis": "movement", "account_formula": "-6",
                        "sequence": 50}),
            ],
        })
        st = self._loan_statement(version)
        st.action_compute_lines()
        parts = {line.code: line.in_movement_section for line in st.line_ids}
        self.assertEqual(parts, {"s079": False, "s080": False, "s100": False,
                                 "r61": True, "r01": True})
        self.assertEqual(set(st.balance_line_ids.mapped("code")),
                         {"s079", "s080", "s100"})
        self.assertEqual(set(st.movement_line_ids.mapped("code")),
                         {"r61", "r01"})
        for xmlid, section in (("cssk_fs_balance_action", "balance"),
                               ("cssk_fs_pl_action", "movement")):
            ctx = self.env.ref("l10n_cssk_fs_base.%s" % xmlid).context
            self.assertIn("'fs_section': '%s'" % section, ctx)
