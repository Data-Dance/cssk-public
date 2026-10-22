# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestCzCashJournal(AccountTestInvoicingCommon):
    """The Czech catalogue, the deník layout and Příloha č. 1."""

    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.cssk_bookkeeping_regime = "de"

        def category(xmlid):
            return cls.env.ref("l10n_cz_cash_journal.%s" % xmlid)

        cls.cat_vyrobky = category("cat_p_vyrobky")
        cls.cat_material = category("cat_v_material")
        cls.cat_rezie = category("cat_v_rezie")
        cls.cat_pojistne = category("cat_vn_pojistne_podnikatele")
        cls.cat_osobni = category("cat_vn_osobni_spotreba")
        cls.cat_prubezne = category("cat_c_prubezne")
        cls.cat_odpisy = category("cat_z_odpisy")

        cls.income_account = cls.company_data["default_account_revenue"]
        cls.expense_account = cls.company_data["default_account_expense"]
        cls.income_account.cssk_cash_category_id = cls.cat_vyrobky
        cls.expense_account.cssk_cash_category_id = cls.cat_material

        cls.bank_journal = cls.company_data["default_journal_bank"]
        cls.cash_journal = cls.company_data["default_journal_cash"]

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

    def _pay(self, invoice, payment_date="2026-03-15"):
        wizard = self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=invoice.ids,
        ).create({
            "payment_date": fields.Date.to_date(payment_date),
            "journal_id": self.bank_journal.id,
        })
        return wizard._create_payments()

    def _generate(self):
        return self.env["cssk.cash.journal.line"]._cssk_regenerate(
            self.company,
            fields.Date.to_date("2026-01-01"),
            fields.Date.to_date("2026-12-31"),
        )

    def _priloha(self):
        wizard = self.env["l10n.cz.cash.priloha"].create({
            "company_id": self.company.id,
            "date_from": fields.Date.to_date("2026-01-01"),
            "date_to": fields.Date.to_date("2026-12-31"),
        })
        wizard.action_compute()
        return wizard

    # -- the catalogue -------------------------------------------------

    def test_the_czech_categories_are_installed(self):
        categories = self.env["cssk.cash.category"].search([
            ("country_id", "=", self.env.ref("base.cz").id),
        ])
        codes = set(categories.mapped("code"))
        self.assertTrue(
            {"P1", "P2", "V1", "V2", "V4", "V5", "V6",
             "VN1", "VN5", "C1", "Z1", "Z2"} <= codes)

    def test_pojistne_podnikatele_is_not_deductible_in_czechia(self):
        """§ 25 odst. 1 písm. g) ZDP — and Slovakia says the opposite.

        The same payment is a tax expense under SK § 19 ods. 3 písm. i), so the
        two catalogues must disagree here. This is the test that would catch
        someone "harmonising" them.
        """
        self.assertFalse(self.cat_pojistne.taxable)
        self.assertEqual(self.cat_pojistne.kind, "expense")

        slovak = self.env["cssk.cash.category"].search([
            ("country_id", "=", self.env.ref("base.sk").id),
            ("code", "=", "V4"),
        ])
        if slovak:
            self.assertTrue(
                slovak.taxable,
                "poistné podnikateľa is deductible in Slovakia; the catalogues "
                "are not translations of each other")

    # -- the deník -----------------------------------------------------

    def test_the_denik_puts_a_sale_in_its_column(self):
        invoice = self._invoice()
        self._pay(invoice)
        self._generate()
        values = self.env["report.l10n_cz_cash_journal.report_penezni_denik"] \
            ._cz_denik_values(
                self.company,
                fields.Date.to_date("2026-01-01"),
                fields.Date.to_date("2026-12-31"))
        self.assertEqual(len(values["lines"]), 1)
        cells = values["lines"][0]["cells"]
        self.assertAlmostEqual(cells["p_vyrobky"], 1000.0, places=2)
        self.assertAlmostEqual(cells["banka_prijem"], 1000.0, places=2)
        self.assertAlmostEqual(values["closing_bank"], 1000.0, places=2)

    def test_the_owners_insurance_is_in_the_book_but_not_in_the_tax_base(self):
        """The Czech difference, end to end: in the deník, out of ř. 102."""
        insurance = self.expense_account.copy({
            "code": "526900",
            "cssk_cash_category_id": self.cat_pojistne.id,
        })
        bill = self._invoice(move_type="in_invoice", amount=800.0,
                             account=insurance)
        self._pay(bill)
        self._generate()

        values = self.env["report.l10n_cz_cash_journal.report_penezni_denik"] \
            ._cz_denik_values(
                self.company,
                fields.Date.to_date("2026-01-01"),
                fields.Date.to_date("2026-12-31"))
        self.assertAlmostEqual(values["totals"]["vn"], 800.0, places=2)
        self.assertAlmostEqual(values["closing_bank"], -800.0, places=2)

        figures = {line.code: line.value for line in self._priloha().line_ids}
        self.assertAlmostEqual(figures["r102"], 0.0, places=2)

    # -- Příloha č. 1 --------------------------------------------------

    def test_priloha_rows_101_and_102_come_from_the_book(self):
        sale = self._invoice(amount=1000.0)
        self._pay(sale, payment_date="2026-03-01")
        bill = self._invoice(move_type="in_invoice", amount=400.0,
                             account=self.expense_account)
        self._pay(bill, payment_date="2026-03-10")
        self._generate()

        figures = {line.code: line.value for line in self._priloha().line_ids}
        self.assertAlmostEqual(figures["r101"], 1000.0, places=2)
        self.assertAlmostEqual(figures["r102"], 400.0, places=2)
        self.assertAlmostEqual(figures["r104"], 600.0, places=2)

    def test_oddil_d_reports_both_ends_of_the_period(self):
        self._invoice(amount=1000.0, invoice_date="2026-06-01")
        rows = {line.code: line for line in self._priloha().line_ids
                if line.section == "d"}
        self.assertEqual(
            set(rows), {"d1", "d2", "d3", "d4", "d5", "d6", "d7", "d8", "d9"})
        self.assertAlmostEqual(rows["d5"].opening_value, 0.0, places=2)
        self.assertAlmostEqual(rows["d5"].closing_value, 1000.0, places=2,
                               msg="an unpaid invoice is a pohledávka at year end")

    def test_dluhy_are_reported_as_a_positive_amount(self):
        """Oddíl D asks for dluhy, not for a negative asset."""
        bill = self._invoice(move_type="in_invoice", amount=700.0,
                             account=self.expense_account,
                             invoice_date="2026-06-01")
        self.assertEqual(bill.state, "posted")
        rows = {line.code: line for line in self._priloha().line_ids
                if line.section == "d"}
        self.assertAlmostEqual(rows["d7"].closing_value, 700.0, places=2)

    def test_the_zapis_is_printable(self):
        """§ 7b odst. 4 wants a written record; it must actually render."""
        self._invoice(amount=500.0, invoice_date="2026-06-01")
        wizard = self._priloha()
        report = self.env.ref(
            "l10n_cz_cash_journal.action_report_zapis_o_zjisteni")
        html = self.env["ir.actions.report"]._render_qweb_html(
            report.report_name, wizard.ids)[0]
        self.assertIn(b"7b odst. 4", html)
        self.assertIn("Pohledávky".encode(), html)
