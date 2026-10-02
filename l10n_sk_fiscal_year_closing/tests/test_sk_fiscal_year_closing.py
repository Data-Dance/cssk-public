# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestSkZavierka(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.template = cls.env.ref("l10n_sk_fiscal_year_closing.fyc_template_sk")
        cls.journal = cls.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", cls.company.id)], limit=1
        )

    def _account(self, code):
        return self.env["account.account"].search(
            [("company_ids", "in", self.company.id), ("code", "=", code)], limit=1
        )

    def _post_result(self, expense=400.0, income=1000.0):
        """A year with a profit: 1000 revenue against 400 costs."""
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "date": "2025-06-30",
                "journal_id": self.journal.id,
                "company_id": self.company.id,
                "line_ids": [
                    Command.create(
                        {
                            "account_id": self._account("501000").id,
                            "debit": expense,
                            "credit": 0.0,
                        }
                    ),
                    Command.create(
                        {
                            "account_id": self._account("221000").id,
                            "debit": income - expense,
                            "credit": 0.0,
                        }
                    ),
                    Command.create(
                        {
                            "account_id": self._account("602000").id,
                            "debit": 0.0,
                            "credit": income,
                        }
                    ),
                ],
            }
        )
        move.action_post()
        return move

    def _closing(self):
        return self.env["account.fiscalyear.closing"].create(
            {
                "name": "Závierka 2025",
                "company_id": self.company.id,
                "year": 2025,
                "date_start": "2025-01-01",
                "date_end": "2025-12-31",
                "date_opening": "2026-01-01",
                "closing_template_id": self.template.id,
                "check_draft_moves": False,
            }
        )

    # ------------------------------------------------------------------
    def test_zavierkove_ucty_are_postable(self):
        """l10n_sk ships 701/702/710 as off_balance, which Odoo refuses to mix
        with ordinary accounts — no závierka could be posted at all."""
        for code in ("701000", "702000", "710000"):
            self.assertEqual(
                self._account(code).account_type,
                "equity",
                f"{code} must not stay off_balance",
            )

    def test_template_ships_for_the_sk_chart(self):
        self.assertEqual(self.template.chart_template, "sk")
        codes = self.template.move_config_ids.mapped("code")
        self.assertEqual(set(codes), {"SK_PL", "SK_CLOSING", "SK_OPENING"})

    def test_template_uses_the_three_zavierkove_ucty(self):
        by_code = {c.code: c for c in self.template.move_config_ids}
        pl_dests = by_code["SK_PL"].mapping_ids.mapped("dest_account")
        self.assertEqual(set(pl_dests), {"710000"})
        closing_dests = by_code["SK_CLOSING"].mapping_ids.mapped("dest_account")
        self.assertEqual(set(closing_dests), {"702000"})
        # The opening is the inverse of the closing, rerouted to 701 by our override.
        self.assertEqual(by_code["SK_OPENING"].inverse, "SK_CLOSING")
        self.assertEqual(by_code["SK_OPENING"].move_type, "opening")

    def test_closing_result_lands_on_710(self):
        self._post_result()
        closing = self._closing()
        # The engine copies the template through an onchange, not an action.
        closing.onchange_template_id()
        closing.button_calculate()

        pl_config = closing.move_config_ids.filtered(lambda c: c.code == "SK_PL")
        self.assertTrue(pl_config.move_id, "the loss & profit move must be created")
        lines_710 = pl_config.move_id.line_ids.filtered(
            lambda line: line.account_id.code == "710000"
        )
        self.assertTrue(lines_710)
        # Closing the P&L credits 501 (400) and debits 602 (1000), so the
        # counterpart on 710 is a CREDIT of 600 — a profit.
        self.assertEqual(sum(lines_710.mapped("balance")), -600.0)

    def test_closing_mirrors_every_account_on_702(self):
        """702 must carry the counter-entry, not just an omitted net."""
        self._post_result()
        closing = self._closing()
        closing.onchange_template_id()
        closing.button_calculate()

        config = closing.move_config_ids.filtered(lambda c: c.code == "SK_CLOSING")
        lines = config.move_id.line_ids
        on_702 = lines.filtered(lambda line: line.account_id.code == "702000")
        self.assertTrue(on_702, "702 must appear in the closing entry")
        # One mirror per closed account, and 702 nets to zero (bilančná rovnosť).
        self.assertEqual(len(on_702), len(lines) - len(on_702))
        self.assertEqual(sum(on_702.mapped("balance")), 0.0)

    def test_mirrors_use_each_mapping_own_destination(self):
        """Copilot review: mirroring everything onto the first dest is wrong
        when a config maps different sources to different accounts."""
        self._post_result()
        closing = self._closing()
        closing.onchange_template_id()
        pl = closing.move_config_ids.filtered(lambda c: c.code == "SK_PL")
        # Send trieda 6 to 702 instead of 710, leaving trieda 5 on 710.
        other_dest = self._account("702000")
        pl.mapping_ids.filtered(lambda m: m.src_accounts == "6%").dest_account_id = (
            other_dest
        )
        closing.button_calculate()

        lines = pl.move_id.line_ids
        # 501 (trieda 5) mirrors onto 710; 602 (trieda 6) onto 702.
        self.assertEqual(
            sum(lines.filtered(lambda l: l.account_id.code == "710000").mapped("balance")),
            400.0,
        )
        self.assertEqual(
            sum(lines.filtered(lambda l: l.account_id.code == "702000").mapped("balance")),
            -1000.0,
        )

    def test_opening_move_runs_through_701_not_702(self):
        """The whole reason this module overrides inverse_move_prepare."""
        self._post_result()
        closing = self._closing()
        # The engine copies the template through an onchange, not an action.
        closing.onchange_template_id()
        closing.button_calculate()

        opening = closing.move_config_ids.filtered(lambda c: c.code == "SK_OPENING")
        self.assertTrue(opening.move_id, "the opening move must be created")
        codes = set(opening.move_id.line_ids.mapped("account_id.code"))
        self.assertIn("701000", codes, "the opening must run through 701")
        self.assertNotIn(
            "702000", codes, "702 belongs to the closing, not to the opening"
        )
