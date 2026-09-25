from datetime import date

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestPurchaseAdvance(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids |= cls.env.ref("purchase.group_purchase_manager")
        company = cls.env.company
        Account = cls.env["account.account"]
        # payable type: the clearing is the payment-term leg of the tax doc
        cls.clearing = Account.create({
            "code": "314001",
            "name": "Paid advances clearing",
            "account_type": "liability_payable",
            "reconcile": True,
        })
        cls.net_advance = Account.create({
            "code": "314000",
            "name": "Paid advances",
            "account_type": "asset_current",
        })
        cls.adv_journal = cls.env["account.journal"].create({
            "name": "Advance Tax Documents (Purchase)",
            "code": "PDADV",
            "type": "purchase",
        })
        company.advance_purchase_journal_id = cls.adv_journal
        company.advance_paid_clearing_account_id = cls.clearing
        company.advance_paid_account_id = cls.net_advance

        cls.bank_journal = cls.company_data["default_journal_bank"]
        outstanding = Account.create({
            "code": "OUTPAY",
            "name": "Outstanding Payments",
            "account_type": "asset_current",
            "reconcile": True,
        })
        cls.bank_journal.outbound_payment_method_line_ids[
            :1
        ].payment_account_id = outstanding

        cls.service = cls.env["product.product"].create({
            "name": "Advance service",
            "type": "service",
            "purchase_method": "purchase",
            "supplier_taxes_id": [
                Command.set(cls.company_data["default_tax_purchase"].ids)
            ],
        })

    def _advance(self, price=1000.0, parent=None, partner=None):
        return self.env["purchase.order"].create({
            "partner_id": (partner or self.partner_a).id,
            "is_advance_invoice": True,
            "advance_invoice_parent_order_id": parent.id if parent else False,
            "order_line": [
                Command.create({
                    "product_id": self.service.id,
                    "product_qty": 1,
                    "price_unit": price,
                })
            ],
        })

    def _pay(self, order, amount=None):
        vals = {
            "journal_id": self.bank_journal.id,
            "payment_method_line_id":
                self.bank_journal.outbound_payment_method_line_ids[:1].id,
        }
        if amount is not None:
            vals["amount"] = amount
        wizard = (
            self.env["purchase.advance.payment.wizard"]
            .with_context(
                active_model="purchase.order", active_id=order.id
            )
            .create(vals)
        )
        wizard.action_create_payment()
        return order.advance_payment_ids[-1:]

    def _register_tax_doc(self, order, supplier_ref="DOD-2026-001", **vals):
        wizard = (
            self.env["purchase.advance.tax.doc.wizard"]
            .with_context(
                active_model="purchase.order", active_id=order.id
            )
            .create({"supplier_ref": supplier_ref, **vals})
        )
        action = wizard.action_create()
        return self.env["account.move"].browse(action["res_id"])

    # ------------------------------------------------------------------
    def test_sequence_and_statuses(self):
        advance = self._advance()
        self.assertTrue(advance.name.startswith("PADV"))
        self.assertEqual(advance.advance_invoice_payment_status, "none")
        self.assertEqual(
            advance.advance_invoice_accounting_status, "nothing_to_account"
        )

        self._pay(advance, amount=advance.amount_total / 2)
        self.assertEqual(
            advance.advance_invoice_payment_status, "paid_partially"
        )
        self.assertEqual(advance.advance_invoice_accounting_status, "waiting")
        self.assertEqual(advance.state, "purchase")

        self._pay(advance)
        self.assertEqual(advance.advance_invoice_payment_status, "paid_fully")
        self.assertEqual(advance.amount_paid, advance.amount_total)

    def test_expected_doc_date(self):
        advance = self._advance()
        # mid-month payment: +15 days wins
        self.assertEqual(
            advance._advance_invoice_tax_doc_deadline(date(2026, 7, 1)),
            date(2026, 7, 16),
        )
        # late-month payment: end of month wins
        self.assertEqual(
            advance._advance_invoice_tax_doc_deadline(date(2026, 7, 25)),
            date(2026, 7, 31),
        )

    def test_tax_doc_full_cycle(self):
        advance = self._advance()
        payment = self._pay(advance)
        self.assertEqual(payment.destination_account_id, self.clearing)

        tax_doc = self._register_tax_doc(advance)
        self.assertEqual(tax_doc.state, "draft")
        self.assertEqual(tax_doc.journal_id, self.adv_journal)
        self.assertEqual(tax_doc.ref, "DOD-2026-001")
        self.assertEqual(
            tax_doc.taxable_supply_date, advance.advance_invoice_paid_date
        )
        self.assertEqual(tax_doc.advance_purchase_order_id, advance)
        product_lines = tax_doc.invoice_line_ids.filtered(
            lambda line: line.display_type == "product"
        )
        self.assertTrue(product_lines)
        self.assertEqual(product_lines.account_id, self.net_advance)
        self.assertEqual(
            product_lines.tax_ids,
            self.company_data["default_tax_purchase"],
        )
        term_lines = tax_doc.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        )
        self.assertEqual(term_lines.account_id, self.clearing)
        self.assertEqual(
            tax_doc.currency_id.compare_amounts(
                tax_doc.amount_total, advance.amount_paid
            ),
            0,
        )

        tax_doc.action_post()
        clearing_lines = (
            payment.move_id + tax_doc
        ).line_ids.filtered(lambda line: line.account_id == self.clearing)
        self.assertTrue(all(clearing_lines.mapped("reconciled")))
        self.assertEqual(
            advance.advance_invoice_accounting_status, "accounted"
        )

        # a second tax document for the same payment must be refused
        with self.assertRaises(UserError):
            self._register_tax_doc(advance, supplier_ref="DOD-2026-002")

    def test_deduction_with_posted_tax_doc(self):
        advance = self._advance(price=400.0)
        self._pay(advance)
        tax_doc = self._register_tax_doc(advance)
        tax_doc.action_post()

        bill = self.env["account.move"].create({
            "move_type": "in_invoice",
            "partner_id": self.partner_a.id,
            "invoice_date": date(2026, 7, 15),
            "invoice_line_ids": [
                Command.create({
                    "product_id": self.service.id,
                    "quantity": 1,
                    "price_unit": 1000.0,
                })
            ],
        })
        wizard = self.env[
            "account.move.link.purchase.advance.wizard"
        ].with_context(
            active_model="account.move", active_id=bill.id
        ).create({})
        self.assertIn(advance, wizard.available_advance_ids)
        wizard.advance_ids = [Command.set(advance.ids)]
        wizard.action_link()

        deduction_lines = bill.invoice_line_ids.filtered(
            "advance_deduction_order_id"
        )
        self.assertTrue(deduction_lines)
        # net deduction with the same taxes → input-VAT reversal
        self.assertEqual(
            deduction_lines.tax_ids,
            self.company_data["default_tax_purchase"],
        )
        self.assertEqual(
            bill.currency_id.compare_amounts(
                bill.amount_total,
                self.service.currency_id.round(
                    1150.0 - advance.amount_paid
                ),
            ),
            0,
        )
        self.assertEqual(
            advance.currency_id.compare_amounts(
                advance._advance_deducted_amount_now(), advance.amount_paid
            ),
            0,
        )

    def test_deduction_gross_without_tax_doc(self):
        advance = self._advance(price=200.0)
        self._pay(advance)

        bill = self.env["account.move"].create({
            "move_type": "in_invoice",
            "partner_id": self.partner_a.id,
            "invoice_date": date(2026, 7, 15),
            "invoice_line_ids": [
                Command.create({
                    "product_id": self.service.id,
                    "quantity": 1,
                    "price_unit": 1000.0,
                })
            ],
        })
        wizard = self.env[
            "account.move.link.purchase.advance.wizard"
        ].with_context(
            active_model="account.move", active_id=bill.id
        ).create({"advance_ids": [Command.set(advance.ids)]})
        wizard.action_link()

        deduction_lines = bill.invoice_line_ids.filtered(
            "advance_deduction_order_id"
        )
        self.assertEqual(len(deduction_lines), 1)
        self.assertFalse(deduction_lines.tax_ids)
        self.assertEqual(deduction_lines.price_unit, -advance.amount_paid)

    def test_parent_po_auto_deduction(self):
        parent = self.env["purchase.order"].create({
            "partner_id": self.partner_a.id,
            "order_line": [
                Command.create({
                    "product_id": self.service.id,
                    "product_qty": 1,
                    "price_unit": 1000.0,
                })
            ],
        })
        advance = self._advance(price=300.0, parent=parent)
        self._pay(advance)

        parent.button_confirm()
        parent.action_create_invoice()
        bill = parent.invoice_ids.filtered(lambda m: m.state == "draft")[:1]
        self.assertTrue(bill)
        deduction_lines = bill.invoice_line_ids.filtered(
            lambda line: line.advance_deduction_order_id == advance
        )
        self.assertEqual(len(deduction_lines), 1)
        self.assertEqual(deduction_lines.price_unit, -advance.amount_paid)
