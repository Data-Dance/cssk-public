# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestCzFiscalYearClosing(AccountTestInvoicingCommon):
    """The three závěrkové účty must be postable alongside ordinary accounts."""

    chart_template = "cz"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

    def _account(self, code):
        return self.env["account.account"].search([
            ("code", "=", code), ("company_ids", "in", self.company.id),
        ], limit=1)

    def test_the_closing_accounts_are_not_off_balance(self):
        """As shipped they are, and nothing can be posted to them.

        `l10n_cz` gives 701000/702000/710000 `account_type = off_balance`, and
        `account_move_line._check_off_balance` refuses any entry mixing an
        off-balance account with another — which is what a Czech závěrka is.
        """
        for code in ("701000", "702000", "710000"):
            account = self._account(code)
            self.assertTrue(account, "%s is missing from the CZ chart" % code)
            self.assertEqual(
                account.account_type, "equity",
                "%s is still off_balance, so no závěrka can be posted" % code,
            )

    def test_a_closing_entry_actually_posts(self):
        """The property the retype exists for, tested by posting one.

        Asserting the account type alone would pass against a constraint that
        had moved elsewhere. This posts the shape that used to be refused: a
        result account closed against 710.
        """
        revenue = self.company_data["default_account_revenue"]
        move = self.env["account.move"].with_company(self.company).create({
            "move_type": "entry",
            "journal_id": self.company_data["default_journal_misc"].id,
            "date": "2025-12-31",
            "line_ids": [
                (0, 0, {"account_id": revenue.id, "debit": 1000.0,
                        "credit": 0.0, "name": "Uzavření třídy 6"}),
                (0, 0, {"account_id": self._account("710000").id,
                        "debit": 0.0, "credit": 1000.0, "name": "Účet Z+Z"}),
            ],
        })
        move.action_post()
        self.assertEqual(
            move.state, "posted",
            "a result account closed against 710 must post — this is the "
            "entry the off_balance constraint refused",
        )

    def test_an_opening_balance_posts_from_701(self):
        """The other half: rozvahové účty reopened from 701.

        Measured on a seven-year import before this module existed, the
        constraint failed 82 documents and left the trial balance out by
        698 169 015, because the result accounts were never closed.
        """
        receivable = self.company_data["default_account_receivable"]
        move = self.env["account.move"].with_company(self.company).create({
            "move_type": "entry",
            "journal_id": self.company_data["default_journal_misc"].id,
            "date": "2026-01-01",
            "line_ids": [
                (0, 0, {"account_id": receivable.id, "debit": 5000.0,
                        "credit": 0.0, "name": "Počáteční stav"}),
                (0, 0, {"account_id": self._account("701000").id,
                        "debit": 0.0, "credit": 5000.0, "name": "PÚR"}),
            ],
        })
        move.action_post()
        self.assertEqual(move.state, "posted")

    def test_the_retype_is_idempotent_and_reports_what_it_changed(self):
        """It runs on install and on any later chart load; it must not thrash.

        Also: running it when there is nothing to do must return 0 rather than
        claim work, since the count is what a log line reports.
        """
        from odoo.addons.l10n_cz_fiscal_year_closing.hooks import retype
        self.assertEqual(
            retype(self.env), 0,
            "nothing should be left off_balance after installation",
        )
        self._account("710000").account_type = "off_balance"
        self.assertEqual(retype(self.env), 1, "a reverted account was not fixed")
        self.assertEqual(self._account("710000").account_type, "equity")
