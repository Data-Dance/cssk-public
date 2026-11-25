# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestCzClosingTemplate(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.template = cls.env.ref("l10n_cz_fiscal_year_closing.fyc_template_cz")
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
                            "debit": max(income - expense, 0.0),
                            "credit": max(expense - income, 0.0),
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
                "name": "Závěrka 2025",
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
        """l10n_cz ships 701/702/710 as off_balance, which Odoo refuses to mix
        with ordinary accounts, so no závěrka could be posted at all."""
        for code in ("701000", "702000", "710000"):
            self.assertEqual(
                self._account(code).account_type,
                "equity",
                f"{code} must not stay off_balance",
            )

    def test_template_ships_for_the_cz_chart(self):
        self.assertEqual(self.template.chart_template, "cz")
        codes = self.template.move_config_ids.mapped("code")
        self.assertEqual(set(codes), {"CZ_PL", "CZ_CLOSING", "CZ_OPENING"})

    def test_template_uses_the_three_zavierkove_ucty(self):
        by_code = {c.code: c for c in self.template.move_config_ids}
        pl_dests = by_code["CZ_PL"].mapping_ids.mapped("dest_account")
        self.assertEqual(set(pl_dests), {"710000"})
        closing_dests = by_code["CZ_CLOSING"].mapping_ids.mapped("dest_account")
        self.assertEqual(set(closing_dests), {"702000"})
        # The opening is the inverse of the closing, rerouted to 701 by our override.
        self.assertEqual(by_code["CZ_OPENING"].inverse, "CZ_CLOSING")
        self.assertEqual(by_code["CZ_OPENING"].move_type, "opening")

    def test_closing_result_lands_on_710(self):
        self._post_result()
        closing = self._closing()
        # The engine copies the template through an onchange, not an action.
        closing.onchange_template_id()
        closing.button_calculate()

        pl_config = closing.move_config_ids.filtered(lambda c: c.code == "CZ_PL")
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

        config = closing.move_config_ids.filtered(lambda c: c.code == "CZ_CLOSING")
        lines = config.move_id.line_ids
        on_702 = lines.filtered(lambda line: line.account_id.code == "702000")
        self.assertTrue(on_702, "702 must appear in the closing entry")
        # One mirror per closed account, and 702 nets to zero.
        self.assertEqual(len(on_702), len(lines) - len(on_702))
        self.assertEqual(sum(on_702.mapped("balance")), 0.0)

    def test_mirrors_use_each_mapping_own_destination(self):
        """Code review: mirroring everything onto the first dest is wrong
        when a config maps different sources to different accounts."""
        self._post_result()
        closing = self._closing()
        closing.onchange_template_id()
        pl = closing.move_config_ids.filtered(lambda c: c.code == "CZ_PL")
        # Send třída 6 to 702 instead of 710, leaving třída 5 on 710.
        other_dest = self._account("702000")
        pl.mapping_ids.filtered(lambda m: m.src_accounts == "6%").dest_account_id = (
            other_dest
        )
        closing.button_calculate()

        lines = pl.move_id.line_ids
        # 501 (třída 5) mirrors onto 710; 602 (třída 6) onto 702.
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

        opening = closing.move_config_ids.filtered(lambda c: c.code == "CZ_OPENING")
        self.assertTrue(opening.move_id, "the opening move must be created")
        codes = set(opening.move_id.line_ids.mapped("account_id.code"))
        self.assertIn("701000", codes, "the opening must run through 701")
        self.assertNotIn(
            "702000", codes, "702 belongs to the closing, not to the opening"
        )

    def _opening_after_close(self, expense, income):
        self._post_result(expense=expense, income=income)
        closing = self._closing()
        closing.onchange_template_id()
        closing.button_calculate()
        opening = closing.move_config_ids.filtered(lambda c: c.code == "CZ_OPENING")
        self.assertTrue(opening.move_id, "the opening move must be created")
        return opening.move_id

    def test_opening_reopens_a_profit_on_431(self):
        """ČÚS 002 bod 2.1.3: at the opening the result goes to an account
        of group 43, a profit na vrub 701 and ve prospěch 431. A plain
        reversal of the closing would reopen it on 710."""
        move = self._opening_after_close(expense=400.0, income=1000.0)
        codes = set(move.line_ids.mapped("account_id.code"))
        self.assertNotIn("710000", codes, "710 has no place in the new year")
        on_431 = move.line_ids.filtered(lambda l: l.account_id.code == "431000")
        self.assertEqual(sum(on_431.mapped("balance")), -600.0,
                         "a profit of 600 is a CREDIT on 431")
        # 701 still carries every counterpart, so it nets to zero.
        on_701 = move.line_ids.filtered(lambda l: l.account_id.code == "701000")
        self.assertEqual(sum(on_701.mapped("balance")), 0.0)

    def test_opening_reopens_a_loss_on_431(self):
        """A loss: ve prospěch 701 and na vrub 431."""
        move = self._opening_after_close(expense=1000.0, income=400.0)
        on_431 = move.line_ids.filtered(lambda l: l.account_id.code == "431000")
        self.assertEqual(sum(on_431.mapped("balance")), 600.0,
                         "a loss of 600 is a DEBIT on 431")
        self.assertNotIn("710000", set(move.line_ids.mapped("account_id.code")))

    def test_pre_close_flags_a_balance_on_431(self):
        account_431 = self.env["account.account"].search(
            [("company_ids", "in", self.company.id), ("code", "=like", "431%")], limit=1
        )
        other = self.env["account.account"].search(
            [("company_ids", "in", self.company.id), ("code", "=like", "428%")], limit=1
        )
        closing = self._closing()
        self.assertNotIn("431", closing.l10n_cz_pre_close_warning or "")
        move = self.env["account.move"].create({
            "journal_id": self.journal.id,
            "date": "2025-06-30",
            "line_ids": [
                Command.create({"account_id": account_431.id, "debit": 100.0}),
                Command.create({"account_id": other.id, "credit": 100.0}),
            ],
        })
        closing.invalidate_recordset(["l10n_cz_pre_close_warning"])
        # A draft entry is reported, whatever language the message is in,
        # and a draft does not count towards the balance of 431.
        self.assertTrue(closing.l10n_cz_pre_close_warning)
        self.assertNotIn("431", closing.l10n_cz_pre_close_warning)
        move.action_post()
        closing.invalidate_recordset(["l10n_cz_pre_close_warning"])
        self.assertIn("431", closing.l10n_cz_pre_close_warning)

    def test_pre_close_list_is_for_czech_companies_only(self):
        """Both country modules can be installed; each speaks for its own."""
        closing = self._closing()
        self.env["account.move"].create({
            "journal_id": self.journal.id,
            "date": "2025-06-30",
            "line_ids": [
                Command.create({"account_id": self._account("501000").id, "debit": 1.0}),
                Command.create({"account_id": self._account("221000").id, "credit": 1.0}),
            ],
        })
        closing.invalidate_recordset(["l10n_cz_pre_close_warning"])
        self.assertTrue(closing.l10n_cz_pre_close_warning)
        self.company.account_fiscal_country_id = self.env.ref("base.sk")
        closing.invalidate_recordset(["l10n_cz_pre_close_warning"])
        self.assertFalse(closing.l10n_cz_pre_close_warning)

    def test_a_company_on_another_chart_keeps_the_engine_behaviour(self):
        """The overrides are gated on the Czech chart."""
        config = self.env["account.fiscalyear.closing.config"]
        self.assertTrue(hasattr(config, "_l10n_cz_is_cz"))
        closing = self._closing()
        closing.onchange_template_id()
        pl = closing.move_config_ids.filtered(lambda c: c.code == "CZ_PL")
        self.assertTrue(pl._l10n_cz_is_cz())
        self.company.chart_template = "generic_coa"
        self.assertFalse(pl._l10n_cz_is_cz())
