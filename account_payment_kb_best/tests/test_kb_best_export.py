# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestKbBestExport(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.czk = cls.env.ref("base.CZK")
        cls.czk.active = True
        cls.eur = cls.env.ref("base.EUR")
        cls.eur.active = True
        cls.company_bank = cls.env["res.partner.bank"].sudo().create({
            "acc_number": "CZ5901000900930669910217",
            "partner_id": cls.company.partner_id.id,
            "company_id": cls.company.id,
        })
        cls.journal = cls.env["account.journal"].sudo().create({
            "name": "KB", "type": "bank", "code": "KBBK",
            "company_id": cls.company.id,
            "bank_account_id": cls.company_bank.id,
            "currency_id": cls.czk.id,
        })
        cls.supplier = cls.env["res.partner"].create({"name": "Dodavatel s.r.o."})
        cls.supplier_bank = cls.env["res.partner.bank"].sudo().create({
            "acc_number": "19012333/0300",
            "partner_id": cls.supplier.id,
        })
        germany = cls.env.ref("base.de")
        cls.foreign = cls.env["res.partner"].create({
            "name": "Lieferant GmbH", "street": "Hauptstrasse 12",
            "city": "Berlin", "zip": "10115", "country_id": germany.id,
        })
        cls.foreign_bank = cls.env["res.partner.bank"].sudo().create({
            "acc_number": "DE89370400440532013000",
            "partner_id": cls.foreign.id,
            "bank_id": cls.env["res.bank"].create({
                "name": "Commerzbank", "bic": "COBADEFFXXX",
                "country": germany.id}).id,
        })

    def _mode(self, xmlid):
        method = self.env.ref("account_payment_kb_best." + xmlid)
        return self.env["account.payment.mode"].create({
            "name": method.name, "company_id": self.company.id,
            "payment_method_id": method.id,
            "bank_account_link": "fixed", "fixed_journal_id": self.journal.id,
        })

    def _order(self, xmlid, payment_type="outbound", **line_vals):
        order = self.env["account.payment.order"].sudo().create({
            "payment_mode_id": self._mode(xmlid).id,
            "payment_type": payment_type,
            "journal_id": self.journal.id,
        })
        vals = {
            "order_id": order.id,
            "partner_id": self.supplier.id,
            "partner_bank_id": self.supplier_bank.id,
            "currency_id": self.czk.id,
            "amount_currency": 1234.50,
            "communication": "FA 2026/0042",
        }
        vals.update(line_vals)
        self.env["account.payment.line"].sudo().create(vals)
        return order.sudo()

    def _records(self, data):
        return data.decode("cp1250")[:-2].split("\r\n")

    def test_domestic_transfer(self):
        order = self._order("account_payment_method_kb_best_domestic_out",
                            variable_symbol="20260042", constant_symbol="0308")
        data, filename = order.generate_payment_file()
        self.assertTrue(filename.startswith("BEST-DP-KBBK-"))
        self.assertTrue(filename.endswith(".ikm"))
        header, payment, trailer = self._records(data)
        self.assertEqual((header[:2], payment[:2], trailer[:2]), ("HI", "01", "TI"))
        self.assertEqual(len(payment), 351)
        self.assertEqual(payment[23:26], "CZK")
        self.assertEqual(payment[26:41], "000000000123450")
        self.assertEqual(payment[41], "0")
        self.assertEqual(payment[46:56], "0000000308")
        self.assertEqual(payment[199:219], "0100" + "0900930669910217")
        self.assertEqual(payment[272:292], "0300" + "0000000019012333")
        self.assertEqual(payment[292:302], "0020260042")
        # Sekv_No is the payment line's id in base 36
        line = order.payment_line_ids
        self.assertEqual(payment[2:7], _base36(line.id))

    def test_vs_falls_back_to_communication(self):
        order = self._order("account_payment_method_kb_best_domestic_out",
                            communication="platba VS:778899")
        data, _name = order.generate_payment_file()
        self.assertEqual(self._records(data)[1][292:302], "0000778899")

    def test_direct_debit(self):
        order = self._order("account_payment_method_kb_best_domestic_in",
                            payment_type="inbound")
        data, _name = order.generate_payment_file()
        self.assertEqual(self._records(data)[1][41], "1")

    def test_foreign_sepa(self):
        order = self._order("account_payment_method_kb_best_foreign",
                            partner_id=self.foreign.id,
                            partner_bank_id=self.foreign_bank.id,
                            currency_id=self.eur.id, amount_currency=41.0,
                            communication="Rechnung 77")
        data, filename = order.generate_payment_file()
        self.assertTrue(filename.startswith("BEST-ZP-"))
        records = self._records(data)
        self.assertEqual([r[:2] for r in records], ["HI", "02", "03", "TI"])
        payment = records[1]
        self.assertEqual(len(payment), 882)
        self.assertEqual(payment[29:32], "EUR")
        self.assertEqual(payment[47:50], "SLV")
        self.assertEqual(payment[879], "Y")
        self.assertEqual(payment[140:143], "CZK")  # the KB account's currency
        self.assertEqual(payment[564:598].strip(), "DE89370400440532013000")

    def test_not_a_kb_account(self):
        self.company_bank.acc_number = "CZ6508000000192000145399"
        order = self._order("account_payment_method_kb_best_domestic_out")
        with self.assertRaisesRegex(UserError, "not a KB account"):
            order.generate_payment_file()


def _base36(number):
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    out = ""
    number %= 36 ** 5
    while True:
        number, rest = divmod(number, 36)
        out = digits[rest] + out
        if not number:
            return out.rjust(5, "0")
