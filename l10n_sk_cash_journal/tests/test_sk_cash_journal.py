# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestSkCashJournal(AccountTestInvoicingCommon):
    """The Slovak catalogue, the statutory grid and the DPFO figures."""

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.cssk_bookkeeping_regime = "de"

        def category(xmlid):
            return cls.env.ref("l10n_sk_cash_journal.%s" % xmlid)

        cls.cat_vyrobky = category("cat_p_vyrobky")
        cls.cat_zasoby = category("cat_v_zasoby")
        cls.cat_sluzby = category("cat_v_sluzby")
        cls.cat_poistne = category("cat_v_poistne_podnikatel")
        cls.cat_osobna = category("cat_vn_osobna_spotreba")
        cls.cat_priebezne = category("cat_c_priebezne")
        cls.cat_odpisy = category("cat_z_odpisy")

        cls.income_account = cls.company_data["default_account_revenue"]
        cls.expense_account = cls.company_data["default_account_expense"]
        cls.income_account.cssk_cash_category_id = cls.cat_vyrobky
        cls.expense_account.cssk_cash_category_id = cls.cat_zasoby

        cls.bank_journal = cls.company_data["default_journal_bank"]
        cls.cash_journal = cls.company_data["default_journal_cash"]
        cls.bank_journal.default_account_id.cssk_cash_category_id = \
            cls.cat_priebezne
        cls.cash_journal.default_account_id.cssk_cash_category_id = \
            cls.cat_priebezne

    # -- helpers -------------------------------------------------------

    def _invoice(self, move_type="out_invoice", amount=1000.0, account=None,
                 invoice_date="2026-02-01"):
        invoice = self.env["account.move"].create({
            "move_type": move_type,
            "partner_id": self.partner_a.id,
            "invoice_date": fields.Date.to_date(invoice_date),
            "date": fields.Date.to_date(invoice_date),
            "invoice_line_ids": [(0, 0, {
                "name": "položka",
                "quantity": 1.0,
                "price_unit": amount,
                "account_id": (account or self.income_account).id,
                "tax_ids": [(5, 0, 0)],
            })],
        })
        invoice.action_post()
        return invoice

    def _pay(self, invoice, journal=None, payment_date="2026-03-15"):
        wizard = self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=invoice.ids,
        ).create({
            "payment_date": fields.Date.to_date(payment_date),
            "journal_id": (journal or self.bank_journal).id,
        })
        return wizard._create_payments()

    def _generate(self):
        return self.env["cssk.cash.journal.line"]._cssk_regenerate(
            self.company,
            fields.Date.to_date("2026-01-01"),
            fields.Date.to_date("2026-12-31"),
        )

    # -- the catalogue -------------------------------------------------

    def test_the_statutory_categories_are_installed(self):
        """Opatrenie MF/27076/2007-74, § 4 — every column has a category."""
        categories = self.env["cssk.cash.category"].search([
            ("country_id", "=", self.env.ref("base.sk").id),
        ])
        codes = set(categories.mapped("code"))
        self.assertTrue(
            {"P1", "P2", "P3", "V1", "V2", "V3", "V4", "V5", "V6", "V9",
             "VN1", "VN2", "VN3", "C1", "Z1"} <= codes)

    def test_poistne_podnikatela_is_a_tax_expense_in_slovakia(self):
        """§ 19 ods. 3 písm. i) ZDP — the clearest CZ/SK difference.

        In the Czech Republic the same payment is non-deductible (§ 25 odst. 1
        písm. g), so the two catalogues must disagree here.
        """
        self.assertTrue(self.cat_poistne.taxable)
        self.assertEqual(self.cat_poistne.kind, "expense")

    def test_depreciation_is_a_non_cash_category(self):
        self.assertTrue(self.cat_odpisy.non_cash)
        self.assertTrue(self.cat_odpisy.taxable)

    # -- the grid ------------------------------------------------------

    def test_the_grid_puts_a_sale_in_its_statutory_column(self):
        invoice = self._invoice()
        self._pay(invoice)
        self._generate()
        values = self.env["report.l10n_sk_cash_journal.report_penazny_dennik"] \
            ._sk_dennik_values(
                self.company,
                fields.Date.to_date("2026-01-01"),
                fields.Date.to_date("2026-12-31"))
        self.assertEqual(len(values["lines"]), 1)
        cells = values["lines"][0]["cells"]
        self.assertAlmostEqual(cells["p_vyrobky"], 1000.0, places=2)
        self.assertAlmostEqual(cells["banka_prijem"], 1000.0, places=2)
        self.assertAlmostEqual(values["totals"]["p_vyrobky"], 1000.0, places=2)

    def test_the_running_balance_follows_the_bank(self):
        """§ 4 ods. 10 — the book must tie to the cash and bank balances."""
        sale = self._invoice(amount=1000.0)
        self._pay(sale, payment_date="2026-03-01")
        bill = self._invoice(move_type="in_invoice", amount=400.0,
                             account=self.expense_account)
        self._pay(bill, payment_date="2026-03-10")
        self._generate()
        values = self.env["report.l10n_sk_cash_journal.report_penazny_dennik"] \
            ._sk_dennik_values(
                self.company,
                fields.Date.to_date("2026-01-01"),
                fields.Date.to_date("2026-12-31"))
        self.assertAlmostEqual(values["closing_bank"], 600.0, places=2)

        # "The bank" is the bank account plus the transit accounts: without a
        # statement the money is still sitting on outstanding receipts, and with
        # one the two transit legs net out.
        money_accounts = self.bank_journal.default_account_id | self.env[
            "cssk.cash.journal.line"]._cssk_transit_accounts(self.company)
        ledger = self.env["account.move.line"].search([
            ("company_id", "=", self.company.id),
            ("parent_state", "=", "posted"),
            ("account_id", "in", money_accounts.ids),
        ])
        self.assertAlmostEqual(
            values["closing_bank"], sum(ledger.mapped("balance")), places=2,
            msg="the denník must reconcile to the bank account")

    def test_a_category_the_layout_does_not_name_still_appears(self):
        """Otherwise the columns would not add up to the money."""
        private = self.expense_account.copy({
            "code": "501900",
            "cssk_cash_category_id": self.cat_osobna.id,
        })
        bill = self._invoice(move_type="in_invoice", amount=250.0,
                             account=private)
        self._pay(bill)
        self._generate()
        values = self.env["report.l10n_sk_cash_journal.report_penazny_dennik"] \
            ._sk_dennik_values(
                self.company,
                fields.Date.to_date("2026-01-01"),
                fields.Date.to_date("2026-12-31"))
        self.assertAlmostEqual(values["totals"]["vn"], 250.0, places=2)

    # -- the tax return ------------------------------------------------

    def test_dpfo_tabulka_1_totals_come_from_the_book(self):
        sale = self._invoice(amount=1000.0)
        self._pay(sale, payment_date="2026-03-01")
        bill = self._invoice(move_type="in_invoice", amount=400.0,
                             account=self.expense_account)
        self._pay(bill, payment_date="2026-03-10")
        self._generate()

        wizard = self.env["l10n.sk.cash.dpfo"].create({
            "company_id": self.company.id,
            "date_from": fields.Date.to_date("2026-01-01"),
            "date_to": fields.Date.to_date("2026-12-31"),
        })
        wizard.action_compute()
        figures = {line.code: line.value for line in wizard.line_ids}
        self.assertAlmostEqual(figures["t1r10_prijmy"], 1000.0, places=2)
        self.assertAlmostEqual(figures["t1r10_vydavky"], 400.0, places=2)
        self.assertAlmostEqual(figures["zaklad"], 600.0, places=2)
        self.assertAlmostEqual(figures["t1r2"], 1400.0, places=2,
                               msg="both sides of § 6 ods. 1 b) carry the code")

    def test_a_non_taxable_payment_stays_out_of_the_tax_base(self):
        """An owner's withdrawal is in the book and not in the return."""
        private = self.expense_account.copy({
            "code": "501910",
            "cssk_cash_category_id": self.cat_osobna.id,
        })
        bill = self._invoice(move_type="in_invoice", amount=300.0,
                             account=private)
        self._pay(bill)
        self._generate()
        wizard = self.env["l10n.sk.cash.dpfo"].create({
            "company_id": self.company.id,
            "date_from": fields.Date.to_date("2026-01-01"),
            "date_to": fields.Date.to_date("2026-12-31"),
        })
        wizard.action_compute()
        figures = {line.code: line.value for line in wizard.line_ids}
        self.assertAlmostEqual(figures["t1r10_vydavky"], 0.0, places=2)

    def test_dpfo_tabulka_1a_balances_come_from_the_ledger(self):
        """Tabuľka 1a wants the state at both ends of the year."""
        self._invoice(amount=1000.0, invoice_date="2026-06-01")
        wizard = self.env["l10n.sk.cash.dpfo"].create({
            "company_id": self.company.id,
            "date_from": fields.Date.to_date("2026-01-01"),
            "date_to": fields.Date.to_date("2026-12-31"),
        })
        wizard.action_compute()
        rows = {line.code: line for line in wizard.line_ids
                if line.table == "t1a"}
        self.assertEqual(
            set(rows), {"r1", "r2", "r3", "r4", "r5", "r6"})
        self.assertAlmostEqual(rows["r4"].opening_value, 0.0, places=2)
        self.assertAlmostEqual(rows["r4"].closing_value, 1000.0, places=2,
                               msg="an unpaid invoice is a pohľadávka at year end")

    def test_a_flat_rate_payer_gets_tabulka_1b(self):
        """§ 6 ods. 10 with § 6 ods. 11 a) and d): zásoby and pohľadávky only."""
        self.company.cssk_bookkeeping_regime = "pausal"
        wizard = self.env["l10n.sk.cash.dpfo"].create({
            "company_id": self.company.id,
            "date_from": fields.Date.to_date("2026-01-01"),
            "date_to": fields.Date.to_date("2026-12-31"),
        })
        wizard.action_compute()
        tables = {line.table for line in wizard.line_ids}
        self.assertIn("t1b", tables)
        self.assertNotIn("t1a", tables)
        codes = {line.code for line in wizard.line_ids if line.table == "t1b"}
        self.assertEqual(codes, {"r3", "r4"})
