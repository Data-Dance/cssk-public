# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).

import io

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged

from openpyxl import load_workbook


@tagged("post_install", "-at_install")
class TestAdvanceSaldoXlsx(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids |= (
            cls.env.ref("purchase.group_purchase_manager")
            + cls.env.ref("sales_team.group_sale_manager")
            + cls.env.ref("account.group_account_user")
        )
        company = cls.env.company
        Account = cls.env["account.account"]
        company.advance_paid_clearing_account_id = Account.create({
            "code": "314001", "name": "Paid advances clearing",
            "account_type": "liability_payable", "reconcile": True,
        })
        company.advance_paid_account_id = Account.create({
            "code": "314000", "name": "Paid advances",
            "account_type": "asset_current",
        })
        company.advance_purchase_journal_id = cls.env["account.journal"].create(
            {"name": "PDADV", "code": "PDADV", "type": "purchase"}
        )
        cls.service = cls.env["product.product"].create({
            "name": "Advance service", "type": "service",
        })

    def _paid_purchase_advance(self, price=500.0):
        order = self.env["purchase.order"].create({
            "partner_id": self.partner_a.id,
            "is_advance_invoice": True,
            "order_line": [
                Command.create({
                    "product_id": self.service.id,
                    "product_qty": 1,
                    "price_unit": price,
                    "tax_ids": [Command.clear()],
                })
            ],
        })
        bank_journal = self.company_data["default_journal_bank"]
        method_line = bank_journal.outbound_payment_method_line_ids[:1]
        if not method_line.payment_account_id:
            method_line.payment_account_id = self.env["account.account"].create({
                "code": "OUTPAY", "name": "Outstanding Payments",
                "account_type": "asset_current", "reconcile": True,
            })
        wizard = self.env["purchase.advance.payment.wizard"].with_context(
            active_model="purchase.order", active_id=order.id
        ).create({
            "journal_id": bank_journal.id,
            "payment_method_line_id": method_line.id,
        })
        wizard.action_create_payment()
        return order

    def _render(self, include_settled=False):
        wizard = self.env["advance.saldo.xlsx.wizard"].create({
            "include_settled": include_settled,
        })
        report = self.env.ref(
            "advance_invoice_saldo_xlsx.report_advance_saldo_xlsx"
        )
        content, report_type = self.env["ir.actions.report"]._render_xlsx(
            report.report_name, wizard.ids, data=None
        )
        self.assertEqual(report_type, "xlsx")
        return load_workbook(io.BytesIO(content), read_only=True)

    def test_open_purchase_advance_listed(self):
        order = self._paid_purchase_advance(price=500.0)
        workbook = self._render()
        sheet = workbook["Received advances"]
        rows = list(sheet.iter_rows(values_only=True))
        self.assertGreaterEqual(len(rows), 2)
        row = next(r for r in rows[1:] if r[0] == order.name)
        self.assertEqual(row[4], 500.0)   # total
        self.assertEqual(row[5], 500.0)   # paid
        self.assertEqual(row[9], 500.0)   # open = paid - deducted
        self.assertIn("Issued advances", workbook.sheetnames)

    def test_unpaid_advance_listed_settled_hidden(self):
        order = self.env["purchase.order"].create({
            "partner_id": self.partner_a.id,
            "is_advance_invoice": True,
            "order_line": [
                Command.create({
                    "product_id": self.service.id,
                    "product_qty": 1,
                    "price_unit": 100.0,
                    "tax_ids": [Command.clear()],
                })
            ],
        })
        workbook = self._render()
        sheet = workbook["Received advances"]
        names = [r[0] for r in sheet.iter_rows(values_only=True)][1:]
        # unpaid advance still shows (payment status none)
        self.assertIn(order.name, names)
