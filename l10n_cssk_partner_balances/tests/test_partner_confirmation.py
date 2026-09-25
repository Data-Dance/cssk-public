from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestPartnerConfirmation(AccountTestInvoicingCommon):
    """Functional tests for the saldokonto confirmation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]

    def _post_receivable(self, amount, date="2026-06-10"):
        inv = self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date=date,
            amounts=[amount], taxes=self.env["account.tax"], post=True,
        )
        return inv

    def _pay(self, invoice, payment_date):
        return self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=invoice.ids
        ).create({"payment_date": payment_date})._create_payments()

    def _make_confirmation(self, as_of_date="2026-06-30"):
        return self.env["cssk.partner.confirmation"].create({
            "company_id": self.company.id,
            "partner_id": self.partner_a.id,
            "as_of_date": as_of_date,
            "confirmation_type": "both",
        })

    def test_snapshot_and_totals(self):
        self._post_receivable(1000.0)
        conf = self._make_confirmation()
        conf.action_compute_lines()

        self.assertTrue(conf.name.startswith("SALDO/"))
        self.assertEqual(len(conf.line_ids), 1)
        line = conf.line_ids
        self.assertEqual(line.account_type, "asset_receivable")
        self.assertAlmostEqual(line.amount_residual, 1000.0, places=2)
        self.assertAlmostEqual(conf.total_receivable, 1000.0, places=2)
        self.assertAlmostEqual(conf.total_payable, 0.0, places=2)
        self.assertAlmostEqual(conf.net_balance, 1000.0, places=2)

    def test_blocked_line_excluded_from_totals(self):
        self._post_receivable(1000.0)
        conf = self._make_confirmation()
        conf.action_compute_lines()
        conf.line_ids.write({"blocked": True})
        self.assertAlmostEqual(conf.total_receivable, 0.0, places=2)
        self.assertAlmostEqual(conf.net_balance, 0.0, places=2)

    def test_workflow_states(self):
        self._post_receivable(500.0)
        conf = self._make_confirmation()
        conf.action_compute_lines()
        self.assertEqual(conf.state, "draft")
        conf.action_send()
        self.assertEqual(conf.state, "sent")
        conf.action_agreed()
        self.assertEqual(conf.state, "agreed")

    def test_snapshot_is_as_of_date_not_today(self):
        """An invoice open on 31.12 but paid in January must still appear
        (with its FULL amount) on a 31.12 confirmation generated later."""
        inv = self._post_receivable(1000.0, date="2026-11-10")
        self._pay(inv, "2027-01-15")
        ar_line = inv.line_ids.filtered(
            lambda l: l.account_id.account_type == "asset_receivable"
        )
        self.assertTrue(ar_line.reconciled)  # paid by "today"

        conf = self._make_confirmation(as_of_date="2026-12-31")
        conf.action_compute_lines()
        self.assertEqual(len(conf.line_ids), 1)
        self.assertEqual(conf.line_ids.move_line_id, ar_line)
        self.assertAlmostEqual(conf.line_ids.amount_residual, 1000.0, places=2)
        self.assertAlmostEqual(conf.total_receivable, 1000.0, places=2)

    def test_snapshot_after_payment_date_is_empty(self):
        """As of 31.1 (after the January payment) the item is closed."""
        inv = self._post_receivable(1000.0, date="2026-11-10")
        self._pay(inv, "2027-01-15")
        conf = self._make_confirmation(as_of_date="2027-01-31")
        conf.action_compute_lines()
        self.assertFalse(conf.line_ids)
        self.assertAlmostEqual(conf.net_balance, 0.0, places=2)

    def test_snapshot_partial_payment_after_date(self):
        """A partial payment after the as-of date is added back in full."""
        inv = self._post_receivable(1000.0, date="2026-11-10")
        self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=inv.ids
        ).create({
            "payment_date": "2027-01-15", "amount": 400.0,
        })._create_payments()
        conf = self._make_confirmation(as_of_date="2026-12-31")
        conf.action_compute_lines()
        self.assertAlmostEqual(conf.line_ids.amount_residual, 1000.0, places=2)

    def test_state_transition_guards(self):
        self._post_receivable(500.0)
        conf = self._make_confirmation()
        conf.action_compute_lines()
        # draft: cannot agree/dispute/reset before sending
        with self.assertRaises(UserError):
            conf.action_agreed()
        with self.assertRaises(UserError):
            conf.action_disputed()
        with self.assertRaises(UserError):
            conf.action_reset_draft()
        conf.action_send()
        with self.assertRaises(UserError):
            conf.action_send()  # already sent
        conf.action_agreed()
        with self.assertRaises(UserError):
            conf.action_disputed()  # agreed is not re-disputable directly
        conf.action_cancel()
        with self.assertRaises(UserError):
            conf.action_cancel()  # already cancelled
        with self.assertRaises(UserError):
            conf.action_agreed()

    def test_agreed_confirmation_frozen(self):
        """Lines of an agreed confirmation are frozen; the record cannot be
        deleted in agreed/disputed states."""
        self._post_receivable(500.0)
        conf = self._make_confirmation()
        conf.action_compute_lines()
        conf.action_send()
        conf.action_agreed()
        with self.assertRaises(UserError):
            conf.line_ids.write({"blocked": True})
        with self.assertRaises(UserError):
            conf.line_ids.unlink()
        with self.assertRaises(UserError):
            conf.unlink()
        # back in draft everything is editable again
        conf.action_reset_draft()
        conf.line_ids.write({"blocked": True})
        conf.unlink()

    def test_bulk_wizard(self):
        self._post_receivable(700.0)
        wizard = self.env["cssk.partner.confirmation.wizard"].create({
            "company_id": self.company.id,
            "as_of_date": "2026-06-30",
            "confirmation_type": "both",
        })
        result = wizard.action_generate()
        confs = self.env["cssk.partner.confirmation"].search(result["domain"])
        self.assertTrue(confs)
        partner_conf = confs.filtered(
            lambda c: c.partner_id == self.partner_a
        )
        self.assertTrue(partner_conf)
        self.assertAlmostEqual(
            partner_conf.total_receivable, 700.0, places=2
        )
