# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import AccessError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestInteractiveLedger(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Service = cls.env["account.financial.report.interactive"]
        cls.company = cls.company_data["company"]
        cls.income = cls.company_data["default_account_revenue"]
        cls.receivable = cls.company_data["default_account_receivable"]
        # Last year and this year: 100 + 50 of sales (no taxes).
        cls.init_invoice("out_invoice", invoice_date="2025-06-01", amounts=[100.0], post=True)
        cls.init_invoice("out_invoice", invoice_date="2026-02-01", amounts=[50.0], post=True)
        for day in range(1, 6):
            cls.init_invoice("out_invoice", invoice_date="2026-03-%02d" % day, amounts=[10.0], post=True)

    def _data(self, **extra):
        data = {
            "company_id": self.company.id,
            "date_from": "2026-03-01", "date_to": "2026-03-31",
            "fy_start_date": "2026-01-01",
            "only_posted_moves": True,
            "account_ids": [], "partner_ids": [], "journal_ids": [],
        }
        data.update(extra)
        return data

    def _row(self, result, account):
        return next(r for r in result["accounts"] if r["id"] == account.id)

    def test_profit_and_loss_restarts_at_the_fiscal_year(self):
        result = self.Service.get_accounts(self._data())
        income = self._row(result, self.income)
        # Opening = this fiscal year only (50), not last year's 100.
        self.assertAlmostEqual(income["opening"], -50.0)
        self.assertAlmostEqual(income["credit"], 50.0)
        self.assertAlmostEqual(income["closing"], -100.0)
        receivable = self._row(result, self.receivable)
        self.assertAlmostEqual(receivable["opening"], 150.0)      # balance sheet: everything before
        # Last year's profit sits on the unaffected earnings account, so the
        # opening and closing columns still balance.
        self.assertAlmostEqual(result["totals"]["opening"], 0.0)
        self.assertAlmostEqual(result["totals"]["closing"], 0.0)

    def test_pages_carry_the_running_balance(self):
        data = self._data()
        opening = self._row(self.Service.get_accounts(data), self.receivable)["opening"]
        first = self.Service.get_lines(data, self.receivable.id, 0, opening, 2)
        self.assertEqual((first["total"], first["offset"], len(first["lines"])), (5, 2, 2))
        balances = [line["balance"] for line in first["lines"]]
        rest = self.Service.get_lines(data, self.receivable.id, first["offset"], balances[-1], 10)
        balances += [line["balance"] for line in rest["lines"]]
        self.assertEqual(len(balances), 5)
        self.assertAlmostEqual(balances[0], opening + 10.0)
        self.assertAlmostEqual(balances[-1], self._row(self.Service.get_accounts(data), self.receivable)["closing"])

    def test_journal_filter(self):
        other = self.company_data["default_journal_misc"]
        result = self.Service.get_accounts(self._data(journal_ids=[other.id], hide_account_at_0=True))
        self.assertFalse(result["accounts"])

    def test_account_domain_lists_the_period_items(self):
        domain = self.Service.get_account_domain(self._data(), self.receivable.id)
        self.assertEqual(self.env["account.move.line"].search_count(domain), 5)

    def test_needs_accounting_rights(self):
        user = self.env["res.users"].create({
            "name": "No accounting", "login": "no_accounting",
            "group_ids": [(6, 0, [self.env.ref("base.group_user").id])],
            "company_id": self.company.id, "company_ids": [(6, 0, self.company.ids)]})
        with self.assertRaises(AccessError):
            self.Service.with_user(user).get_accounts(self._data())

    def test_wizard_opens_the_client_action(self):
        # The OCA wizard expects ONE unaffected earnings account per company;
        # the test chart has two.
        unaffected = self.env["account.account"].search([
            ("account_type", "=", "equity_unaffected"), ("company_ids", "in", self.company.ids)])
        unaffected[1:].account_type = "equity"
        wizard = self.env["general.ledger.report.wizard"].with_context(
                allowed_company_ids=self.company.ids).create({
            "company_id": self.company.id, "date_from": "2026-03-01", "date_to": "2026-03-31"})
        action = wizard.button_interactive()
        self.assertEqual(action["tag"], "afr_interactive_ledger")
        self.assertEqual(action["params"]["data"]["date_from"], "2026-03-01")
        result = self.Service.get_accounts(action["params"]["data"])
        self.assertTrue(result["accounts"])

    def test_previous_periods_step_back_by_whole_months(self):
        data = self.Service._normalize(self._data(date_from="2026-03-01", date_to="2026-03-31"))
        periods = self.Service._comparison_periods(data, {"mode": "previous", "count": 2})
        self.assertEqual([(str(a), str(b)) for _l, a, b in periods],
                         [("2026-02-01", "2026-02-28"), ("2026-01-01", "2026-01-31")])
        quarter = self.Service._normalize(self._data(date_from="2026-04-01", date_to="2026-06-30"))
        (_l, a, b), = self.Service._comparison_periods(quarter, {"mode": "previous", "count": 1})
        self.assertEqual((str(a), str(b)), ("2026-01-01", "2026-03-31"))

    def test_partial_months_step_back_by_days(self):
        data = self.Service._normalize(self._data(date_from="2026-03-10", date_to="2026-03-19"))
        (_l, a, b), = self.Service._comparison_periods(data, {"mode": "previous", "count": 1})
        self.assertEqual((str(a), str(b)), ("2026-02-28", "2026-03-09"))

    def test_same_period_earlier_years(self):
        data = self.Service._normalize(self._data())
        periods = self.Service._comparison_periods(data, {"mode": "last_year", "count": 2})
        self.assertEqual([str(a) for _l, a, _b in periods], ["2025-03-01", "2024-03-01"])

    def test_comparison_values_and_growth(self):
        result = self.Service.get_accounts(self._data(), {"mode": "previous", "count": 2})
        self.assertEqual(len(result["comparison_labels"]), 2)
        income = self._row(result, self.income)
        self.assertAlmostEqual(income["net"], -50.0)            # March: 5 x 10
        self.assertEqual(income["compare"], [-50.0, 0.0])        # February 50, January nothing
        self.assertEqual(income["growth"], 0.0)
        self.assertEqual(income["growth_sense"], 1)
        self.assertEqual(self._row(result, self.receivable)["growth_sense"], 0)

    def test_rising_revenue_reads_as_positive_growth(self):
        """Growth is measured on the account's natural side: more revenue is a
        positive figure, not a negative one."""
        result = self.Service.get_accounts(
            self._data(date_from="2026-01-01", date_to="2026-12-31"), {"mode": "last_year", "count": 1})
        income = self._row(result, self.income)
        self.assertEqual(income["compare"], [-100.0])      # 2025: 100
        self.assertAlmostEqual(income["net"], -100.0)       # 2026: 50 + 5 x 10
        self.assertEqual(income["growth"], 0.0)
        self.init_invoice("out_invoice", invoice_date="2026-04-01", amounts=[50.0], post=True)
        income = self._row(self.Service.get_accounts(
            self._data(date_from="2026-01-01", date_to="2026-12-31"), {"mode": "last_year", "count": 1}),
            self.income)
        self.assertEqual(income["growth"], 50.0)            # 150 vs 100: +50 %, not -50 %

    def test_account_moving_only_in_a_compared_period_is_listed(self):
        """March 2027 in a 2027 fiscal year: the income account has no opening
        and no movement, only March 2026 to compare with - it must be listed."""
        result = self.Service.get_accounts(
            self._data(date_from="2027-03-01", date_to="2027-03-31", fy_start_date="2027-01-01",
                       hide_account_at_0=True),
            {"mode": "last_year", "count": 1})
        income = self._row(result, self.income)
        self.assertEqual((income["opening"], income["net"]), (0.0, 0.0))
        self.assertEqual(income["compare"], [-50.0])

    def test_period_arrows(self):
        data = self._data(date_from="2026-03-01", date_to="2026-03-31")
        back = self.Service.shift_period(data, -1)
        self.assertEqual((back["date_from"], back["date_to"]), ("2026-02-01", "2026-02-28"))
        across = self.Service.shift_period(self._data(date_from="2026-01-01", date_to="2026-01-31"), -1)
        self.assertEqual((across["date_from"], across["fy_start_date"]), ("2025-12-01", "2025-01-01"))
        week = self.Service.shift_period(self._data(date_from="2026-03-02", date_to="2026-03-08"), 1)
        self.assertEqual((week["date_from"], week["date_to"]), ("2026-03-09", "2026-03-15"))
        # The shifted data drives the same service.
        self.assertTrue(self.Service.get_accounts(back)["accounts"])

    def test_statement_action_for_a_partner(self):
        action = self.Service.statement_action(self._data(), self.partner_a.id)
        installed = self.env.ref("partner_statement.activity_statement_wizard_action",
                                 raise_if_not_found=False)
        self.assertEqual(bool(action), bool(installed))
        self.assertEqual(self.Service.get_accounts(self._data())["statements"], bool(installed))
        if action:
            self.assertEqual(action["res_model"], "activity.statement.wizard")
            self.assertEqual(action["context"]["active_ids"], [self.partner_a.id])
            self.assertEqual(action["context"]["default_date_start"], "2026-03-01")
            wizard = self.env["activity.statement.wizard"].with_context(action["context"]).create({})
            self.assertEqual(str(wizard.date_start), "2026-03-01")

    def test_lines_carry_the_partner(self):
        page = self.Service.get_lines(self._data(), self.receivable.id, 0, 0.0, 1)
        self.assertEqual(page["lines"][0]["partner_id"], self.partner_a.id)

    # ------------------------------------------------------------------
    # Wizard options carried into the interactive view
    # ------------------------------------------------------------------
    def test_hierarchy_inserts_group_subtotals(self):
        Group = self.env["account.group"]
        top = Group.create({"name": "Class 1", "code_prefix_start": "1", "company_id": self.company.id})
        Group.create({"name": "Receivables", "code_prefix_start": "12", "company_id": self.company.id})
        self.receivable.invalidate_recordset(["group_id"])
        rows = self.Service.get_accounts(self._data(show_hierarchy=True))["accounts"]
        groups = [r for r in rows if r["type"] == "group"]
        self.assertEqual([g["name"] for g in groups if g["code"] in ("1", "12")], ["Class 1", "Receivables"])
        receivable_index = next(i for i, r in enumerate(rows) if r.get("id") == self.receivable.id)
        self.assertEqual(rows[receivable_index - 1]["name"], "Receivables")     # right before its account
        self.assertEqual(rows[receivable_index]["level"], 3)
        class1 = next(g for g in groups if g["id"] == "g%s" % top.id)
        self.assertAlmostEqual(class1["closing"], self._row({"accounts": rows}, self.receivable)["closing"])
        limited = self.Service.get_accounts(self._data(
            show_hierarchy=True, limit_hierarchy_level=True, show_hierarchy_level=1))["accounts"]
        self.assertNotIn("Receivables", [r["name"] for r in limited if r["type"] == "group"])

    def test_grouped_by_partner(self):
        data = self._data(grouped_by="partners")
        row = self._row(self.Service.get_accounts(data), self.receivable)
        self.assertTrue(row["by_partner"])
        self.assertFalse(self._row(self.Service.get_accounts(data), self.income)["by_partner"])
        partners = self.Service.get_partners(data, self.receivable.id)
        self.assertEqual([p["id"] for p in partners], [self.partner_a.id])
        self.assertAlmostEqual(partners[0]["closing"], row["closing"])
        page = self.Service.get_lines(data, self.receivable.id, 0, partners[0]["opening"], 80, self.partner_a.id)
        self.assertEqual(page["total"], 5)
        self.assertEqual(self.Service.get_lines(data, self.receivable.id, 0, 0.0, 80, 0)["total"], 0)

    def test_centralized_account_shows_months(self):
        self.income.centralized = True
        data = self._data(date_from="2026-01-01", date_to="2026-12-31", centralize=True)
        page = self.Service.get_lines(data, self.income.id, 0, 0.0)
        self.assertEqual([line["label"] for line in page["lines"]], ["2026-02", "2026-03"])
        self.assertAlmostEqual(page["lines"][-1]["balance"], -100.0)
        self.assertFalse(page["lines"][0]["move_id"])
        # Without the wizard option the items are listed one by one.
        self.assertEqual(self.Service.get_lines(self._data(date_from="2026-01-01", date_to="2026-12-31"),
                                                self.income.id, 0, 0.0)["total"], 6)

    def test_foreign_currency_amount_on_lines(self):
        eur = self.setup_other_currency("EUR")
        self.init_invoice("out_invoice", invoice_date="2026-03-20", amounts=[100.0], currency=eur, post=True)
        lines = self.Service.get_lines(self._data(foreign_currency=True), self.receivable.id, 0, 0.0)["lines"]
        foreign = [line for line in lines if line["currency"]]
        self.assertEqual([line["currency"] for line in foreign], ["EUR"])
        self.assertAlmostEqual(foreign[0]["amount_currency"], 100.0)
        plain = self.Service.get_lines(self._data(), self.receivable.id, 0, 0.0)["lines"]
        self.assertFalse([line for line in plain if line["currency"]])

    def test_extra_domain_filters_everything(self):
        domain = "[('partner_id', '=', %d)]" % self.partner_b.id
        result = self.Service.get_accounts(self._data(extra_domain=domain, hide_account_at_0=True))
        self.assertFalse(result["accounts"])         # partner B has no March items
        result = self.Service.get_accounts(self._data(extra_domain="[('partner_id', '=', %d)]" % self.partner_a.id))
        self.assertAlmostEqual(self._row(result, self.receivable)["debit"], 50.0)
        page = self.Service.get_lines(self._data(extra_domain="[('name', 'ilike', 'nothing like this')]"),
                                      self.receivable.id, 0, 0.0)
        self.assertEqual(page["total"], 0)

    def test_extra_domain_is_parsed_literally(self):
        from odoo.exceptions import UserError
        with self.assertRaises(UserError):
            self.Service.get_accounts(self._data(extra_domain="__import__('os').getcwd()"))
