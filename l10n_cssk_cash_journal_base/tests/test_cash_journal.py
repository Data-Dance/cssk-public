# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestCashJournalCommon(AccountTestInvoicingCommon):
    """Fixtures shared by the denník tests.

    The company is put in the ``de`` regime and given a small category
    catalogue, because the engine reads categories off accounts and a test that
    maps nothing would only ever exercise the review path.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.cssk_bookkeeping_regime = "de"
        cls.country = cls.company.country_id or cls.env.ref("base.sk")

        def category(code, name, kind, taxable=True, non_cash=False):
            return cls.env["cssk.cash.category"].create({
                "code": code,
                "name": name,
                "country_id": cls.country.id,
                "kind": kind,
                "taxable": taxable,
                "non_cash": non_cash,
            })

        cls.cat_sales = category("P1", "Predaj výrobkov a služieb", "income")
        cls.cat_other_income = category(
            "PN1", "Ostatný príjem neovplyvňujúci ZD", "income", taxable=False)
        cls.cat_goods = category("V1", "Zásoby", "expense")
        cls.cat_services = category("V2", "Služby", "expense")
        cls.cat_private = category(
            "VN1", "Osobná spotreba", "expense", taxable=False)
        cls.cat_transit = category("C1", "Priebežné položky", "transit",
                                   taxable=False)
        cls.cat_loan_in = category(
            "PN2", "Prijatý úver", "income", taxable=False)
        cls.cat_loan_out = category(
            "VN5", "Splátka istiny", "expense", taxable=False)
        cls.cat_depreciation = category(
            "Z1", "Odpisy", "expense", non_cash=True)

        cls.income_account = cls.company_data["default_account_revenue"]
        cls.expense_account = cls.company_data["default_account_expense"]
        cls.income_account.cssk_cash_category_id = cls.cat_sales
        cls.expense_account.cssk_cash_category_id = cls.cat_goods
        # A second expense account under a different category, so that a
        # document can split across two columns of the denník.
        cls.services_account = cls.expense_account.copy({
            "code": "%s9" % cls.expense_account.code,
        })
        cls.services_account.cssk_cash_category_id = cls.cat_services

        cls.bank_journal = cls.company_data["default_journal_bank"]
        cls.cash_journal = cls.company_data["default_journal_cash"]

        # Transit accounts must be reachable for the chain tests; Odoo creates
        # the suspense account with the chart, so only assert it exists.
        cls.suspense_account = cls.bank_journal.suspense_account_id \
            or cls.company.account_journal_suspense_account_id

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _generate(self, date_from="2026-01-01", date_to="2026-12-31"):
        return self.env["cssk.cash.journal.line"]._cssk_regenerate(
            self.company,
            fields.Date.to_date(date_from),
            fields.Date.to_date(date_to),
        )

    def _rows(self):
        return self.env["cssk.cash.journal.line"].search([
            ("company_id", "=", self.company.id),
        ])

    def _pay(self, invoice, amount=None, journal=None, payment_date="2026-03-15"):
        """Register a payment on ``invoice``, optionally partial."""
        wizard = self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=invoice.ids,
        ).create({
            "payment_date": payment_date,
            "journal_id": (journal or self.bank_journal).id,
        })
        if amount is not None:
            wizard.amount = amount
        return wizard._create_payments()

    def _invoice(self, move_type="out_invoice", lines=None, taxes=None,
                 invoice_date="2026-02-01"):
        tax_ids = taxes if taxes is not None else False
        invoice_lines = []
        for price, account in lines:
            invoice_lines.append({
                "name": "line %s" % price,
                "quantity": 1.0,
                "price_unit": price,
                "account_id": account.id,
                "tax_ids": [(6, 0, tax_ids.ids)] if tax_ids else [(5, 0, 0)],
            })
        invoice = self.env["account.move"].create({
            "move_type": move_type,
            "partner_id": self.partner_a.id,
            "invoice_date": fields.Date.to_date(invoice_date),
            "date": fields.Date.to_date(invoice_date),
            "invoice_line_ids": [(0, 0, vals) for vals in invoice_lines],
        })
        invoice.action_post()
        return invoice


class TestCashJournalGeneration(TestCashJournalCommon):

    def test_models_load(self):
        for model in ("cssk.cash.category", "cssk.cash.journal.line",
                      "cssk.cash.journal.generate"):
            self.assertIn(model, self.env)

    def test_invoice_is_not_a_row_until_it_is_paid(self):
        """The document creates a receivable; only money writes the book."""
        self._invoice(lines=[(1000.0, self.income_account)])
        self._generate()
        self.assertFalse(self._rows())

    def test_full_payment_of_an_untaxed_invoice(self):
        invoice = self._invoice(lines=[(1000.0, self.income_account)])
        self._pay(invoice)
        self._generate()
        rows = self._rows()
        self.assertEqual(len(rows), 1)
        row = rows
        self.assertEqual(row.kind, "income")
        self.assertEqual(row.category_id, self.cat_sales)
        self.assertEqual(row.amount, 1000.0)
        self.assertEqual(row.amount_tax, 0.0)
        self.assertEqual(row.date, fields.Date.to_date("2026-03-15"))
        self.assertEqual(row.source_move_id, invoice)
        self.assertFalse(row.needs_review)
        self.assertTrue(row.taxable)

    def test_vat_is_reported_apart_from_the_base(self):
        """A VAT payer's base is net; the VAT rides in its own column.

        SK § 21 ods. 1 písm. i) keeps VAT out of the income-tax base, and the
        denník has a DPH column for exactly this.
        """
        invoice = self._invoice(
            lines=[(1000.0, self.income_account)], taxes=self.tax_sale_a)
        self._pay(invoice)
        self._generate()
        row = self._rows()
        self.assertEqual(len(row), 1)
        tax_rate = self.tax_sale_a.amount / 100.0
        self.assertAlmostEqual(row.amount, 1000.0, places=2)
        self.assertAlmostEqual(row.amount_tax, 1000.0 * tax_rate, places=2)

    def test_partial_payment_is_split_pro_rata(self):
        """Two categories on one bill, half paid: each gets half.

        This is the decision the research flagged — Odoo pro-rates, POHODA
        settles VAT first — so it is asserted rather than assumed.
        """
        bill = self._invoice(
            move_type="in_invoice",
            lines=[(600.0, self.expense_account),
                   (400.0, self.services_account)],
        )
        self._pay(bill, amount=500.0)
        self._generate()
        rows = self._rows().sorted("amount", reverse=True)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows.mapped("kind"), ["expense", "expense"])
        self.assertEqual(
            rows.mapped("category_id"), self.cat_goods | self.cat_services)
        self.assertAlmostEqual(rows[0].amount, 300.0, places=2)
        self.assertAlmostEqual(rows[1].amount, 200.0, places=2)
        self.assertAlmostEqual(sum(rows.mapped("amount")), 500.0, places=2)

    def test_rows_of_one_payment_add_up_to_the_money(self):
        """Rounding must not lose or invent a cent."""
        bill = self._invoice(
            move_type="in_invoice",
            lines=[(33.33, self.expense_account),
                   (33.33, self.services_account),
                   (33.34, self.expense_account)],
        )
        self._pay(bill, amount=50.0)
        self._generate()
        rows = self._rows()
        self.assertAlmostEqual(
            sum(rows.mapped("amount")) + sum(rows.mapped("amount_tax")),
            50.0, places=2)

    def test_line_category_overrides_the_account(self):
        bill = self._invoice(
            move_type="in_invoice", lines=[(100.0, self.expense_account)])
        # A private share of a business bill: the accountant retags the line.
        bill.line_ids.filtered(lambda line: line.display_type == "product") \
            .cssk_cash_category_id = self.cat_private
        self._pay(bill)
        self._generate()
        row = self._rows()
        self.assertEqual(row.category_id, self.cat_private)
        self.assertFalse(row.taxable)

    def test_payment_is_not_counted_twice_through_the_outstanding_account(self):
        """A payment lands on an outstanding account, then on the bank.

        Both are ``asset_cash``, so the naive reading books the money twice.
        Only the journal's own account is money; the rest is a chain to follow.
        """
        invoice = self._invoice(lines=[(1000.0, self.income_account)])
        payment = self._pay(invoice)
        self.assertTrue(payment.outstanding_account_id)
        self._generate()
        rows = self._rows()
        self.assertAlmostEqual(sum(rows.mapped("amount_signed")), 1000.0,
                               places=2)

    def test_direct_bank_expense_takes_the_account_category(self):
        """A bank charge has no invoice; the account carries the category."""
        fee_account = self.services_account
        move = self.env["account.move"].create({
            "journal_id": self.bank_journal.id,
            "date": fields.Date.to_date("2026-04-30"),
            "line_ids": [
                (0, 0, {
                    "account_id": fee_account.id,
                    "name": "Bank charges",
                    "debit": 12.0,
                    "credit": 0.0,
                }),
                (0, 0, {
                    "account_id": self.bank_journal.default_account_id.id,
                    "name": "Bank charges",
                    "debit": 0.0,
                    "credit": 12.0,
                }),
            ],
        })
        move.action_post()
        self._generate()
        row = self._rows()
        self.assertEqual(len(row), 1)
        self.assertEqual(row.kind, "expense")
        self.assertEqual(row.category_id, self.cat_services)
        self.assertEqual(row.amount, 12.0)
        self.assertEqual(row.payment_kind, "bank")

    def _taxed_entry(self, lines, journal=None):
        """A journal entry paying ``lines`` [(account, amount, taxes)] out of
        the bank — the shape the Expenses app and a hand-made entry share."""
        journal = journal or self.bank_journal
        move = self.env["account.move"].create({
            "journal_id": journal.id,
            "date": fields.Date.to_date("2026-05-10"),
            "line_ids": [
                (0, 0, {"account_id": account.id, "name": "Výdavok",
                        "debit": amount, "credit": 0.0,
                        "tax_ids": [(6, 0, taxes.ids)]})
                for account, amount, taxes in lines
            ],
        })
        # Odoo adds the VAT lines; the money leg balances whatever they are.
        total = sum(move.line_ids.mapped("debit")) - sum(move.line_ids.mapped("credit"))
        move.write({"line_ids": [(0, 0, {
            "account_id": journal.default_account_id.id, "name": "Výdavok",
            "debit": 0.0, "credit": total})]})
        move.action_post()
        return move

    def test_an_expense_entry_with_vat_is_one_row(self):
        """"Rozdelilo mi to výdavok do dvoch riadkov — zvlášť základ, zvlášť
        DPH." An entry outside an invoice is one row with its VAT, as a paid
        bill is."""
        tax = self.tax_purchase_a
        move = self._taxed_entry([(self.expense_account, 100.0, tax)])
        tax_lines = move.line_ids.filtered(lambda l: l.display_type == "tax")
        self.assertTrue(tax_lines, "fixture: Odoo computed a VAT line")
        self._generate()
        rows = self._rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows.category_id, self.cat_goods)
        self.assertAlmostEqual(rows.amount, 100.0, 2)
        self.assertAlmostEqual(rows.amount_tax, sum(tax_lines.mapped("debit")), 2)
        bank_out = -sum(move.line_ids.filtered(
            lambda l: l.account_id == self.bank_journal.default_account_id).mapped("balance"))
        self.assertAlmostEqual(rows.amount + rows.amount_tax, bank_out, 2,
                               msg="the book still adds up to the money")

    def test_vat_follows_each_base_line_of_a_split_entry(self):
        tax = self.tax_purchase_a
        move = self._taxed_entry([(self.expense_account, 100.0, tax),
                                  (self.services_account, 300.0, tax)])
        self._generate()
        rows = self._rows()
        self.assertEqual(len(rows), 2)
        by_cat = {r.category_id: r for r in rows}
        rate = tax.amount / 100.0
        self.assertAlmostEqual(by_cat[self.cat_goods].amount_tax, 100.0 * rate, 2)
        self.assertAlmostEqual(by_cat[self.cat_services].amount_tax, 300.0 * rate, 2)
        bank_out = -sum(move.line_ids.filtered(
            lambda l: l.account_id == self.bank_journal.default_account_id).mapped("balance"))
        self.assertAlmostEqual(
            sum(rows.mapped("amount")) + sum(rows.mapped("amount_tax")), bank_out, 2)

    def test_transfer_between_bank_and_cash_is_a_transit_row(self):
        """Money between one's own pockets is a priebežná položka, not income."""
        move = self.env["account.move"].create({
            "journal_id": self.bank_journal.id,
            "date": fields.Date.to_date("2026-05-02"),
            "line_ids": [
                (0, 0, {
                    "account_id": self.cash_journal.default_account_id.id,
                    "name": "To the till",
                    "debit": 200.0,
                    "credit": 0.0,
                }),
                (0, 0, {
                    "account_id": self.bank_journal.default_account_id.id,
                    "name": "To the till",
                    "debit": 0.0,
                    "credit": 200.0,
                }),
            ],
        })
        move.action_post()
        self._generate()
        rows = self._rows()
        self.assertEqual(len(rows), 2)
        self.assertEqual(set(rows.mapped("kind")), {"transit"})
        self.assertFalse(any(rows.mapped("taxable")))
        self.assertEqual(set(rows.mapped("amount")), {200.0})

    def test_unmapped_account_is_flagged_not_guessed(self):
        # ``copy()`` carries the mapping over, which is right for an account
        # that means the same thing — so an unmapped account has to be made
        # unmapped explicitly.
        unmapped = self.expense_account.copy({
            "code": "%s8" % self.expense_account.code,
            "cssk_cash_category_id": False,
        })
        bill = self._invoice(move_type="in_invoice", lines=[(70.0, unmapped)])
        self._pay(bill)
        self._generate()
        row = self._rows()
        self.assertTrue(row.needs_review)
        self.assertFalse(row.category_id)
        self.assertFalse(row.taxable)
        self.assertIn(unmapped.display_name, row.review_reason)

    def test_non_cash_rows_come_from_flagged_categories(self):
        """Depreciation is an expense that never touched the money."""
        depreciation_account = self.expense_account.copy({
            "code": "%s7" % self.expense_account.code,
        })
        depreciation_account.cssk_cash_category_id = self.cat_depreciation
        accumulated = self.expense_account.copy({
            "code": "%s6" % self.expense_account.code,
        })
        move = self.env["account.move"].create({
            "journal_id": self.company_data["default_journal_misc"].id,
            "date": fields.Date.to_date("2026-12-31"),
            "line_ids": [
                (0, 0, {
                    "account_id": depreciation_account.id,
                    "name": "Odpis 2026",
                    "debit": 900.0,
                    "credit": 0.0,
                }),
                (0, 0, {
                    "account_id": accumulated.id,
                    "name": "Odpis 2026",
                    "debit": 0.0,
                    "credit": 900.0,
                }),
            ],
        })
        move.action_post()
        self._generate()
        row = self._rows().filtered("non_cash")
        self.assertEqual(len(row), 1)
        self.assertEqual(row.category_id, self.cat_depreciation)
        self.assertEqual(row.kind, "expense")
        self.assertEqual(row.amount, 900.0)
        self.assertEqual(row.payment_kind, "none")

    def test_regeneration_is_idempotent_and_keeps_manual_rows(self):
        invoice = self._invoice(lines=[(1000.0, self.income_account)])
        self._pay(invoice)
        self._generate()
        first = self._rows()
        self.assertEqual(len(first), 1)

        manual = self.env["cssk.cash.journal.line"].create({
            "company_id": self.company.id,
            "date": fields.Date.to_date("2026-06-01"),
            "kind": "income",
            "category_id": self.cat_other_income.id,
            "amount": 42.0,
            "manual": True,
            "label": "Typed by the accountant",
        })
        self._generate()
        rows = self._rows()
        self.assertEqual(len(rows), 2)
        self.assertIn(manual, rows)
        self.assertEqual(
            len(rows.filtered(lambda row: not row.manual)), 1,
            "regeneration must replace its own rows, not add to them")

    def test_numbering_follows_the_date_order(self):
        """'V časovom slede' (§ 6 ods. 11 ZDP) — the book is read in order."""
        first = self._invoice(lines=[(100.0, self.income_account)])
        second = self._invoice(lines=[(200.0, self.income_account)])
        self._pay(first, payment_date="2026-03-20")
        self._pay(second, payment_date="2026-03-05")
        self._generate()
        rows = self._rows().sorted("date")
        self.assertEqual(rows.mapped("number"), ["2026/00001", "2026/00002"])
        self.assertEqual(rows[0].amount, 200.0)

    def test_the_lock_date_protects_a_filed_period(self):
        invoice = self._invoice(lines=[(1000.0, self.income_account)])
        self._pay(invoice, payment_date="2026-03-15")
        self._generate()
        row = self._rows()
        self.assertEqual(len(row), 1)

        self.company.fiscalyear_lock_date = fields.Date.to_date("2026-06-30")
        with self.assertRaises(UserError):
            self._generate("2026-01-01", "2026-06-30")
        self.assertEqual(self._rows(), row, "a locked row must survive")

        # A window that reaches past the lock date regenerates only the open part.
        self._generate("2026-01-01", "2026-12-31")
        self.assertEqual(self._rows(), row)

    def test_the_start_date_leaves_earlier_payments_alone(self):
        """A mid-year migration: the denník starts when the customer did."""
        invoice = self._invoice(lines=[(100.0, self.income_account)])
        self._pay(invoice, payment_date="2026-02-10")
        later = self._invoice(lines=[(300.0, self.income_account)])
        self._pay(later, payment_date="2026-08-10")
        self.company.cssk_cash_journal_start = fields.Date.to_date("2026-07-01")
        self._generate()
        rows = self._rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows.amount, 300.0)


