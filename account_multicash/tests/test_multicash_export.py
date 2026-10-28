# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestMultiCashExport(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.bank = cls.env["res.bank"].sudo().create(
            {"name": "KB", "bic": "KOMBCZPP"})
        cls.company_bank = cls.env["res.partner.bank"].sudo().create({
            "acc_number": "CZ6508000000192000145399",
            "partner_id": cls.company.partner_id.id,
            "bank_id": cls.bank.id, "company_id": cls.company.id,
        })
        cls.journal = cls.env["account.journal"].sudo().create({
            "name": "MC Bank", "type": "bank", "code": "MCBK",
            "company_id": cls.company.id,
            "bank_account_id": cls.company_bank.id,
        })
        cls.supplier = cls.env["res.partner"].create({"name": "Dodavatel"})
        cls.supplier_bank = cls.env["res.partner.bank"].sudo().create({
            "acc_number": "CZ5530000000000019012333",
            "partner_id": cls.supplier.id, "bank_id": cls.bank.id,
        })
        cls.foreign = cls.env["res.partner"].create({"name": "Lieferant GmbH"})
        cls.foreign_bank = cls.env["res.partner.bank"].sudo().create({
            "acc_number": "DE89370400440532013000",
            "partner_id": cls.foreign.id, "bank_id": cls.bank.id,
        })
        cls.czk = cls.env.ref("base.CZK")
        cls.eur = cls.env.ref("base.EUR")

    def _mode(self, code, payment_type="outbound"):
        method = self.env["account.payment.method"].search(
            [("code", "=", code), ("payment_type", "=", payment_type)], limit=1)
        return self.env["account.payment.mode"].sudo().create({
            "name": code, "company_id": self.company.id,
            "payment_method_id": method.id,
            "bank_account_link": "fixed", "fixed_journal_id": self.journal.id,
        })

    def _order(self, mode, partner, partner_bank, currency, amount=1234.50):
        order = self.env["account.payment.order"].sudo().create({
            "payment_mode_id": mode.id, "payment_type": mode.payment_type,
            "journal_id": self.journal.id,
        })
        self.env["account.payment.line"].sudo().create({
            "order_id": order.id, "partner_id": partner.id,
            "partner_bank_id": partner_bank.id, "currency_id": currency.id,
            "amount_currency": amount, "date": "2026-03-15",
            "communication": "FA 2026/0042", "variable_symbol": "20260042",
        })
        return order.sudo()

    def test_cfd_domestic(self):
        mode = self._mode("multicash_cfd")
        order = self._order(mode, self.supplier, self.supplier_bank, self.czk)
        text, fn = order.generate_payment_file()
        self.assertTrue(fn.startswith("CFD-") and fn.endswith(".cfd"))
        body = text.decode("cp1250")
        self.assertIn("KC:", body)          # CFD amount tag
        self.assertIn("20260042", body)     # VS

    def test_cfa_foreign_needs_bic(self):
        mode = self._mode("multicash_cfa")
        order = self._order(mode, self.foreign, self.foreign_bank, self.eur)
        text, fn = order.generate_payment_file()
        self.assertTrue(fn.endswith(".cfa"))
        self.assertTrue(text)

    def test_cfa_without_bic_raises(self):
        from odoo.exceptions import UserError
        nobic_bank = self.env["res.bank"].sudo().create({"name": "NoBIC"})
        self.journal.bank_account_id.bank_id = nobic_bank
        mode = self._mode("multicash_cfa")
        order = self._order(mode, self.foreign, self.foreign_bank, self.eur)
        with self.assertRaises(UserError):
            order.generate_payment_file()

    def _add_line(self, order, partner, partner_bank, currency, **vals):
        line_vals = {
            "order_id": order.id, "partner_id": partner.id,
            "partner_bank_id": partner_bank.id, "currency_id": currency.id,
            "amount_currency": 100.0, "date": "2026-03-15",
            "communication": "FA 2026/0043",
        }
        line_vals.update(vals)
        self.env["account.payment.line"].sudo().create(line_vals)

    def test_mt101_lines_with_different_dates_are_refused(self):
        """MT101 has one :30: execution date for the whole message; the file
        used to take the first line's date for every payment."""
        from odoo.exceptions import UserError
        mode = self._mode("multicash_mt101")
        order = self._order(mode, self.foreign, self.foreign_bank, self.eur)
        self._add_line(order, self.foreign, self.foreign_bank, self.eur,
                       date="2026-03-20")
        with self.assertRaisesRegex(UserError, "one execution date"):
            order.generate_payment_file()

    def test_cfd_lines_keep_their_own_dates(self):
        mode = self._mode("multicash_cfd")
        order = self._order(mode, self.supplier, self.supplier_bank, self.czk)
        self._add_line(order, self.supplier, self.supplier_bank, self.czk,
                       date="2026-03-20")
        body = order.generate_payment_file()[0].decode("cp852")
        self.assertIn("HD:11 260315", body)
        self.assertIn("HD:11 260320", body)

    def test_zero_amount_line_is_refused(self):
        from odoo.exceptions import UserError
        mode = self._mode("multicash_cfd")
        # Ungrouped: grouped with the first line, a zero line now nets into it.
        mode.group_lines = False
        order = self._order(mode, self.supplier, self.supplier_bank, self.czk)
        self._add_line(order, self.supplier, self.supplier_bank, self.czk,
                       amount_currency=0.0)
        with self.assertRaisesRegex(UserError, "zero or negative"):
            order.generate_payment_file()

    def test_cfa_priority_and_charge_bearer_come_from_the_line(self):
        """They used to be read from fields no Community module defines, so
        every CFA went out as normal priority with shared charges."""
        mode = self._mode("multicash_cfa")
        order = self._order(mode, self.foreign, self.foreign_bank, self.eur)
        body = order.generate_payment_file()[0].decode("cp852")
        self.assertIn("N1}{4:", body)
        self.assertIn(":71A:BN1", body)
        order.payment_line_ids.write({
            "iso20022_priority": "URGP", "iso20022_charge_bearer": "DEBT",
        })
        body = order.generate_payment_file()[0].decode("cp852")
        self.assertIn("S1}{4:", body)
        self.assertIn(":71A:OUR", body)

    def test_credit_note_grouped_with_its_invoice_is_one_net_item(self):
        """One payment of the net amount, not a negative item every bank
        refuses."""
        mode = self._mode("multicash_cfd")
        order = self._order(mode, self.supplier, self.supplier_bank, self.czk,
                            amount=1000.0)
        self._add_line(order, self.supplier, self.supplier_bank, self.czk,
                       amount_currency=-300.0, variable_symbol="20260007")
        body = order.generate_payment_file()[0].decode("cp852")
        self.assertEqual(body.count("HD:11 "), 1, body)
        self.assertIn("ZK:20260042", body)
        self.assertNotIn("20260007", body)

    def test_mt101_credit_note_nets_too(self):
        mode = self._mode("multicash_mt101")
        order = self._order(mode, self.foreign, self.foreign_bank, self.eur,
                            amount=1000.0)
        self._add_line(order, self.foreign, self.foreign_bank, self.eur,
                       amount_currency=-250.0)
        body = order.generate_payment_file()[0].decode("cp852")
        self.assertIn("EUR750,", body)
        self.assertNotIn("EUR1000,", body)
