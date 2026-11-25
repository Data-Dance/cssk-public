# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""§ 74b odst. 3 a 4: the deduction on a bill six months overdue."""

from datetime import date

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestCzPar74b(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, lang="en_US"))
        cls.company = cls.company_data["company"]
        cls.company.vat = "CZ25663585"
        cls.company.l10n_cssk_tax_authority_id = cls.env[
            "cssk.tax.authority"].search(
            [("country_code", "=", "CZ"), ("submission_code", "=", "451")],
            limit=1)
        cls.version = cls.env.ref("l10n_cz_vat_return.dphdp3_version_2025")
        ref = cls.env["account.chart.template"].ref
        cls.purchase21 = ref("l10n_cz_21_receipt_domestic_supplies")
        cls.supplier = cls.env["res.partner"].create({
            "name": "Dodavatel s.r.o.", "vat": "CZ46342958",
            "country_id": cls.env.ref("base.cz").id})
        cls.cost = cls.env["account.account"].search([
            ("company_ids", "in", cls.company.id),
            ("code", "=like", "538%")], limit=1)
        cls.bank = cls.company_data["default_journal_bank"]

    def _bill(self, amount=1000.0, bill_date="2025-01-10", due="2025-01-24",
              tax=None, ref="FV-2025-001"):
        tax = tax or self.purchase21
        bill = self.env["account.move"].create({
            "move_type": "in_invoice", "partner_id": self.supplier.id,
            "ref": ref, "invoice_date": bill_date, "date": bill_date,
            "taxable_supply_date": bill_date, "invoice_date_due": due,
            "invoice_line_ids": [Command.create({
                "name": "zboží", "quantity": 1, "price_unit": amount,
                "tax_ids": [Command.set(tax.ids)]})],
        })
        bill.action_post()
        return bill

    def _pay(self, bill, amount, on):
        self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=bill.ids).create({
                "amount": amount, "payment_date": on,
                "journal_id": self.bank.id,
            })._create_payments()

    def _wizard(self, on="2025-08-15", **vals):
        return self.env["l10n.cz.par74b.wizard"].create(dict({
            "company_id": self.company.id, "date": on,
            "period_type": "month",
            "correction_account_id": self.cost.id}, **vals))

    def _correct(self, **kw):
        action = self._wizard(**kw).action_generate()
        Move = self.env["account.move"]
        return Move.browse(action["res_id"]) if action.get("res_id") \
            else Move.search(action["domain"])

    def _return(self, month_start, month_end):
        ret = self.env["cssk.vat.return"].create({
            "company_id": self.company.id, "version_id": self.version.id,
            "statement_type_id": self.env.ref(
                "l10n_cz_vat_return.dphdp3_type_B").id,
            "period_type": "month",
            "date_from": month_start, "date_to": month_end})
        ret.action_compute_lines()
        return {line.code: line.value for line in ret.line_ids}

    # ------------------------------------------------------------------
    def test_the_six_months_run_from_the_month_of_the_due_date(self):
        """§ 74b odst. 3: the last day of the sixth calendar month after
        the month in which the debt fell due."""
        deadline = self.env["account.move"]._l10n_cz_par74b_deadline_of
        self.assertEqual(deadline(date(2025, 1, 24)), date(2025, 7, 31))
        self.assertEqual(deadline(date(2025, 1, 31)), date(2025, 7, 31))
        self.assertEqual(deadline(date(2025, 8, 1)), date(2026, 2, 28))
        self.assertEqual(deadline(date(2027, 8, 31)), date(2028, 2, 29))
        self.assertFalse(deadline(False))

    def test_which_bills_are_offered(self):
        overdue = self._bill()
        not_yet = self._bill(bill_date="2025-03-01", due="2025-03-15",
                             ref="FV-2")
        paid = self._bill(ref="FV-3")
        self._pay(paid, 1210.0, "2025-02-01")
        # zákon č. 461/2024 Sb., čl. II bod 17: a deduction that arose
        # before 1. 1. 2025 is outside the new § 74b
        old = self._bill(bill_date="2024-12-20", due="2025-01-03", ref="FV-4")
        wizard = self._wizard()
        self.assertEqual(wizard.bill_ids, overdue)
        self.assertEqual(wizard.bill_count, 1)
        self.assertNotIn(not_yet, self._wizard(on="2025-09-29").bill_ids)
        self.assertIn(not_yet, self._wizard(on="2025-09-30").bill_ids)
        self.assertNotIn(old, self._wizard(on="2026-06-30").bill_ids)

    def test_a_reverse_charge_bill_is_not_offered(self):
        """No VAT is owed to the supplier, so none of the unpaid
        consideration is VAT."""
        rc = self.env["account.tax"].search([
            ("company_id", "=", self.company.id),
            ("type_tax_use", "=", "purchase"), ("amount", ">", 0)]).filtered(
            lambda t: any(r.factor_percent < 0 for r in
                          t.invoice_repartition_line_ids))[:1]
        if not rc:
            self.skipTest("the chart has no reverse-charge purchase tax")
        bill = self._bill(tax=rc)
        self.assertFalse(bill._l10n_cz_par74b_deducted())
        self.assertFalse(self._wizard().bill_ids)

    def test_the_correction_is_a_zero_document_on_the_deadline(self):
        bill = self._bill()
        correction = self._correct()
        self.assertEqual(correction.state, "draft",
                         "the accountant posts it")
        self.assertEqual(bill.l10n_cz_par74b_state, "draft")
        self.assertEqual(correction.move_type, "in_refund")
        self.assertEqual(correction.date, date(2025, 7, 31))
        self.assertEqual(correction.invoice_date, date(2025, 7, 31))
        self.assertEqual(correction.l10n_cz_bad_debt, "P")
        self.assertEqual(correction.ref, "FV-2025-001")
        self.assertEqual(correction.amount_total, 0.0)
        self.assertEqual(correction.amount_tax, 210.0)
        correction.action_post()
        self.assertEqual(bill.l10n_cz_par74b_state, "corrected")
        self.assertEqual(bill.amount_residual, 1210.0,
                         "the debt to the supplier is untouched")
        by_account = {}
        for line in correction.line_ids:
            by_account[line.account_id.code[:3]] = by_account.get(
                line.account_id.code[:3], 0.0) + line.balance
        self.assertEqual(by_account["343"], -210.0)
        self.assertEqual(by_account["538"], 210.0)
        self.assertEqual(by_account.get("321", 0.0), 0.0)

    def test_the_return_lowers_r40_and_shows_r34(self):
        """ř. 63 does not read ř. 34, so ř. 40 must carry the correction;
        ř. 34 repeats its tax."""
        self._bill()
        self._correct().action_post()
        self.assertEqual(
            self._return("2025-01-01", "2025-01-31")["odp_tuz23_nar"], 210.0)
        july = self._return("2025-07-01", "2025-07-31")
        self.assertEqual(july["pln23"], -1000.0)
        self.assertEqual(july["odp_tuz23_nar"], -210.0)
        self.assertEqual(july["opr_dluz"], 210.0)
        self.assertEqual(july["odp_zocelk"], -210.0)

    def test_a_part_payment_corrects_the_unpaid_share(self):
        """"Ve výši vypočtené z neposkytnuté úplaty"."""
        bill = self._bill()
        self._pay(bill, 302.5, "2025-03-01")       # a quarter
        correction = self._correct()
        self.assertEqual(correction.amount_tax, 157.5)
        self.assertEqual(correction.amount_total, 0.0)

    def test_a_payment_after_the_deadline_does_not_undo_the_duty(self):
        """The duty arose when the six months ran out; what is paid later
        gives the deduction back under odst. 4."""
        bill = self._bill()
        self._pay(bill, 1210.0, "2025-08-05")
        wizard = self._wizard(on="2025-08-15")
        self.assertEqual(wizard.bill_ids, bill)
        correction = self._correct(on="2025-08-15")
        self.assertEqual(correction.amount_tax, 210.0)
        correction.action_post()
        reclaim = self.env["account.move"].browse(
            bill.action_l10n_cz_par74b_reclaim()["res_id"])
        self.assertEqual(reclaim.amount_tax, 210.0)

    def test_a_quarterly_payer_has_until_the_end_of_the_quarter(self):
        """§ 74b odst. 3, second sentence."""
        bill = self._bill()                         # deadline 31. 7. 2025
        self._pay(bill, 1210.0, "2025-09-20")       # same quarter
        self.assertFalse(
            self._wizard(on="2025-10-05", period_type="quarter").bill_ids)
        self.assertEqual(
            self._wizard(on="2025-10-05", period_type="month").bill_ids, bill)
        late = self._bill(ref="FV-9")
        self.assertFalse(
            self._wizard(on="2025-09-29", period_type="quarter").bill_ids,
            "the quarter has not ended yet")
        self.assertEqual(
            self._wizard(on="2025-09-30", period_type="quarter").bill_ids,
            late)
        correction = self._correct(on="2025-09-30", period_type="quarter")
        self.assertEqual(correction.date, date(2025, 7, 31))

    def test_a_second_run_does_not_correct_twice(self):
        self._bill()
        correction = self._correct()
        self.assertFalse(self._wizard().bill_ids, "a draft is waiting")
        with self.assertRaisesRegex(UserError, "No bill meets"):
            self._wizard().action_generate()
        correction.action_post()
        self.assertFalse(self._wizard(on="2026-03-31").bill_ids)
        correction.button_draft()
        correction.button_cancel()
        self.assertTrue(self._wizard().bill_ids, "a cancelled one frees it")

    def test_the_deduction_comes_back_with_the_payment(self):
        """§ 74b odst. 4 and 6: from what was paid, counting what was
        already given back."""
        bill = self._bill()
        self._pay(bill, 302.5, "2025-03-01")
        self._correct().action_post()               # 157.50 corrected
        with self.assertRaisesRegex(UserError, "nothing to give back"):
            bill.action_l10n_cz_par74b_reclaim()
        self._pay(bill, 605.0, "2025-09-10")        # half of the bill
        first = self.env["account.move"].browse(
            bill.action_l10n_cz_par74b_reclaim()["res_id"])
        self.assertEqual(first.move_type, "in_invoice")
        self.assertEqual(first.l10n_cz_bad_debt, "P")
        self.assertTrue(first.l10n_cz_par74b_is_reclaim)
        self.assertEqual(first.amount_total, 0.0)
        self.assertEqual(first.amount_tax, 105.0)
        first.action_post()
        self.assertEqual(bill.l10n_cz_par74b_state, "reclaimed")
        with self.assertRaisesRegex(UserError, "nothing to give back"):
            bill.action_l10n_cz_par74b_reclaim()
        self._pay(bill, 302.5, "2025-10-10")        # the rest
        second = self.env["account.move"].browse(
            bill.action_l10n_cz_par74b_reclaim()["res_id"])
        self.assertEqual(second.amount_tax, 52.5)
        second.action_post()
        self.assertEqual(bill._l10n_cz_par74b_posted_vat(reclaim=True),
                         bill._l10n_cz_par74b_posted_vat(reclaim=False))
        vat = sum(first.line_ids.filtered(
            lambda l: l.account_id.code.startswith("343")).mapped("balance"))
        self.assertEqual(vat, 105.0, "the deduction is debited back")

    def test_a_draft_reclaim_counts(self):
        """Two drafts for one payment would give the deduction back
        twice once both are posted."""
        bill = self._bill()
        self._correct().action_post()
        self._pay(bill, 1210.0, "2025-09-10")
        bill.action_l10n_cz_par74b_reclaim()
        with self.assertRaisesRegex(UserError, "nothing to give back"):
            bill.action_l10n_cz_par74b_reclaim()

    def test_the_reclaim_has_two_calendar_years(self):
        """§ 74b odst. 9."""
        from freezegun import freeze_time

        bill = self._bill()
        self._correct().action_post()
        self._pay(bill, 1210.0, "2025-09-10")
        with freeze_time("2028-01-02"):
            with self.assertRaisesRegex(UserError, "odst. 9"):
                bill.action_l10n_cz_par74b_reclaim()
        with freeze_time("2027-12-31"):
            bill.action_l10n_cz_par74b_reclaim()

    def test_a_foreign_bill_is_measured_in_its_own_currency(self):
        """Half of a EUR bill paid is half unpaid, whatever the rate did
        between the bill and the payment."""
        eur = self.setup_other_currency(
            "EUR", rates=[("2025-01-01", 0.04), ("2025-03-01", 0.05)])
        bill = self.env["account.move"].create({
            "move_type": "in_invoice", "partner_id": self.supplier.id,
            "ref": "EUR-1", "currency_id": eur.id,
            "invoice_date": "2025-01-10", "date": "2025-01-10",
            "taxable_supply_date": "2025-01-10",
            "invoice_date_due": "2025-01-24",
            "invoice_line_ids": [Command.create({
                "name": "zboží", "quantity": 1, "price_unit": 1000.0,
                "tax_ids": [Command.set(self.purchase21.ids)]})],
        })
        bill.action_post()
        self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=bill.ids).create({
                "amount": 605.0, "currency_id": eur.id,
                "payment_date": "2025-03-05", "journal_id": self.bank.id,
            })._create_payments()
        self.assertAlmostEqual(
            bill._l10n_cz_par74b_unpaid_fraction(date(2025, 7, 31)), 0.5, 6)
        correction = self._correct()
        deducted = sum(
            vat for _b, vat in bill._l10n_cz_par74b_deducted().values())
        self.assertAlmostEqual(correction.amount_tax, deducted / 2, 2)
        self.assertEqual(correction.currency_id, self.company.currency_id)

    def test_a_bill_in_instalments_is_shown_not_corrected(self):
        """Each instalment has its own six months."""
        term = self.env["account.payment.term"].create({
            "name": "2 splátky", "line_ids": [
                Command.create({"value": "percent", "value_amount": 50,
                                "nb_days": 14}),
                Command.create({"value": "percent", "value_amount": 50,
                                "nb_days": 60})]})
        bill = self.env["account.move"].create({
            "move_type": "in_invoice", "partner_id": self.supplier.id,
            "ref": "SPL-1", "invoice_date": "2025-01-10",
            "date": "2025-01-10", "taxable_supply_date": "2025-01-10",
            "invoice_payment_term_id": term.id,
            "invoice_line_ids": [Command.create({
                "name": "zboží", "quantity": 1, "price_unit": 1000.0,
                "tax_ids": [Command.set(self.purchase21.ids)]})],
        })
        bill.action_post()
        wizard = self._wizard(on="2025-12-31")
        self.assertFalse(wizard.bill_ids)
        self.assertEqual(wizard.instalment_bill_ids, bill)
        with self.assertRaisesRegex(UserError, "No bill meets"):
            wizard.action_generate()

    def test_a_closed_period_is_refused_not_moved(self):
        """Odoo would move the document past the lock and put the
        correction in a later period by itself."""
        self._bill()
        self.company.tax_lock_date = "2025-07-31"
        with self.assertRaisesRegex(UserError, "closed period"):
            self._wizard().action_generate()
        correction = self._correct(book_on="date")
        self.assertEqual(correction.date, date(2025, 8, 15))

    def test_a_company_that_is_not_czech_is_offered_nothing(self):
        self._bill()
        self.company.account_fiscal_country_id = self.env.ref("base.sk")
        self.assertFalse(self._wizard().bill_ids)