class TestCashJournalAllocation(TestCashJournalCommon):
    """The cases a second-opinion review (gpt-5.3-codex) raised on the draft."""

    def test_a_receipt_net_of_a_charge_keeps_both_full_amounts(self):
        """120 in, 20 deducted: the book says 120 income and 20 expense.

        The draft prorated ``abs(balance)`` over the money and produced
        85.71 / 14.29 — two wrong categories whose net happened to be right.
        A line's own sign and balance decide, so each side is whole.
        """
        move = self.env["account.move"].create({
            "journal_id": self.bank_journal.id,
            "date": fields.Date.to_date("2026-04-02"),
            "line_ids": [
                (0, 0, {
                    "account_id": self.bank_journal.default_account_id.id,
                    "name": "Net receipt", "debit": 100.0, "credit": 0.0,
                }),
                (0, 0, {
                    "account_id": self.income_account.id,
                    "name": "Sale", "debit": 0.0, "credit": 120.0,
                }),
                (0, 0, {
                    "account_id": self.services_account.id,
                    "name": "Charge deducted", "debit": 20.0, "credit": 0.0,
                }),
            ],
        })
        move.action_post()
        self._generate()
        rows = self._rows()
        income = rows.filtered(lambda row: row.kind == "income")
        expense = rows.filtered(lambda row: row.kind == "expense")
        self.assertAlmostEqual(income.amount, 120.0, places=2)
        self.assertAlmostEqual(expense.amount, 20.0, places=2)
        self.assertAlmostEqual(sum(rows.mapped("amount_signed")), 100.0,
                               places=2)

    def test_a_negative_document_line_lands_in_the_other_column(self):
        """A deduction on an invoice must not inflate both categories."""
        invoice = self._invoice(lines=[
            (1000.0, self.income_account),
            (-100.0, self.services_account),
        ])
        self._pay(invoice)
        self._generate()
        rows = self._rows()
        self.assertEqual(len(rows), 2)
        income = rows.filtered(lambda row: row.kind == "income")
        expense = rows.filtered(lambda row: row.kind == "expense")
        self.assertAlmostEqual(income.amount, 1000.0, places=2)
        self.assertAlmostEqual(expense.amount, 100.0, places=2)
        self.assertAlmostEqual(sum(rows.mapped("amount_signed")), 900.0,
                               places=2)

    def test_a_zero_balance_counterpart_absorbs_nothing(self):
        """The remainder must never be filed under a line worth nothing."""
        move = self.env["account.move"].create({
            "journal_id": self.bank_journal.id,
            "date": fields.Date.to_date("2026-04-03"),
            "line_ids": [
                (0, 0, {
                    "account_id": self.bank_journal.default_account_id.id,
                    "name": "Receipt", "debit": 50.0, "credit": 0.0,
                }),
                (0, 0, {
                    "account_id": self.income_account.id,
                    "name": "Sale", "debit": 0.0, "credit": 50.0,
                }),
                (0, 0, {
                    "account_id": self.services_account.id,
                    "name": "Nothing", "debit": 0.0, "credit": 0.0,
                }),
            ],
        })
        move.action_post()
        self._generate()
        rows = self._rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows.category_id, self.cat_sales)
        self.assertAlmostEqual(rows.amount, 50.0, places=2)

    def test_money_moved_in_a_misc_journal_is_still_money(self):
        """An accountant's correction touching the bank belongs in the book."""
        move = self.env["account.move"].create({
            "journal_id": self.company_data["default_journal_misc"].id,
            "date": fields.Date.to_date("2026-04-04"),
            "line_ids": [
                (0, 0, {
                    "account_id": self.bank_journal.default_account_id.id,
                    "name": "Correction", "debit": 0.0, "credit": 30.0,
                }),
                (0, 0, {
                    "account_id": self.services_account.id,
                    "name": "Correction", "debit": 30.0, "credit": 0.0,
                }),
            ],
        })
        move.action_post()
        self._generate()
        row = self._rows()
        self.assertEqual(len(row), 1)
        self.assertEqual(row.kind, "expense")
        self.assertEqual(row.category_id, self.cat_services)
        self.assertEqual(row.payment_kind, "bank",
                         "the account decides the money column, not the journal")

    def test_an_unmatched_receipt_is_flagged_as_a_possible_advance(self):
        """Money on a receivable with no document is not a transit row."""
        payment = self.env["account.payment"].create({
            "payment_type": "inbound",
            "partner_type": "customer",
            "partner_id": self.partner_a.id,
            "amount": 500.0,
            "date": fields.Date.to_date("2026-04-05"),
            "journal_id": self.bank_journal.id,
        })
        payment.action_post()
        self._generate()
        rows = self._rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows.kind, "income")
        self.assertTrue(rows.needs_review)
        self.assertIn("advance", rows.review_reason)
        self.assertAlmostEqual(rows.amount, 500.0, places=2)

    def test_numbering_is_stable_across_regeneration(self):
        """Two runs of the same book must number the same rows the same way."""
        for day, amount in (("2026-03-04", 100.0), ("2026-03-04", 200.0),
                            ("2026-03-05", 300.0)):
            invoice = self._invoice(lines=[(amount, self.income_account)])
            self._pay(invoice, payment_date=day)
        self._generate()
        first = {row.move_line_id.id: row.number for row in self._rows()}
        self._generate()
        second = {row.move_line_id.id: row.number for row in self._rows()}
        self.assertEqual(first, second)


