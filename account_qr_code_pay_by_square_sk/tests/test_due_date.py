# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import lzma
from datetime import date, timedelta
from unittest.mock import patch

from odoo import fields
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged

from odoo.addons.account_qr_code_pay_by_square_sk.models import res_bank

METHOD = "skpaybysquare_qr"


def decode(code):
    """PAY by square string → its tab-separated fields (CRC dropped)."""
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUV"
    bits = "".join(bin(alphabet.index(c))[2:].zfill(5) for c in code)
    raw = bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits) - 7, 8))
    length = int.from_bytes(raw[2:4], "little")
    data = lzma.LZMADecompressor(
        format=lzma.FORMAT_RAW,
        filters=[{"id": lzma.FILTER_LZMA1, "lc": 3, "lp": 0, "pb": 2,
                  "dict_size": 128 * 1024}],
    ).decompress(raw[4:], max_length=length)
    return data[4:].decode().split("\t")


@tagged("post_install", "-at_install")
class TestDueDate(AccountTestInvoicingCommon):
    """PaymentDueDate is the invoice's due date, not the day of printing."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.eur = cls.env.ref("base.EUR")
        cls.eur.active = True
        cls.bank = cls.env["res.partner.bank"].sudo().create({
            "acc_number": "SK3112000000198742637541",
            "partner_id": cls.company_data["company"].partner_id.id,
            "acc_holder_name": "Issuer",
        })

    def _due_field(self, **context):
        params = self.bank.with_context(**context)._get_qr_code_generation_params(
            METHOD, 10.0, self.eur, self.partner_a, "INV/1", "INV/1")
        return decode(params["value"])[5]

    def test_the_due_date_travels_into_the_code(self):
        due = fields.Date.today() + timedelta(days=14)
        self.assertEqual(self._due_field(qr_code_date_due=due),
                         due.strftime("%Y%m%d"))

    def test_an_overdue_invoice_is_dated_today(self):
        self.assertEqual(self._due_field(qr_code_date_due=date(2020, 1, 31)),
                         fields.Date.today().strftime("%Y%m%d"))

    def test_without_an_invoice_it_is_today(self):
        self.assertEqual(self._due_field(),
                         fields.Date.today().strftime("%Y%m%d"))

    def test_the_invoice_passes_its_due_date(self):
        due = fields.Date.today() + timedelta(days=30)
        invoice = self.init_invoice(
            "out_invoice", partner=self.partner_a, amounts=[100.0],
            currency=self.eur, taxes=self.env["account.tax"],
        )
        invoice.write({
            "invoice_date_due": due,
            "partner_bank_id": self.bank.id,
            "qr_code_method": METHOD,
        })
        invoice.company_id.qr_code = True
        seen = []
        real = res_bank.generate

        def spy(*args, **kwargs):
            seen.append(kwargs.get("date_due"))
            return real(*args, **kwargs)

        with patch.object(res_bank, "generate", spy):
            invoice._generate_qr_code()
        self.assertTrue(seen)
        self.assertEqual(set(seen), {due})
