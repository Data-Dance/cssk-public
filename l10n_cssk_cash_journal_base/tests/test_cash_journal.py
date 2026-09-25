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