class TestCashJournalDirectionVersusCategory(TestCashJournalCommon):
    """Where the money went is not where the amount belongs.

    Both cases below were live defects, found when a cooperating accountant
    asked which side of a document (MD/D) the denník should read. The answer is
    neither: the line's sign gives the direction, the category gives the column.
    """

    def test_a_refunded_sale_reduces_income_instead_of_adding_an_expense(self):
        """1000 sold and 200 refunded is príjmy 800, not 1000 against 200.

        The tax base was right either way; the gross columns of DPFO tabuľka 1
        were not, and the sales column of the book read 1200.
        """
        sale = self._invoice(lines=[(1000.0, self.income_account)])
        self._pay(sale, payment_date="2026-03-01")
        refund = self._invoice(
            move_type="out_refund", lines=[(200.0, self.income_account)])
        self._pay(refund, payment_date="2026-03-05")
        self._generate()

        rows = self._rows()
        self.assertEqual(len(rows), 2)
        storno = rows.filtered("counter_entry")
        self.assertEqual(len(storno), 1)
        self.assertEqual(storno.kind, "income",
                         "a refunded sale stays in its sales category")
        self.assertEqual(storno.money_direction, "out",
                         "and the money really did leave the bank")
        self.assertAlmostEqual(storno.amount, 200.0, places=2)
        self.assertAlmostEqual(storno.amount_classified, -200.0, places=2)
        self.assertAlmostEqual(storno.amount_signed, -200.0, places=2)

        figures = self.env["cssk.cash.figures"]._cssk_flows(
            self.company,
            fields.Date.to_date("2026-01-01"),
            fields.Date.to_date("2026-12-31"))
        self.assertAlmostEqual(figures["income"], 800.0, places=2)
        self.assertAlmostEqual(figures["expense"], 0.0, places=2)
        self.assertAlmostEqual(figures["money_income"], 1000.0, places=2)
        self.assertAlmostEqual(figures["money_expense"], 200.0, places=2,
                               msg="the money columns still follow the money")

    def test_a_refund_from_a_supplier_reduces_expenses(self):
        """The mirror case: money in, against an expense category."""
        bill = self._invoice(
            move_type="in_invoice", lines=[(500.0, self.expense_account)])
        self._pay(bill, payment_date="2026-04-01")
        credit = self._invoice(
            move_type="in_refund", lines=[(120.0, self.expense_account)])
        self._pay(credit, payment_date="2026-04-10")
        self._generate()

        storno = self._rows().filtered("counter_entry")
        self.assertEqual(storno.kind, "expense")
        self.assertEqual(storno.money_direction, "in")
        figures = self.env["cssk.cash.figures"]._cssk_flows(
            self.company,
            fields.Date.to_date("2026-01-01"),
            fields.Date.to_date("2026-12-31"))
        self.assertAlmostEqual(figures["expense"], 380.0, places=2)
        self.assertAlmostEqual(figures["income"], 0.0, places=2)

    def test_an_account_mapped_to_a_transit_category_is_a_transit_row(self):
        """'261 Peniaze na ceste' mapped by hand, not configured in Odoo.

        It used to come out as an expense and land in "výdavky neovplyvňujúce
        základ dane" — harmless for the tax base, wrong in the book.
        """
        on_the_way = self.expense_account.copy({
            "code": "%s5" % self.expense_account.code,
            "cssk_cash_category_id": self.cat_transit.id,
            "reconcile": True,
        })
        move = self.env["account.move"].create({
            "journal_id": self.bank_journal.id,
            "date": fields.Date.to_date("2026-05-20"),
            "line_ids": [
                (0, 0, {
                    "account_id": on_the_way.id,
                    "name": "na ceste", "debit": 300.0, "credit": 0.0,
                }),
                (0, 0, {
                    "account_id": self.bank_journal.default_account_id.id,
                    "name": "na ceste", "debit": 0.0, "credit": 300.0,
                }),
            ],
        })
        move.action_post()
        self._generate()
        row = self._rows()
        self.assertEqual(len(row), 1)
        self.assertEqual(row.kind, "transit")
        self.assertEqual(row.money_direction, "out")
        self.assertFalse(row.taxable)

        figures = self.env["cssk.cash.figures"]._cssk_flows(
            self.company,
            fields.Date.to_date("2026-01-01"),
            fields.Date.to_date("2026-12-31"))
        self.assertAlmostEqual(figures["transit_out"], 300.0, places=2)
        self.assertAlmostEqual(figures["expense"], 0.0, places=2)


