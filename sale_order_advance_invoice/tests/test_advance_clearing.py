# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Every way a payment reaches an advance ends on the clearing account.

The tax document raised on a payment puts its receivable leg on the advance
clearing account, and posting it reconciles that leg with the payment there.
Only *Register Payment* (and the bank matching add-on) used to book the
payment to that account. An online provider payment, or a transfer attached
with *Link Manual Transfer*, stayed on the customer's receivable, and the
clearing account was left with an open balance per advance.
"""

from odoo.tests import tagged

from .common import AdvanceInvoiceCommon


@tagged("post_install", "-at_install")
class TestAdvanceClearing(AdvanceInvoiceCommon):

    def setUp(self):
        super().setUp()
        self._configure_advance_accounts()
        self.clearing = self.env.company.advance_received_account_id
        self.clearing.reconcile = True
        self.bank = self.env["account.journal"].search(
            [("type", "=", "bank"), ("company_id", "=", self.env.company.id)], limit=1
        )

    def _confirmed_advance(self):
        advance = self._advance(self._order(), include_items=True)
        advance.action_confirm()
        return advance

    def _post_tax_document(self, advance):
        advance.action_create_invoice_direct_for_advance()
        tax_doc = advance.invoice_ids.filtered(lambda m: m.state == "draft")
        tax_doc.action_post()
        return tax_doc

    def _clearing_balance(self, partner):
        lines = self.env["account.move.line"].search([
            ("account_id", "=", self.clearing.id),
            ("partner_id", "child_of", partner.commercial_partner_id.id),
            ("parent_state", "=", "posted"),
        ])
        return sum(lines.mapped("balance")), lines

    def test_an_online_payment_is_booked_to_the_clearing_account(self):
        advance = self._confirmed_advance()
        provider = self.env["payment.provider"].create({
            "name": "Online", "code": "none", "journal_id": self.bank.id,
            "company_id": self.env.company.id,
        })
        self.bank._get_available_payment_method_lines("inbound")[:1].payment_provider_id = provider
        tx = self.env["payment.transaction"].sudo().create({
            "provider_id": provider.id,
            "payment_method_id": advance._get_payment_method_for_provider(provider).id,
            "reference": "ONLINE-%s" % advance.name,
            "amount": advance.amount_total,
            "currency_id": advance.currency_id.id,
            "partner_id": advance.partner_id.id,
            "operation": "online_redirect",
            "state": "done",
            "sale_order_ids": [(6, 0, advance.ids)],
        })
        payment = tx._create_payment()
        self.assertEqual(payment.destination_account_id, self.clearing)

        self._post_tax_document(advance)
        balance, lines = self._clearing_balance(advance.partner_id)
        self.assertAlmostEqual(balance, 0.0, places=2)
        self.assertTrue(all(lines.mapped("reconciled")))

    def test_a_linked_manual_transfer_is_carried_to_the_clearing_account(self):
        advance = self._confirmed_advance()
        payment = self.env["account.payment"].create({
            "payment_type": "inbound",
            "partner_type": "customer",
            "partner_id": self.partner.id,
            "amount": advance.amount_total,
            "journal_id": self.bank.id,
        })
        payment.action_post()
        receivable = payment.destination_account_id
        self.assertNotEqual(receivable, self.clearing)

        self.env["sale.order.manual.transfer.link.wizard"].create({
            "sale_order_id": advance.id,
            "payment_id": payment.id,
        }).action_link_manual_transfer()
        self.assertEqual(advance.advance_invoice_payment_status, "paid_fully")
        self.assertTrue(advance.advance_clearing_transfer_ids)
        self.assertTrue(
            payment.move_id.line_ids.filtered(
                lambda line: line.account_id == receivable
            ).reconciled,
            "the payment's receivable leg is cleared by the transfer",
        )

        self._post_tax_document(advance)
        balance, lines = self._clearing_balance(advance.partner_id)
        self.assertAlmostEqual(balance, 0.0, places=2)
        self.assertTrue(all(lines.mapped("reconciled")),
                        "the tax document did not meet the payment")
