from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestSkPar53b(AccountTestInvoicingCommon):
    """§ 53b oprava odpočítanej dane workflow + § 79 carry settlement."""

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.write({"vat": "SK2023456787", "city": "Bratislava",
                           "country_id": cls.env.ref("base.sk").id})
        cls.version = cls.env.ref("l10n_sk_vat_return.dph_version_2025")
        Tag = cls.env["account.account.tag"]
        cls.tag29 = Tag._get_tax_tags("29", cls.env.ref("base.sk").id)
        if not cls.tag29:
            cls.tag29 = Tag.create({
                "name": "29", "applicability": "taxes",
                "country_id": cls.env.ref("base.sk").id})

    def _unpaid_bill(self, due="2026-01-01"):
        bill = self.init_invoice(
            "in_invoice", partner=self.partner_a, invoice_date="2025-12-15",
            amounts=[1000.0], taxes=self.tax_purchase_a, post=False)
        bill.invoice_date_due = due
        bill.action_post()
        return bill

    def _wizard(self, date="2026-06-30"):
        return self.env["l10n.sk.par53b.wizard"].create({
            "company_id": self.company.id, "date": date,
            "journal_id": self.company_data["default_journal_misc"].id,
            "correction_account_id":
                self.company_data["default_account_expense"].id,
        })

    def _pay(self, bill, amount, date="2026-07-01"):
        self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=bill.ids,
        ).create({
            "amount": amount,
            "journal_id": self.company_data["default_journal_bank"].id,
            "payment_date": date,
        })._create_payments()

    def _return(self):
        return self.env["cssk.vat.return"].create({
            "company_id": self.company.id, "version_id": self.version.id,
            "date_from": "2026-06-01", "date_to": "2026-06-30",
            "period_type": "month",
            "statement_type_id": self.version.statement_type_ids[0].id})

    def test_par53b_correction_feeds_r29(self):
        bill = self._unpaid_bill()
        vat = sum(bill.line_ids.filtered("tax_line_id").mapped("balance"))
        self.assertGreater(vat, 0, "bill must have deducted input VAT")

        wiz = self._wizard()
        self.assertIn(bill, wiz.bill_ids, "unpaid >100 days bill must qualify")
        wiz.action_generate()

        corr = bill.l10n_sk_par53b_correction_ids
        self.assertEqual(len(corr), 1)
        self.assertEqual(corr.state, "posted")
        self.assertEqual(bill.l10n_sk_par53b_state, "corrected")
        # the VAT-account line credits 343 and carries the r29 (§ 53b) tag
        vat_line = corr.line_ids.filtered("tax_tag_ids")
        self.assertEqual(vat_line.tax_tag_ids, self.tag29)
        self.assertAlmostEqual(vat_line.credit, vat, places=2)

        # the DPH return for the correction period reports r29 = +VAT (the
        # § 53b add-back increases the tax due), so r_net / r32 rise by VAT.
        ret = self._return()
        ret.action_compute_lines()
        vals = {line.code: line.value for line in ret.line_ids}
        self.assertAlmostEqual(vals["r29"], vat, places=2)
        self.assertAlmostEqual(vals["r32"], vat, places=2)   # daň na úhradu
        self.assertAlmostEqual(vals["r33"], 0.0, places=2)   # not an excess

    def test_par53b_idempotent_and_reclaim(self):
        bill = self._unpaid_bill()
        vat = sum(bill.line_ids.filtered("tax_line_id").mapped("balance"))
        self._wizard().action_generate()
        # already corrected → no longer offered
        self.assertNotIn(bill, self._wizard().bill_ids)

        # § 53b ods. 6 works AFTER payment — nothing paid yet, no re-claim
        with self.assertRaises(UserError):
            bill.action_par53b_reclaim()

        # full payment → the re-claim re-deducts the full corrected VAT
        self._pay(bill, bill.amount_total)
        self.assertIn(bill.payment_state, ("in_payment", "paid"))
        bill.action_par53b_reclaim()
        self.assertEqual(bill.l10n_sk_par53b_state, "reclaimed")
        reclaim = bill.l10n_sk_par53b_correction_ids.filtered(
            "l10n_sk_par53b_is_reclaim")
        self.assertEqual(len(reclaim), 1)
        self.assertEqual(reclaim.state, "posted")
        # the re-claim re-deducts: debits the VAT account, same r29 tag
        vat_line = reclaim.line_ids.filtered("tax_tag_ids")
        self.assertEqual(vat_line.tax_tag_ids, self.tag29)
        self.assertAlmostEqual(vat_line.debit, vat, places=2)

        # a second re-claim would exceed what the correction un-deducted
        with self.assertRaises(UserError):
            bill.action_par53b_reclaim()

    def test_par53b_reclaim_proportional_and_capped(self):
        """§ 53b ods. 6: partial payment re-claims the paid share of the
        corrected VAT; further re-claims only follow further payments and the
        cumulative re-claims never exceed the corrections."""
        bill = self._unpaid_bill()
        vat = sum(bill.line_ids.filtered("tax_line_id").mapped("balance"))
        self._wizard().action_generate()  # corrects the full VAT (unpaid bill)

        self._pay(bill, bill.amount_total / 2.0)
        self.assertEqual(bill.payment_state, "partial")
        bill.action_par53b_reclaim()
        reclaims = bill.l10n_sk_par53b_correction_ids.filtered(
            "l10n_sk_par53b_is_reclaim")
        vat_line = reclaims.line_ids.filtered("tax_tag_ids")
        self.assertAlmostEqual(vat_line.debit, vat / 2.0, places=2)

        # no new payment → nothing more to re-claim (no double-reclaim)
        with self.assertRaises(UserError):
            bill.action_par53b_reclaim()

        # pay the rest → the second re-claim tops up to exactly the correction
        self._pay(bill, bill.amount_total / 2.0, date="2026-07-15")
        bill.action_par53b_reclaim()
        reclaims = bill.l10n_sk_par53b_correction_ids.filtered(
            "l10n_sk_par53b_is_reclaim")
        self.assertEqual(len(reclaims), 2)
        total = sum(reclaims.line_ids.filtered("tax_tag_ids").mapped("debit"))
        self.assertAlmostEqual(total, vat, places=2)
        with self.assertRaises(UserError):
            bill.action_par53b_reclaim()

    def test_par53b_proportional_on_partial(self):
        """A partially-paid bill reverses only the unpaid share of the VAT."""
        bill = self._unpaid_bill()
        vat = sum(bill.line_ids.filtered("tax_line_id").mapped("balance"))
        self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=bill.ids,
        ).create({
            "amount": bill.amount_total / 2.0,
            "journal_id": self.company_data["default_journal_bank"].id,
            "payment_date": "2026-02-01",
        })._create_payments()
        self.assertEqual(bill.payment_state, "partial")

        self._wizard().action_generate()
        vat_line = bill.l10n_sk_par53b_correction_ids.line_ids.filtered(
            "tax_tag_ids")
        self.assertAlmostEqual(vat_line.credit, vat / 2.0, places=2)

    def test_to_pay_79_carry(self):
        """§ 79 settlement: to_pay = r32 − r33 − carried_in + carried_out."""
        self.init_invoice("out_invoice", partner=self.partner_a,
                          invoice_date="2026-06-10", amounts=[1000.0],
                          taxes=self.tax_sale_a, post=True)
        ret = self._return()
        ret.action_compute_lines()
        # r32 = 230, r33 = 0, no carry → to_pay 230 (matches UHRADIT)
        self.assertAlmostEqual(ret.to_pay, 230.0, places=2)
        ret.excess_carried_in = 50.0
        self.assertAlmostEqual(ret.to_pay, 180.0, places=2)  # 230 − 50 carried in

    def test_carry_pull_from_prior_period(self):
        """A prior excess period's carried_out flows into the next return."""
        prior = self.env["cssk.vat.return"].create({
            "company_id": self.company.id, "version_id": self.version.id,
            "date_from": "2026-05-01", "date_to": "2026-05-31",
            "period_type": "month",
            "statement_type_id": self.version.statement_type_ids[0].id})
        prior.excess_carried_out = 120.0
        nxt = self._return()
        nxt.action_pull_prior_carry()
        self.assertEqual(nxt.prior_return_id, prior)
        self.assertAlmostEqual(nxt.excess_carried_in, 120.0, places=2)