class TestCashJournalTwoWayAccounts(TestCashJournalCommon):
    """An account that moves both ways needs a category for each direction.

    Raised by a cooperating accountant asking whether a pôžička — neither income
    nor expense, but a receivable or a liability — shows up in the book at all.
    It did, in one column: a loan of 10 000 received and 2 500 repaid netted to
    7 500 of "príjmy neovplyvňujúce ZD" and left "výdavky neovplyvňujúce ZD"
    empty. Her own chart has a worse case in ``343``, where an odvod DPH and a
    nadmerný odpočet share one account.
    """

    def _loan_account(self, both_ways=True):
        account = self.env["account.account"].create({
            "name": "Bankový úver",
            "code": "461100",
            "account_type": "liability_non_current",
            "reconcile": True,
            "cssk_cash_category_id": self.cat_loan_out.id if both_ways
            else self.cat_loan_in.id,
        })
        if both_ways:
            account.cssk_cash_category_in_id = self.cat_loan_in
        return account

    def _bank_move(self, account, amount, incoming, date):
        bank = self.bank_journal.default_account_id
        move = self.env["account.move"].create({
            "journal_id": self.bank_journal.id,
            "date": fields.Date.to_date(date),
            "line_ids": [
                (0, 0, {
                    "account_id": bank.id, "name": "úver",
                    "debit": amount if incoming else 0.0,
                    "credit": 0.0 if incoming else amount,
                }),
                (0, 0, {
                    "account_id": account.id, "name": "úver",
                    "debit": 0.0 if incoming else amount,
                    "credit": amount if incoming else 0.0,
                }),
            ],
        })
        move.action_post()
        return move

    def test_a_loan_and_its_instalment_land_in_opposite_columns(self):
        account = self._loan_account()
        self._bank_move(account, 10000.0, True, "2026-05-02")
        self._bank_move(account, 500.0, False, "2026-06-02")
        self._generate()

        rows = self._rows().sorted("date")
        self.assertEqual(rows.mapped("kind"), ["income", "expense"])
        self.assertEqual(rows.mapped("money_direction"), ["in", "out"])
        self.assertEqual(rows.mapped("category_id"),
                         self.cat_loan_in | self.cat_loan_out)
        self.assertFalse(any(rows.mapped("counter_entry")),
                         "neither is a storno — the account simply moves both ways")
        self.assertFalse(any(rows.mapped("taxable")))
        self.assertFalse(any(rows.mapped("needs_review")))

        figures = self.env["cssk.cash.figures"]._cssk_flows(
            self.company,
            fields.Date.to_date("2026-01-01"),
            fields.Date.to_date("2026-12-31"))
        self.assertAlmostEqual(figures["income_all"], 10000.0, places=2)
        self.assertAlmostEqual(figures["expense_all"], 500.0, places=2)
        self.assertAlmostEqual(figures["income"], 0.0, places=2)
        self.assertAlmostEqual(figures["expense"], 0.0, places=2)

    def test_a_one_way_mapping_on_a_two_way_account_is_flagged(self):
        """Better to ask than to net two columns into one silently."""
        account = self._loan_account(both_ways=False)
        self._bank_move(account, 10000.0, True, "2026-05-02")
        self._bank_move(account, 500.0, False, "2026-06-02")
        self._generate()

        rows = self._rows().sorted("date")
        flagged = rows.filtered("needs_review")
        self.assertEqual(len(flagged), 1)
        self.assertEqual(flagged.money_direction, "out")
        self.assertIn("direction", flagged.review_reason)

    def test_a_dobropis_is_still_a_storno(self):
        """The reversal case must keep netting its own column.

        This is what separates the two: a payment matched to a credit note
        reverses an earlier entry, an instalment on a loan does not.
        """
        sale = self._invoice(lines=[(1000.0, self.income_account)])
        self._pay(sale, payment_date="2026-03-01")
        refund = self._invoice(
            move_type="out_refund", lines=[(200.0, self.income_account)])
        self._pay(refund, payment_date="2026-03-05")
        self._generate()
        storno = self._rows().filtered("counter_entry")
        self.assertEqual(storno.kind, "income")
        self.assertFalse(storno.needs_review,
                         "a dobropis is a storno, not a configuration problem")


