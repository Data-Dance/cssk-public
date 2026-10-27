# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged

from ..hooks import post_init_hook
from ..models.account_chart_template import SK_MOVE_TEMPLATES


@tagged("post_install", "-at_install")
class TestSkMoveTemplates(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.templates = cls.env["account.move.template"].search(
            [("company_id", "=", cls.company.id)]
        )

    def _template(self, xmlid):
        return self.env.ref(f"account.{self.company.id}_{xmlid}")

    def test_all_templates_loaded_on_the_sk_chart(self):
        """Every declared predkontácia exists for a company on the SK chart."""
        for xmlid in SK_MOVE_TEMPLATES:
            template = self._template(xmlid)
            self.assertEqual(template.company_id, self.company)
            self.assertEqual(template.journal_id.type, "general")

    def test_lines_resolve_to_slovak_accounts(self):
        """Account xmlids deref to this company's own chart accounts."""
        template = self._template("sk_amt_pokladnica_na_cestu")
        lines = template.line_ids.sorted("sequence")
        # The chart creates no cash journal (the test company gets one only
        # after the chart load), so the cash leg is the summary 211000 here.
        self.assertEqual(lines[0].account_id, self.company.transfer_account_id)
        self.assertEqual(lines[1].account_id.code, "211000")
        self.assertEqual(lines.mapped("move_line_type"), ["dr", "cr"])
        for line in lines:
            self.assertEqual(line.account_id.company_ids, self.company)

    def test_money_in_transit_avoids_the_bank_suspense_account(self):
        """261000 is the SK chart's bank suspense account, where unreconciled
        statement lines wait; transfers go through Liquidity Transfer."""
        suspense = self.company.account_journal_suspense_account_id
        self.assertEqual(suspense.code, "261000")
        transfer = self.company.transfer_account_id
        self.assertTrue(transfer.reconcile)
        self.assertTrue(transfer.code.startswith("261"))
        self.assertNotEqual(transfer, suspense)
        for xmlid in ("sk_amt_pokladnica_na_cestu", "sk_amt_cesta_na_banku",
                      "sk_amt_banka_na_cestu", "sk_amt_cesta_na_pokladnicu"):
            accounts = self._template(xmlid).line_ids.account_id
            self.assertIn(transfer, accounts, xmlid)
            self.assertNotIn(suspense, accounts, xmlid)

    def test_bank_legs_use_the_bank_journal_account(self):
        """221000 is a summary account no bank journal posts to."""
        bank = self.company_data["default_journal_bank"]
        self.assertNotEqual(bank.default_account_id.code, "221000")
        for xmlid in ("sk_amt_cesta_na_banku", "sk_amt_banka_na_cestu"):
            self.assertIn(
                bank.default_account_id,
                self._template(xmlid).line_ids.account_id,
                xmlid,
            )

    def test_upgrade_repoints_the_shipped_accounts_only(self):
        """Templates created before 19.0.1.1.0 carry 261000 / 221000."""
        Chart = self.env["account.chart.template"]
        # The cash journal the test company got after its chart load would
        # be picked up too; settle that first, then count only our edits.
        Chart._l10n_sk_fix_move_template_accounts(self.company)
        old_transit = self.env.ref(f"account.{self.company.id}_chart_sk_261000")
        old_bank = self.env.ref(f"account.{self.company.id}_chart_sk_221000")
        template = self._template("sk_amt_cesta_na_banku")
        bank_line, transit_line = template.line_ids.sorted("sequence")
        bank_line.account_id = old_bank
        transit_line.account_id = old_transit
        # An account the accountant chose is not shipped data.
        edited = self._template("sk_amt_banka_na_cestu").line_ids.sorted("sequence")[0]
        own = self.env["account.account"].create({
            "code": "261900", "name": "Own transit", "account_type": "asset_current",
            "company_ids": [self.company.id],
        })
        edited.account_id = own

        self.assertEqual(Chart._l10n_sk_fix_move_template_accounts(self.company), 2)

        self.assertEqual(
            bank_line.account_id, self.company_data["default_journal_bank"].default_account_id
        )
        self.assertEqual(transit_line.account_id, self.company.transfer_account_id)
        self.assertEqual(edited.account_id, own)
        self.assertEqual(Chart._l10n_sk_fix_move_template_accounts(self.company), 0)

    def test_second_leg_mirrors_the_entered_amount(self):
        """Line 1 is typed, the rest compute from it — a one-amount posting."""
        for xmlid in SK_MOVE_TEMPLATES:
            lines = self._template(xmlid).line_ids.sorted("sequence")
            self.assertEqual(lines[0].type, "input")
            for line in lines[1:]:
                self.assertEqual(line.type, "computed")
                self.assertEqual(line.python_code, "L1")

    def test_templates_are_balanced(self):
        """Each predkontácia posts an equal debit and credit."""
        for xmlid in SK_MOVE_TEMPLATES:
            lines = self._template(xmlid).line_ids
            self.assertEqual(
                len(lines.filtered(lambda line: line.move_line_type == "dr")),
                len(lines.filtered(lambda line: line.move_line_type == "cr")),
                f"{xmlid} is not balanced",
            )

    def test_post_init_hook_recreates_templates_for_an_existing_company(self):
        """The install path for companies that already had the SK chart.

        The chart-template path is exercised by every other test here; this is
        the other half — a company whose chart predates the module. Deleting the
        records and re-running the hook reproduces them under the same xmlids.
        """
        self.env["account.move.template"].search(
            [("company_id", "=", self.company.id)]
        ).unlink()
        self.assertFalse(
            self.env.ref(
                f"account.{self.company.id}_sk_amt_vh_zisk", raise_if_not_found=False
            )
        )

        post_init_hook(self.env)

        for xmlid in SK_MOVE_TEMPLATES:
            template = self._template(xmlid)
            self.assertEqual(template.company_id, self.company)
            self.assertTrue(template.line_ids)
            self.assertTrue(all(template.line_ids.mapped("account_id")))

    def test_post_init_hook_is_idempotent(self):
        """Re-running the hook duplicates neither templates nor their lines."""
        template = self._template("sk_amt_vh_zisk")
        before = self.env["account.move.template"].search_count(
            [("company_id", "=", self.company.id)]
        )
        before_lines = len(template.line_ids)

        post_init_hook(self.env)

        self.assertEqual(
            self.env["account.move.template"].search_count(
                [("company_id", "=", self.company.id)]
            ),
            before,
        )
        self.assertEqual(len(template.line_ids), before_lines)

    def test_post_init_hook_preserves_accountant_edits(self):
        """A shipped predkontácia is data, not code — never revert the customer.

        The loader rewrites any record it is handed (its noupdate flag only
        applies on a module upgrade), so the hook has to skip what already
        exists rather than reload it.
        """
        template = self._template("sk_amt_vh_zisk")
        template.name = "Preúčtovanie zisku — upravené"
        template.line_ids[0].name = "Vlastný popis"

        post_init_hook(self.env)

        self.assertEqual(template.name, "Preúčtovanie zisku — upravené")
        self.assertEqual(template.line_ids[0].name, "Vlastný popis")

    def test_wizard_generates_a_balanced_entry(self):
        """End-to-end: run a predkontácia and check the move it produces."""
        template = self._template("sk_amt_vh_zisk")
        wizard = self.env["account.move.template.run"].create(
            {"template_id": template.id}
        )
        wizard.load_lines()
        wizard.line_ids.filtered(lambda line: line.sequence == 1).amount = 1500.0
        action = wizard.generate_move()

        move = self.env["account.move"].browse(action["res_id"])
        self.assertEqual(move.journal_id.type, "general")
        by_account = {line.account_id.code: line for line in move.line_ids}
        self.assertEqual(by_account["431000"].debit, 1500.0)
        self.assertEqual(by_account["428000"].credit, 1500.0)
        self.assertEqual(sum(move.line_ids.mapped("balance")), 0.0)
