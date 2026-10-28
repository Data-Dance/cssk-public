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

    def _add_line(self, order, **line_vals):
        vals = {
            "order_id": order.id,
            "partner_id": self.supplier.id,
            "partner_bank_id": self.supplier_bank.id,
            "currency_id": self.czk.id,
            "amount_currency": 100.0,
            "date": "2026-03-15",
            "communication": "FA 2026/0043",
        }
        vals.update(line_vals)
        self.env["account.payment.line"].sudo().create(vals)

    def test_lines_with_different_dates_are_refused(self):
        """ABO carries one due date per file. With the default execution date
        type (Due Date) lines are routinely dated differently, and the file
        used to execute them all on the first line's date without a word."""
        from odoo.exceptions import UserError
        order = self._order()
        self._add_line(order, date="2026-03-20")
        with self.assertRaisesRegex(UserError, "one due date"):
            order.generate_payment_file()

    def test_lines_sharing_a_date_export_it(self):
        order = self._order(date="2026-03-20")
        self._add_line(order, date="2026-03-20")
        text = order.generate_payment_file()[0].decode("cp1250")
        group_header = text.split("\r\n")[2]
        self.assertTrue(group_header.endswith(" 200326"), group_header)

    def test_zero_amount_line_is_refused(self):
        from odoo.exceptions import UserError
        # Ungrouped: grouped with the first line, a zero line now nets into it.
        self.mode.group_lines = False
        order = self._order()
        self._add_line(order, amount_currency=0.0)
        with self.assertRaisesRegex(UserError, "zero or negative"):
            order.generate_payment_file()

    # ------------------------------------------------------------------
    # credit notes grouped with their invoice
    # ------------------------------------------------------------------

    def _items(self, text):
        """The item records: everything between the group header and the
        group trailer."""
        lines = text.split("\r\n")
        start = next(i for i, line in enumerate(lines) if line.startswith("2 "))
        end = next(i for i, line in enumerate(lines) if line.startswith("3 +"))
        return lines[start + 1:end]

    def test_credit_note_grouped_with_its_invoice_is_one_net_item(self):
        """A credit note grouped with its invoice is one payment of the net
        amount, and the file must say so: one item per payment line put a
        negative item in the file, which every bank refuses."""
        order = self._order(amount_currency=1000.0, variable_symbol="20260042")
        self._add_line(order, amount_currency=-300.0, variable_symbol="20260007",
                       communication="DOB 2026/0007")
        items = self._items(order.generate_payment_file()[0].decode("cp1250"))
        self.assertEqual(len(items), 1, items)
        self.assertIn(" 70000 ", items[0])
        # the invoice's symbol: the credit note is deducted from it
        self.assertIn("20260042", items[0])
        self.assertNotIn("20260007", items[0])

    def test_invoices_sharing_a_symbol_keep_it_when_netted(self):
        """Two instalments of one invoice (one VS) and a credit note: the
        symbol the payable lines share survives the credit note's own."""
        order = self._order(amount_currency=600.0, variable_symbol="20260042")
        self._add_line(order, amount_currency=400.0, variable_symbol="20260042")
        self._add_line(order, amount_currency=-300.0, variable_symbol="20260007")
        items = self._items(order.generate_payment_file()[0].decode("cp1250"))
        self.assertEqual(len(items), 1, items)
        self.assertIn(" 70000 20260042 ", items[0])

    def test_grouped_invoices_keep_one_item_each(self):
        """Without a credit note nothing is netted: each invoice still travels
        under its own variable symbol."""
        order = self._order(amount_currency=1000.0, variable_symbol="20260042")
        self._add_line(order, amount_currency=500.0, variable_symbol="20260043")
        items = self._items(order.generate_payment_file()[0].decode("cp1250"))
        self.assertEqual(len(items), 2, items)
        self.assertIn("20260042", items[0])
        self.assertIn("20260043", items[1])

    def test_ungrouped_credit_note_is_still_refused(self):
        from odoo.exceptions import UserError
        self.mode.group_lines = False
        order = self._order(amount_currency=1000.0)
        self._add_line(order, amount_currency=-300.0)
        with self.assertRaisesRegex(UserError, "zero or negative"):
            order.generate_payment_file()

    def test_bill_and_credit_note_through_the_order_workflow(self):
        """End to end: a vendor bill and its credit note added to one order,
        confirmed (which groups them into one 700 payment), then exported."""
        self.czk.active = True
        self.mode.write({
            "payment_order_ok": True, "default_date_prefered": "now",
        })
        self.supplier.supplier_payment_mode_id = self.mode
        self.supplier_bank.sudo().allow_out_payment = True
        moves = self.env["account.move"]
        for move_type, amount in (("in_invoice", 1000.0), ("in_refund", 300.0)):
            moves |= self.env["account.move"].create({
                "move_type": move_type,
                "partner_id": self.supplier.id,
                "partner_bank_id": self.supplier_bank.id,
                "currency_id": self.czk.id,
                "invoice_date": "2026-03-01",
                "ref": "%s-1" % move_type,
                "payment_mode_id": self.mode.id,
                "invoice_line_ids": [Command.create({
                    "name": "Goods", "quantity": 1, "price_unit": amount,
                    "tax_ids": [Command.clear()],
                })],
            })
        moves.action_post()
        # sudo: the test user is not in Accounting / Payments
        moves.sudo().create_account_payment_line()
        order = moves.sudo().line_ids.payment_line_ids.order_id
        self.assertEqual(len(order), 1)
        self.assertEqual(
            sorted(order.payment_line_ids.mapped("amount_currency")),
            [-300.0, 1000.0])
        order.draft2open()
        self.assertEqual(order.payment_ids.mapped("amount"), [700.0])
        items = self._items(order.generate_payment_file()[0].decode("cp1250"))
        self.assertEqual(len(items), 1, items)
        self.assertIn(" 70000 ", items[0])
