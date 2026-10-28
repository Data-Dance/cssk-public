# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAdvanceNoReceipt(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids |= (
            cls.env.ref("purchase.group_purchase_manager")
            | cls.env.ref("stock.group_stock_user")
        )
        company = cls.env.company
        Account = cls.env["account.account"]
        company.advance_paid_clearing_account_id = Account.create({
            "code": "314001",
            "name": "Paid advances clearing",
            "account_type": "liability_payable",
            "reconcile": True,
        })
        company.advance_paid_account_id = Account.create({
            "code": "314000",
            "name": "Paid advances",
            "account_type": "asset_current",
        })
        company.advance_purchase_journal_id = cls.env["account.journal"].create({
            "name": "Advance Tax Documents (Purchase)",
            "code": "PDADV",
            "type": "purchase",
        })
        cls.bank_journal = cls.company_data["default_journal_bank"]
        cls.bank_journal.outbound_payment_method_line_ids[:1].payment_account_id = (
            Account.create({
                "code": "OUTPAY",
                "name": "Outstanding Payments",
                "account_type": "asset_current",
                "reconcile": True,
            })
        )
        cls.goods = cls.env["product.product"].create({
            "name": "Stocked goods",
            "type": "consu",
            "is_storable": True,
            "purchase_method": "purchase",
        })

    def _order(self, **vals):
        return self.env["purchase.order"].create({
            "partner_id": self.partner_a.id,
            "order_line": [Command.create({
                "product_id": self.goods.id,
                "product_qty": 5,
                "price_unit": 100.0,
            })],
            **vals,
        })

    def _pay(self, order):
        self.env["purchase.advance.payment.wizard"].with_context(
            active_model="purchase.order", active_id=order.id,
        ).create({
            "journal_id": self.bank_journal.id,
            "payment_method_line_id":
                self.bank_journal.outbound_payment_method_line_ids[:1].id,
        }).action_create_payment()

    def test_paid_advance_creates_no_receipt(self):
        """Paying an advance confirms it; the goods are received once, on
        the parent purchase order."""
        parent = self._order()
        parent.button_confirm()
        self.assertEqual(len(parent.picking_ids), 1)
        advance = self._order(
            is_advance_invoice=True,
            advance_invoice_parent_order_id=parent.id,
        )
        self._pay(advance)
        self.assertEqual(advance.state, "purchase")
        self.assertFalse(advance.picking_ids)
        self.assertEqual(len(parent.picking_ids), 1)
        self.assertEqual(parent.picking_ids.move_ids.product_uom_qty, 5)

    def test_confirmed_advance_creates_no_receipt(self):
        """Confirming by hand, and raising a quantity afterwards, procure
        nothing either."""
        advance = self._order(is_advance_invoice=True)
        advance.button_confirm()
        self.assertEqual(advance.state, "purchase")
        self.assertFalse(advance.picking_ids)
        advance.order_line.product_qty = 8
        advance.order_line = [Command.create({
            "product_id": self.goods.id, "product_qty": 1, "price_unit": 10.0,
        })]
        self.assertFalse(advance.picking_ids)

    def test_ordinary_order_still_receives(self):
        order = self._order()
        order.button_confirm()
        self.assertEqual(order.picking_ids.move_ids.product_uom_qty, 5)
        order.order_line.product_qty = 8
        self.assertEqual(sum(order.picking_ids.move_ids.mapped("product_uom_qty")), 8)