class TestCashJournalPartialAllocation(TestCashJournalCommon):
    """The three models the internal directive may choose between."""

    def _paid_in_part(self, model, payment=500.0):
        """Rows of ONE invoice under ``model``, as (base, VAT).

        Filtered to the invoice, because regeneration rebuilds the whole period
        and a test that measures every row would also count the invoices its
        earlier assertions created.
        """
        self.company.cssk_cash_partial_allocation = model
        invoice = self._invoice(
            lines=[(1000.0, self.income_account)], taxes=self.tax_sale_a)
        self._pay(invoice, amount=payment)
        self._generate()
        rows = self._rows().filtered(lambda row: row.source_move_id == invoice)
        return sum(rows.mapped("amount")), sum(rows.mapped("amount_tax"))

    def test_pro_rata_is_the_default(self):
        self.assertEqual(self.company.cssk_cash_partial_allocation, "prorata")
        rate = self.tax_sale_a.amount / 100.0
        base, tax = self._paid_in_part("prorata")
        self.assertAlmostEqual(base + tax, 500.0, places=2)
        self.assertAlmostEqual(base, 500.0 / (1 + rate), places=2)

    def test_vat_first_settles_the_whole_vat(self):
        """POHODA's model: the first payment pays the VAT off."""
        rate = self.tax_sale_a.amount / 100.0
        base, tax = self._paid_in_part("vat_first")
        self.assertAlmostEqual(tax, 1000.0 * rate, places=2)
        self.assertAlmostEqual(base, 500.0 - 1000.0 * rate, places=2)
        self.assertAlmostEqual(base + tax, 500.0, places=2)

    def test_base_first_settles_the_base(self):
        base, tax = self._paid_in_part("base_first")
        self.assertAlmostEqual(base, 500.0, places=2)
        self.assertAlmostEqual(tax, 0.0, places=2)

    def test_a_full_payment_is_the_same_under_every_model(self):
        rate = self.tax_sale_a.amount / 100.0
        gross = 1000.0 * (1 + rate)
        results = [self._paid_in_part(model, payment=gross)
                   for model in ("prorata", "vat_first", "base_first")]
        for base, tax in results:
            self.assertAlmostEqual(base, 1000.0, places=2)
            self.assertAlmostEqual(tax, 1000.0 * rate, places=2)


