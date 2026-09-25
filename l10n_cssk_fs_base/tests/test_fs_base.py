from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
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