@tagged("post_install", "-at_install")
class TestCzPar74bControlStatement(TestCzPar74b):
    """The correction in the kontrolní hlášení; skipped without l10n_cz_kh."""

    def setUp(self):
        super().setUp()
        self.kh_version = self.env.ref(
            "l10n_cz_kh.cz_kh_version_2025", raise_if_not_found=False)
        if not self.kh_version:
            self.skipTest("l10n_cz_kh is not installed")

    def test_the_correction_is_a_b2_row_with_zdph_44(self):
        """B.2 whatever the amount, under the supplier's number of the
        bill, base and tax negative."""
        import base64

        from lxml import etree

        self.company.write({
            "street": "Diabasová 1141/11", "zip": "155 00",
            "city": "Praha 13", "phone": "+420 511 447 174",
            "email": "dph@example.cz",
            "l10n_cz_epo_signatory_first_name": "Jana",
            "l10n_cz_epo_signatory_last_name": "Nováková",
            "l10n_cz_epo_signatory_position": "jednatelka",
        })
        self._bill(amount=1000.0)       # far below the 10 000 Kč threshold
        self._correct().action_post()
        st = self.env["cssk.control.statement"].create({
            "company_id": self.company.id, "version_id": self.kh_version.id,
            "date_from": "2025-07-01", "date_to": "2025-07-31",
            "period_type": "month",
            "statement_type_id": self.env.ref("l10n_cz_kh.cz_kh_type_B").id,
        })
        st.action_compute_lines()
        self.assertEqual(len(st.cz_b2_ids), 1)
        self.assertEqual(st.cz_b2_ids.entry_ref, "FV-2025-001")
        self.assertAlmostEqual(st.cz_b2_ids.base_std, -1000.0, places=2)
        self.assertAlmostEqual(st.cz_b2_ids.tax_std, -210.0, places=2)
        self.assertFalse(st.cz_b3_ids)
        st.action_export_xml()
        root = etree.fromstring(base64.b64decode(st.xml_attachment_id.datas))
        row = root.find(".//VetaB2")
        self.assertEqual(row.get("zdph_44"), "P")
        self.assertEqual(row.get("c_evid_dd"), "FV-2025-001")
        self.assertEqual(row.get("dic_dod"), "46342958")
        self.assertEqual(row.get("dan1"), "-210")
