# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The signed line amounts keep Odoo's number and currency formatting."""

import re

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestReportSigned(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.ref("base.lang_en").write({"grouping": "[3,0]", "thousands_sep": ","})
        cls.currency = cls.env.company.currency_id

    def _cells(self, move):
        html = self.env["ir.actions.report"]._render_qweb_html(
            "account.report_invoice", move.ids)[0].decode()
        cells = {}
        for name in ("td_price_unit", "td_subtotal"):
            match = re.search(r'<td[^>]*name="%s"[^>]*>(.*?)</td>' % name,
                              html, re.S)
            self.assertTrue(match, "%s not rendered" % name)
            cells[name] = re.sub(r"<[^>]+>|\s+", " ", match.group(1)) \
                .replace("\xa0", " ").replace("\ufeff", "").strip()
        return cells

    def _move(self, move_type):
        return self.init_invoice(move_type, amounts=[1500.0], post=True)

    def test_invoice_line_amounts_are_formatted(self):
        cells = self._cells(self._move("out_invoice"))
        self.assertIn("1,500.00", cells["td_price_unit"])
        self.assertIn("1,500.00", cells["td_subtotal"])
        self.assertIn(self.currency.symbol, cells["td_subtotal"],
                      "the line subtotal is a monetary amount")
        self.assertNotIn("1500.0", cells["td_subtotal"])

    def test_credit_note_line_amounts_are_signed_and_formatted(self):
        cells = self._cells(self._move("out_refund"))
        self.assertIn("-1,500.00", cells["td_price_unit"])
        self.assertIn("-1,500.00", cells["td_subtotal"])
        self.assertIn(self.currency.symbol, cells["td_subtotal"])