class TestCashJournalAdvances(TestCashJournalCommon):
    """A received advance is taxable income when the money arrives.

    Confirmed by the cooperating accountant: "prijatá záloha sa považuje za
    zdaniteľný príjem", classified by what the advance is for — which is why a
    zálohová faktúra should be posted to the account the final supply will land
    on. That is the opposite of the VAT treatment, where an advance invoice is
    not a taxable event of its own.
    """

    def test_an_advance_invoice_carries_the_final_category(self):
        advance = self._invoice(lines=[(300.0, self.income_account)])
        self._pay(advance, payment_date="2026-02-20")
        self._generate()
        row = self._rows()
        self.assertEqual(row.category_id, self.cat_sales)
        self.assertTrue(row.taxable, "taxable income at receipt")
        self.assertFalse(row.needs_review)

    def test_a_payment_with_no_document_still_asks_which_category(self):
        """Nothing says what the advance is for, so it cannot be guessed."""
        payment = self.env["account.payment"].create({
            "payment_type": "inbound",
            "partner_type": "customer",
            "partner_id": self.partner_a.id,
            "amount": 400.0,
            "date": fields.Date.to_date("2026-02-25"),
            "journal_id": self.bank_journal.id,
        })
        payment.action_post()
        self._generate()
        row = self._rows()
        self.assertTrue(row.needs_review)
        self.assertIn("advance", row.review_reason)


