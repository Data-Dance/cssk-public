# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""VAT declared in a later period leaves 343 until the declaring period."""

from datetime import timedelta

from odoo import fields
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestVatDeferral(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.deferral = cls.env["account.account"].create({
            "name": "VAT declared later", "code": "343900",
            "account_type": "asset_current",
            "company_ids": [(6, 0, cls.company.ids)],
        })
        cls.company.cssk_vat_deferral_account_id = cls.deferral
        cls.tax = cls.tax_purchase_a  # 15 % in the test chart

    def _bill(self, date="2025-06-15", declared="2025-08-10"):
        bill = self.env["account.move"].create({
            "move_type": "in_invoice", "partner_id": self.partner_a.id,
            "invoice_date": date, "date": date,
            "cssk_vat_deduction_date": declared,
            "invoice_line_ids": [(0, 0, {
                "name": "x", "quantity": 1, "price_unit": 1000.0,
                "tax_ids": [(6, 0, self.tax.ids)]})],
        })
        bill.action_post()
        return bill

    def _balance(self, account, date_to):
        lines = self.env["account.move.line"].search([
            ("account_id", "=", account.id), ("parent_state", "=", "posted"),
            ("date", "<=", date_to), ("company_id", "=", self.company.id)])
        return sum(lines.mapped("balance"))

    def test_the_tax_waits_on_the_deferral_account_until_declared(self):
        bill = self._bill()
        tax_line = bill.line_ids.filtered("tax_line_id")
        tax_account = tax_line.account_id
        amount = tax_line.balance
        self.assertTrue(amount)
        out, back = bill.cssk_vat_deferral_move_ids.sorted("date")
        self.assertEqual(out.date, fields.Date.to_date("2025-06-15"))
        self.assertEqual(back.date, fields.Date.to_date("2025-08-10"))
        self.assertEqual((out.state, back.state), ("posted", "posted"))
        # June: booked but not declared — the VAT account nets to nothing.
        self.assertAlmostEqual(self._balance(tax_account, "2025-06-30"), 0.0)
        self.assertAlmostEqual(self._balance(self.deferral, "2025-06-30"), amount)
        # August: declared — back on the VAT account.
        self.assertAlmostEqual(self._balance(tax_account, "2025-08-31"), amount)
        self.assertAlmostEqual(self._balance(self.deferral, "2025-08-31"), 0.0)
        # The entries carry no taxes and no tags: no return reads them.
        entry_lines = (out | back).line_ids
        self.assertFalse(entry_lines.tax_ids | entry_lines.tax_line_id)
        self.assertFalse(entry_lines.tax_tag_ids)

    def test_nothing_happens_within_the_booking_month(self):
        bill = self._bill(declared="2025-06-28")
        self.assertFalse(bill.cssk_vat_deferral_move_ids)

    def test_nothing_happens_when_the_setting_is_off(self):
        self.company.cssk_vat_deferral_account_id = False
        self.assertFalse(self._bill().cssk_vat_deferral_move_ids)

    def test_a_future_declaration_posts_itself_on_its_date(self):
        today = fields.Date.context_today(self.env.user)
        later = today + timedelta(days=62)
        bill = self._bill(date=today.isoformat(), declared=later.isoformat())
        back = bill.cssk_vat_deferral_move_ids.filtered(lambda m: m.date == later)
        self.assertEqual(back.state, "draft")
        self.assertEqual(back.auto_post, "at_date")

    def test_reset_to_draft_withdraws_and_reposting_rebuilds(self):
        bill = self._bill()
        first = bill.cssk_vat_deferral_move_ids
        bill.button_draft()
        self.assertEqual(set(first.mapped("state")), {"cancel"})
        bill.action_post()
        live = bill.cssk_vat_deferral_move_ids.filtered(lambda m: m.state != "cancel")
        self.assertEqual(len(live), 2)

    def test_changing_the_declaration_date_moves_the_back_entry(self):
        bill = self._bill()
        bill.cssk_vat_deduction_date = "2025-09-05"
        live = bill.cssk_vat_deferral_move_ids.filtered(lambda m: m.state != "cancel")
        self.assertEqual(
            max(live.mapped("date")), fields.Date.to_date("2025-09-05"))

    def test_rewriting_the_same_date_changes_nothing(self):
        bill = self._bill()
        entries = bill.cssk_vat_deferral_move_ids
        bill.cssk_vat_deduction_date = "2025-08-10"
        self.assertEqual(bill.cssk_vat_deferral_move_ids, entries)
        self.assertEqual(set(entries.mapped("state")), {"posted"})

    def test_cancelling_the_document_withdraws_its_entries(self):
        bill = self._bill()
        entries = bill.cssk_vat_deferral_move_ids
        bill.button_draft()
        bill.button_cancel()
        self.assertEqual(set(entries.mapped("state")), {"cancel"})
