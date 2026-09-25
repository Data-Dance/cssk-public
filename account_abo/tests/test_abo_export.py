# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestAboExport(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        # company (orderer) bank account + bank journal
        cls.bank = cls.env["res.bank"].sudo().create({"name": "KB", "bic": "KOMBCZPP"})
        cls.company_bank = cls.env["res.partner.bank"].sudo().create({
            "acc_number": "CZ6508000000192000145399",
            "partner_id": cls.company.partner_id.id,
            "bank_id": cls.bank.id,
            "company_id": cls.company.id,
        })
        cls.journal = cls.env["account.journal"].sudo().create({
            "name": "ABO Bank", "type": "bank", "code": "ABOBK",
            "company_id": cls.company.id,
            "bank_account_id": cls.company_bank.id,
        })
        cls.abo_method = cls.env["account.payment.method"].search(
            [("code", "=", "abo")], limit=1)
        cls.mode = cls.env["account.payment.mode"].create({
            "name": "ABO", "company_id": cls.company.id,
            "payment_method_id": cls.abo_method.id,
            "bank_account_link": "fixed", "fixed_journal_id": cls.journal.id,
        })
        # supplier with a CZ bank account
        cls.supplier = cls.env["res.partner"].create({"name": "Dodavatel s.r.o."})
        cls.supplier_bank = cls.env["res.partner.bank"].sudo().create({
            "acc_number": "CZ5530000000000019012333",
            "partner_id": cls.supplier.id,
            "bank_id": cls.bank.id,
        })
        cls.czk = cls.env.ref("base.CZK")

    def _order(self, **line_vals):
        order = self.env["account.payment.order"].sudo().create({
            "payment_mode_id": self.mode.id,
            "payment_type": "outbound",
            "journal_id": self.journal.id,
        })
        vals = {
            "order_id": order.id,
            "partner_id": self.supplier.id,
            "partner_bank_id": self.supplier_bank.id,
            "currency_id": self.czk.id,
            "amount_currency": 1234.50,
            "date": "2026-03-15",
            "communication": "FA 2026/0042",
        }
        vals.update(line_vals)
        self.env["account.payment.line"].sudo().create(vals)
        return order.sudo()

    def test_generate_payment_file_dispatch_and_content(self):
        order = self._order(variable_symbol="20260042", constant_symbol="0308")
        file_bytes, filename = order.generate_payment_file()
        self.assertTrue(filename.startswith("ABO-") and filename.endswith(".abo"))
        text = file_bytes.decode("cp1250")
        # header + group + item + trailers
        self.assertTrue(text.startswith("UHL1"))
        self.assertIn("1 1501 ", text)          # accounting file header
        self.assertIn("\r\n2 ", text)            # group header
        # amount in haléř (1234.50 -> 123450) and the explicit VS
        self.assertIn("123450", text)
        self.assertIn("20260042", text)          # VS
        self.assertTrue(text.rstrip().endswith("5 +"))

    def test_vs_falls_back_to_communication(self):
        # no explicit VS -> parsed from "VS:" token in communication
        order = self._order(communication="platba VS:778899", variable_symbol=False)
        text, _fn = order.generate_payment_file()
        self.assertIn("778899", text.decode("cp1250"))

    def test_non_czk_is_rejected(self):
        from odoo.exceptions import UserError
        order = self._order(currency_id=self.env.ref("base.EUR").id)
        with self.assertRaises(UserError):
            order.generate_payment_file()