class TestCashJournalPrinting(TestCashJournalCommon):
    """The spreadsheet the accountant asked for, beside the PDF."""

    def _wizard(self):
        return self.env["cssk.cash.journal.print"].create({
            "company_id": self.company.id,
            "date_from": fields.Date.to_date("2026-01-01"),
            "date_to": fields.Date.to_date("2026-12-31"),
            "output": "xlsx",
        })

    def test_the_spreadsheet_renders_with_both_sheets(self):
        invoice = self._invoice(
            lines=[(1000.0, self.income_account)], taxes=self.tax_sale_a)
        self._pay(invoice)
        self._generate()
        wizard = self._wizard()
        content, extension = self.env["ir.actions.report"]._render_xlsx(
            "l10n_cssk_cash_journal_base.dennik_xlsx", wizard.ids, data=None)
        self.assertEqual(extension, "xlsx")
        self.assertTrue(content)
        self.assertEqual(content[:2], b"PK", "a real xlsx archive")

    def test_the_spreadsheet_holds_the_rows_of_the_period(self):
        invoice = self._invoice(lines=[(1000.0, self.income_account)])
        self._pay(invoice, payment_date="2026-03-15")
        older = self._invoice(
            lines=[(50.0, self.income_account)], invoice_date="2025-01-10")
        self._pay(older, payment_date="2025-02-01")
        self._generate("2025-01-01", "2026-12-31")
        wizard = self._wizard()
        self.assertEqual(
            len(wizard._cssk_rows()), 1,
            "the period on the wizard decides, not everything in the book")

    def test_a_pdf_needs_a_country_layout(self):
        """The base has no layout of its own; it says so instead of crashing."""
        wizard = self._wizard()
        wizard.output = "pdf"
        if not wizard._cssk_pdf_report():
            with self.assertRaises(UserError):
                wizard.action_print()


