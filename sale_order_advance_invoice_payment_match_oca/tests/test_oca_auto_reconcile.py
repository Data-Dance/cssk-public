from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestOcaAutoReconcileAdvance(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids |= cls.env.ref("sales_team.group_sale_manager")
        company = cls.env.company
        Account = cls.env["account.account"]
        cls.clearing = Account.create({
            "code": "324001",
            "name": "Advance clearing",
            "account_type": "asset_receivable",
            "reconcile": True,
        })
        company.advance_received_account_id = cls.clearing
        company.advance_invoice_journal_id = cls.env["account.journal"].create(
            {"name": "Advance Tax Documents", "code": "TDADV", "type": "general"}
        )
        company.advance_invoice_auto_match_statement = True
        cls.bank_journal = cls.company_data["default_journal_bank"]
        outstanding = Account.create({
            "code": "OUTREC",
            "name": "Outstanding Receipts",
            "account_type": "asset_current",
            "reconcile": True,
        })
        cls.bank_journal.inbound_payment_method_line_ids[
            :1
        ].payment_account_id = outstanding
        cls.env["payment.provider"].create({
            "name": "Offline",
            "code": "none",
            "company_id": company.id,
        })

    def test_oca_auto_reconcile_pays_advance(self):
        advance = self.env["sale.order"].create({
            "partner_id": self.partner_a.id,
            "is_advance_invoice": True,
            "order_line": [
                Command.create({
                    "product_id": self.product_a.id,
                    "product_uom_qty": 1,
                    "price_unit": 500.0,
                })
            ],
        })
        line = self.env["account.bank.statement.line"].create({
            "journal_id": self.bank_journal.id,
            "date": fields.Date.from_string("2026-07-10"),
            "payment_ref": f"payment {advance.name}",
            "amount": advance.amount_total,
        })
        line._do_auto_reconcile()
        self.assertTrue(line.is_reconciled)
        self.assertEqual(advance.advance_invoice_payment_status, "paid_fully")
