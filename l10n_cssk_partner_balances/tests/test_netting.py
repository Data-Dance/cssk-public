from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestNetting(AccountTestInvoicingCommon):
    """Functional tests for the zápočet (mutual-offset) agreement."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]

    def _setup_balances(self, receivable=1000.0, payable=600.0):
        out = self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[receivable], taxes=self.env["account.tax"], post=True,
        )
        bill = self.init_invoice(
            "in_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[payable], taxes=self.env["account.tax"], post=True,
        )
        ar_line = out.line_ids.filtered(
            lambda l: l.account_id.account_type == "asset_receivable"
        )
        ap_line = bill.line_ids.filtered(
            lambda l: l.account_id.account_type == "liability_payable"
        )
        return ar_line, ap_line

    def _make_agreement(self):
        wizard = self.env["cssk.netting.wizard"].create({
            "company_id": self.company.id,
            "partner_id": self.partner_a.id,
            "agreement_date": "2026-06-30",
        })
        res = wizard.action_create()
        return self.env["cssk.partner.netting.agreement"].browse(res["res_id"])

    def test_wizard_allocates_balanced(self):
        self._setup_balances(1000.0, 600.0)
        agr = self._make_agreement()
        self.assertTrue(agr.name.startswith("ZAP/"))
        self.assertAlmostEqual(agr.receivable_total, 600.0, places=2)  # partial
        self.assertAlmostEqual(agr.payable_total, 600.0, places=2)     # full
        self.assertAlmostEqual(agr.netting_amount, 600.0, places=2)
        self.assertTrue(agr.is_balanced)

    def test_post_reconciles(self):
        ar_line, ap_line = self._setup_balances(1000.0, 600.0)
        agr = self._make_agreement()
        agr.action_confirm()
        agr.action_send()
        agr.action_countersigned()
        agr.action_post()

        self.assertEqual(agr.state, "posted")
        self.assertTrue(agr.move_id)
        # AP fully offset (600 of 600); AR partially (600 of 1000 → 400 left).
        self.assertAlmostEqual(ap_line.amount_residual, 0.0, places=2)
        self.assertAlmostEqual(ar_line.amount_residual, 400.0, places=2)

    def test_post_requires_countersigned(self):
        self._setup_balances(1000.0, 600.0)
        agr = self._make_agreement()
        with self.assertRaises(UserError):
            agr.action_post()  # still draft

    def test_unilateral_posts_without_countersign(self):
        ar_line, ap_line = self._setup_balances(1000.0, 600.0)
        agr = self._make_agreement()
        agr.netting_mode = "unilateral"
        agr.action_confirm()
        agr.action_send()
        # No countersignature step — a delivered declaration is enough.
        agr.action_post()
        self.assertEqual(agr.state, "posted")
        self.assertAlmostEqual(ap_line.amount_residual, 0.0, places=2)
        self.assertAlmostEqual(ar_line.amount_residual, 400.0, places=2)

    def test_unilateral_post_requires_sent(self):
        self._setup_balances(1000.0, 600.0)
        agr = self._make_agreement()
        agr.netting_mode = "unilateral"
        agr.action_confirm()
        with self.assertRaises(UserError):
            agr.action_post()  # only 'confirmed', not yet delivered

    def test_unilateral_rejects_countersign(self):
        self._setup_balances(1000.0, 600.0)
        agr = self._make_agreement()
        agr.netting_mode = "unilateral"
        agr.action_confirm()
        agr.action_send()
        with self.assertRaises(UserError):
            agr.action_countersigned()

    def _render(self, agr):
        return self.env["ir.actions.report"]._render_qweb_html(
            "l10n_cssk_partner_balances.action_report_partner_netting", agr.ids
        )[0].decode()

    def test_pdf_bilateral_wording(self):
        self._setup_balances(1000.0, 600.0)
        agr = self._make_agreement()  # default = bilateral
        html = self._render(agr)
        self.assertIn("Dohoda o vzájomnom započítaní", html)
        self.assertIn("Za partnera", html)  # two-party signature block

    def test_pdf_unilateral_wording(self):
        self._setup_balances(1000.0, 600.0)
        agr = self._make_agreement()
        agr.netting_mode = "unilateral"
        html = self._render(agr)
        self.assertIn("jednostrannom započítaní", html)
        self.assertIn("§ 358", html)  # legal basis for unilateral set-off
        self.assertNotIn("Za partnera", html)  # single signature only

    def _invoice_line(self, move, account_type):
        return move.line_ids.filtered(
            lambda l: l.account_id.account_type == account_type
        )

    def _post_agreement(self, agr):
        agr.action_confirm()
        agr.action_send()
        agr.action_countersigned()
        agr.action_post()

    def test_per_line_partial_offsets_honoured(self):
        """Two 100 receivables each offset by 50 must BOTH end up with a
        residual of 50 — not one fully reconciled and one untouched."""
        inv1 = self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-01",
            amounts=[100.0], taxes=self.env["account.tax"], post=True,
        )
        inv2 = self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-02",
            amounts=[100.0], taxes=self.env["account.tax"], post=True,
        )
        bill = self.init_invoice(
            "in_invoice", partner=self.partner_a, invoice_date="2026-06-03",
            amounts=[100.0], taxes=self.env["account.tax"], post=True,
        )
        ar1 = self._invoice_line(inv1, "asset_receivable")
        ar2 = self._invoice_line(inv2, "asset_receivable")
        ap = self._invoice_line(bill, "liability_payable")

        agr = self.env["cssk.partner.netting.agreement"].create({
            "company_id": self.company.id,
            "partner_id": self.partner_a.id,
            "agreement_date": "2026-06-30",
            "line_ids": [
                (0, 0, {"move_line_id": ar1.id, "amount_to_offset": 50.0}),
                (0, 0, {"move_line_id": ar2.id, "amount_to_offset": 50.0}),
                (0, 0, {"move_line_id": ap.id, "amount_to_offset": 100.0}),
            ],
        })
        self._post_agreement(agr)

        self.assertAlmostEqual(ar1.amount_residual, 50.0, places=2)
        self.assertAlmostEqual(ar2.amount_residual, 50.0, places=2)
        self.assertAlmostEqual(ap.amount_residual, 0.0, places=2)

    def test_cancel_with_reversal_reopens_partial_offsets(self):
        """Cancelling with reversal unreconciles the clearing partials so all
        residuals return exactly to their pre-netting values."""
        inv1 = self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-01",
            amounts=[100.0], taxes=self.env["account.tax"], post=True,
        )
        inv2 = self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-02",
            amounts=[100.0], taxes=self.env["account.tax"], post=True,
        )
        bill = self.init_invoice(
            "in_invoice", partner=self.partner_a, invoice_date="2026-06-03",
            amounts=[100.0], taxes=self.env["account.tax"], post=True,
        )
        ar1 = self._invoice_line(inv1, "asset_receivable")
        ar2 = self._invoice_line(inv2, "asset_receivable")
        ap = self._invoice_line(bill, "liability_payable")

        agr = self.env["cssk.partner.netting.agreement"].create({
            "company_id": self.company.id,
            "partner_id": self.partner_a.id,
            "agreement_date": "2026-06-30",
            "line_ids": [
                (0, 0, {"move_line_id": ar1.id, "amount_to_offset": 50.0}),
                (0, 0, {"move_line_id": ar2.id, "amount_to_offset": 50.0}),
                (0, 0, {"move_line_id": ap.id, "amount_to_offset": 100.0}),
            ],
        })
        self._post_agreement(agr)
        self.assertAlmostEqual(ap.amount_residual, 0.0, places=2)

        agr.action_cancel_with_reversal()
        self.assertEqual(agr.state, "cancelled")
        # Pre-netting residuals fully restored on every offset item.
        self.assertAlmostEqual(ar1.amount_residual, 100.0, places=2)
        self.assertAlmostEqual(ar2.amount_residual, 100.0, places=2)
        self.assertAlmostEqual(ap.amount_residual, -100.0, places=2)
        self.assertFalse(ar1.reconciled)
        self.assertFalse(ar2.reconciled)
        self.assertFalse(ap.reconciled)
        # The clearing entry itself is neutralised against its reversal.
        self.assertTrue(all(agr.move_id.line_ids.mapped("reconciled")))

    def test_posted_agreement_not_deletable(self):
        self._setup_balances(1000.0, 600.0)
        agr = self._make_agreement()
        self._post_agreement(agr)
        with self.assertRaises(UserError):
            agr.unlink()

    def test_lines_frozen_after_draft(self):
        self._setup_balances(1000.0, 600.0)
        agr = self._make_agreement()
        agr.action_confirm()
        with self.assertRaises(UserError):
            agr.line_ids[0].write({"amount_to_offset": 10.0})
        with self.assertRaises(UserError):
            agr.line_ids[0].unlink()
        agr.action_reset_draft()
        agr.line_ids[0].write({"amount_to_offset": 10.0})  # draft again: OK

    def test_amount_to_offset_constraint(self):
        ar_line, ap_line = self._setup_balances(1000.0, 600.0)
        agreement_model = self.env["cssk.partner.netting.agreement"]
        base = {
            "company_id": self.company.id,
            "partner_id": self.partner_a.id,
            "agreement_date": "2026-06-30",
        }
        with self.assertRaises(ValidationError), self.cr.savepoint():  # zero
            agreement_model.create(dict(base, line_ids=[
                (0, 0, {"move_line_id": ar_line.id, "amount_to_offset": 0.0}),
            ]))
        with self.assertRaises(ValidationError), self.cr.savepoint():
            agreement_model.create(dict(base, line_ids=[  # negative
                (0, 0, {"move_line_id": ar_line.id,
                        "amount_to_offset": -5.0}),
            ]))
        with self.assertRaises(ValidationError), self.cr.savepoint():
            agreement_model.create(dict(base, line_ids=[  # above residual
                (0, 0, {"move_line_id": ap_line.id,
                        "amount_to_offset": 600.01}),
            ]))

    def test_wizard_credit_note_goes_to_payable_side(self):
        """Sign-aware allocation: an open customer credit note is a debt we
        owe the partner → offset on the payable side of the zápočet."""
        inv = self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-01",
            amounts=[100.0], taxes=self.env["account.tax"], post=True,
        )
        refund = self.init_invoice(
            "out_refund", partner=self.partner_a, invoice_date="2026-06-02",
            amounts=[30.0], taxes=self.env["account.tax"], post=True,
        )
        bill = self.init_invoice(
            "in_invoice", partner=self.partner_a, invoice_date="2026-06-03",
            amounts=[100.0], taxes=self.env["account.tax"], post=True,
        )
        ar_inv = self._invoice_line(inv, "asset_receivable")
        ar_refund = self._invoice_line(refund, "asset_receivable")
        ap_bill = self._invoice_line(bill, "liability_payable")

        agr = self._make_agreement()
        self.assertAlmostEqual(agr.receivable_total, 100.0, places=2)
        self.assertAlmostEqual(agr.payable_total, 100.0, places=2)  # 30 + 70
        refund_line = agr.line_ids.filtered(
            lambda l: l.move_line_id == ar_refund
        )
        self.assertEqual(refund_line.side, "payable")
        self.assertAlmostEqual(refund_line.amount_to_offset, 30.0, places=2)
        self.assertTrue(agr.is_balanced)

        self._post_agreement(agr)
        self.assertAlmostEqual(ar_inv.amount_residual, 0.0, places=2)
        self.assertAlmostEqual(ar_refund.amount_residual, 0.0, places=2)
        self.assertAlmostEqual(ap_bill.amount_residual, -30.0, places=2)

    def test_cancel_with_reversal_reopens(self):
        ar_line, ap_line = self._setup_balances(1000.0, 600.0)
        agr = self._make_agreement()
        agr.action_confirm()
        agr.action_send()
        agr.action_countersigned()
        agr.action_post()
        self.assertAlmostEqual(ap_line.amount_residual, 0.0, places=2)

        agr.action_cancel_with_reversal()
        self.assertEqual(agr.state, "cancelled")
        # Reversal reopens the offset: balances restored.
        self.assertAlmostEqual(ap_line.amount_residual, -600.0, places=2)
        self.assertAlmostEqual(ar_line.amount_residual, 1000.0, places=2)