class TestCashJournalAccountForm(TestCashJournalCommon):
    """The mapping has a page of its own on the account form.

    Worth a test because the inbound field existed for days with no UI at all —
    added for two-way accounts, reachable only from the chart mapping or the
    shell — and because an inherited page that stops matching its anchor fails
    silently at install on the next Odoo version.
    """

    def test_the_account_form_has_a_cash_journal_page_with_both_fields(self):
        arch = self.env["account.account"].get_view(
            self.env.ref("account.view_account_form").id, "form")["arch"]
        self.assertIn('name="cssk_cash_journal"', arch)
        self.assertIn('name="cssk_cash_category_id"', arch)
        self.assertIn('name="cssk_cash_category_in_id"', arch,
                      "the inbound category needs somewhere to be set")

    def test_both_fields_are_writable_from_the_form(self):
        account = self.expense_account
        account.write({
            "cssk_cash_category_id": self.cat_loan_out.id
            if hasattr(self, "cat_loan_out") else self.cat_goods.id,
            "cssk_cash_category_in_id": self.cat_other_income.id,
        })
        self.assertTrue(account.cssk_cash_category_in_id)


class TestCashCategoryConstraints(TestCashJournalCommon):

    def test_a_transit_category_cannot_reach_the_tax_base(self):
        with self.assertRaises(ValidationError):
            self.env["cssk.cash.category"].create({
                "code": "C9",
                "name": "Bad transit",
                "country_id": self.country.id,
                "kind": "transit",
                "taxable": True,
            })

    def test_a_category_code_is_unique_per_country(self):
        from psycopg2.errors import UniqueViolation
        with self.assertRaises(UniqueViolation), self.env.cr.savepoint():
            self.env["cssk.cash.category"].create({
                "code": "V1",
                "name": "Duplicate",
                "country_id": self.country.id,
                "kind": "expense",
            })

    def test_jednoduche_uctovnictvo_is_not_offered_to_a_czech_company(self):
        """CZ closed it to sole traders (§ 1f zákona 563/1991 Sb.)."""
        self.company.country_id = self.env.ref("base.cz")
        with self.assertRaises(ValidationError):
            self.company.cssk_bookkeeping_regime = "ju"
