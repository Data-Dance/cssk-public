from odoo import Command, fields
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestClosingJournals(AccountTestInvoicingCommon):
    """The four OCA reports leave out the company's year-end closing and
    archive journals, as the statutory statements do."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        # The 19.0 test chart gives the company two equity_unaffected
        # accounts, and the OCA wizards compute "the" unaffected-earnings
        # account as a single record — so every trial balance raises before
        # it starts (account_financial_report's own suite errors the same way
        # with nothing else installed). A real chart has one; keep one.
        unaffected = cls.env["account.account"].search([
            ("account_type", "=", "equity_unaffected"),
            ("company_ids", "in", cls.company.ids)])
        unaffected[1:].account_type = "equity"
        cls.misc = cls.company_data["default_journal_misc"]
        cls.closing = cls.env["account.journal"].create({
            "name": "Uzávierka", "code": "UZTS", "type": "general",
            "company_id": cls.company.id})
        cls.opening = cls.env["account.journal"].create({
            "name": "Otvorenie", "code": "OTTS", "type": "general",
            "company_id": cls.company.id})
        cls.company.l10n_cssk_closing_journal_ids = [
            Command.set((cls.closing | cls.opening).ids)]
        cls.asset = cls.env["account.account"].create({
            "name": "Test asset", "code": "022991",
            "account_type": "asset_non_current",
            "company_ids": [Command.set(cls.company.ids)]})
        cls.equity = cls.env["account.account"].create({
            "name": "Test equity", "code": "411991", "account_type": "equity",
            "company_ids": [Command.set(cls.company.ids)]})
        # FY 2025: 1000 acquired. Closed on 31.12. and reopened on 1.1.2026
        # the way a Czechoslovak ledger does; then 200 more in 2026.
        cls._post(cls.misc, "2025-05-01", cls.asset, cls.equity, 1000.0)
        cls._post(cls.closing, "2025-12-31", cls.equity, cls.asset, 1000.0)
        cls._post(cls.opening, "2026-01-01", cls.asset, cls.equity, 1000.0)
        cls._post(cls.misc, "2026-03-01", cls.asset, cls.equity, 200.0)

    @classmethod
    def _post(cls, journal, date, debit_acc, credit_acc, amount):
        move = cls.env["account.move"].create({
            "move_type": "entry", "journal_id": journal.id, "date": date,
            "line_ids": [
                Command.create({"account_id": debit_acc.id, "debit": amount}),
                Command.create({"account_id": credit_acc.id, "credit": amount}),
            ]})
        move.action_post()
        return move

    def _trial_balance(self, **vals):
        wizard = self.env["trial.balance.report.wizard"].with_company(
            self.company).create({
                "company_id": self.company.id,
                "date_from": "2026-01-01", "date_to": "2026-12-31",
                "target_move": "posted", **vals})
        data = wizard._prepare_report_trial_balance()
        data.update(wizard._prepare_report_data())
        rows = self.env["report.account_financial_report.trial_balance"]\
            ._get_report_values(wizard, data)["trial_balance"]
        return {row.get("code"): row for row in rows}

    def test_default_is_on_when_the_company_names_journals(self):
        wizard = self.env["trial.balance.report.wizard"].with_company(
            self.company).create({"company_id": self.company.id,
                                  "date_from": "2026-01-01",
                                  "date_to": "2026-12-31"})
        self.assertTrue(wizard.cssk_exclude_closing_journals)

    def test_opening_entry_is_the_opening_balance_not_movement(self):
        row = self._trial_balance()["022991"]
        self.assertAlmostEqual(row["initial_balance"], 1000.0, places=2)
        self.assertAlmostEqual(row["debit"], 200.0, places=2)
        self.assertAlmostEqual(row["ending_balance"], 1200.0, places=2)
        # The OCA behaviour, kept a tick away: the reopening is movement.
        row = self._trial_balance(cssk_exclude_closing_journals=False)["022991"]
        self.assertAlmostEqual(row["initial_balance"], 0.0, places=2)
        self.assertAlmostEqual(row["debit"], 1200.0, places=2)
        self.assertAlmostEqual(row["ending_balance"], 1200.0, places=2)

    def test_an_explicit_journal_choice_is_honoured(self):
        row = self._trial_balance(
            journal_ids=[Command.set(self.opening.ids)])["022991"]
        self.assertAlmostEqual(row["debit"], 1000.0, places=2)

    def test_open_items_leave_out_the_archive(self):
        """A migrated opening balance and the archived documents it sums up
        must not both count as open."""
        receivable = self.company_data["default_account_receivable"]
        partner = self.partner_a
        for journal, date in ((self.closing, "2024-06-01"),
                              (self.misc, "2025-01-01")):
            move = self.env["account.move"].create({
                "move_type": "entry", "journal_id": journal.id, "date": date,
                "line_ids": [
                    Command.create({"account_id": receivable.id,
                                    "partner_id": partner.id, "debit": 300.0}),
                    Command.create({"account_id": self.equity.id,
                                    "credit": 300.0}),
                ]})
            move.action_post()

        def open_total(exclude):
            wizard = self.env["open.items.report.wizard"].with_company(
                self.company).create({
                    "company_id": self.company.id,
                    "date_at": fields.Date.to_date("2026-12-31"),
                    "account_ids": [Command.set(receivable.ids)],
                    "target_move": "posted",
                    "cssk_exclude_closing_journals": exclude})
            data = wizard._prepare_report_open_items()
            data.update(wizard._prepare_report_data())
            res = self.env["report.account_financial_report.open_items"]\
                ._get_report_values(wizard, data)
            totals = res["total_amount"]
            return totals[receivable.id]["residual"] \
                if receivable.id in totals else 0.0

        self.assertAlmostEqual(open_total(False), 600.0, places=2)
        self.assertAlmostEqual(open_total(True), 300.0, places=2)
