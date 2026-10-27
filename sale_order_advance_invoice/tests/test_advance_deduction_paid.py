# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""An advance is deducted for what was received on it, not for its face value.

The final invoice used to deduct the whole advance - its full net with a tax
document, its full gross without one - as soon as anything at all had been
paid. A half-paid advance then wiped out half of the supply that nobody had
paid for. The deduction is now the net the posted tax documents declared, at
their own taxes, plus whatever else was received gross and without VAT.
"""

from datetime import date

from odoo import Command
from odoo.tests import tagged

from ..tools import advance_tax_doc_deadline
from .common import AdvanceInvoiceCommon


@tagged("post_install", "-at_install")
class TestAdvanceDeductionPaid(AdvanceInvoiceCommon):

    def _itemised_confirmed(self, order):
        advance = self._advance(order, include_items=True)
        advance.action_confirm()
        return advance

    def _document(self, advance):
        advance.action_create_invoice_direct_for_advance()
        advance.invoice_ids.filtered(lambda m: m.state == "draft").action_post()

    def _deductions(self, invoice):
        return invoice.invoice_line_ids.filtered(lambda line: line.price_subtotal < 0)

    # === ON THE ORDER'S FINAL INVOICE ===#

    def test_a_half_paid_documented_advance_deducts_half(self):
        self._configure_advance_accounts()
        order = self._order()  # 2980 gross: 2000 @ 21 % + 500 @ 12 %
        advance = self._itemised_confirmed(order)
        self._pay(advance, 1490.0)
        self._document(advance)

        invoice = order._create_invoices(final=True)
        deductions = self._deductions(invoice)
        self.assertAlmostEqual(
            sum(deductions.mapped("price_subtotal")), -1250.0, places=2,
            msg="the whole advance was deducted although only half was paid",
        )
        self.assertAlmostEqual(invoice.amount_total, 1490.0, places=2)
        self.assertEqual(
            {tuple(line.tax_ids.mapped("amount")): line.price_subtotal for line in deductions},
            {(21.0,): -1000.0, (12.0,): -250.0},
        )

    def test_a_half_paid_advance_without_a_tax_document_deducts_what_was_paid(self):
        self._configure_advance_accounts()
        order = self._order()
        advance = self._itemised_confirmed(order)
        self._pay(advance, 1490.0)

        invoice = order._create_invoices(final=True)
        deductions = self._deductions(invoice)
        self.assertEqual(len(deductions), 1)
        self.assertFalse(deductions.tax_ids)
        self.assertAlmostEqual(deductions.price_subtotal, -1490.0, places=2)
        self.assertAlmostEqual(invoice.amount_total, 1490.0, places=2)

    def test_a_payment_no_tax_document_covers_is_deducted_gross(self):
        """Paid in full, but only the first half has a tax document yet."""
        self._configure_advance_accounts()
        order = self._order()
        advance = self._itemised_confirmed(order)
        self._pay(advance, 1490.0)
        self._document(advance)
        self._pay(advance, 1490.0)

        invoice = order._create_invoices(final=True)
        deductions = self._deductions(invoice)
        self.assertEqual(len(deductions), 3, "two documented rates + one undocumented part")
        undocumented = deductions.filtered(lambda line: not line.tax_ids)
        self.assertAlmostEqual(undocumented.price_subtotal, -1490.0, places=2)
        self.assertNotEqual(
            undocumented.account_id, self.env.company.advance_tax_doc_account_id,
            "an undocumented payment has no net advance on the tax-document account",
        )
        self.assertAlmostEqual(invoice.amount_total, 0.0, places=2)

    def test_the_tax_document_s_own_rates_are_given_back(self):
        """A draft tax document declares nothing; the deduction follows posted ones."""
        self._configure_advance_accounts()
        order = self._order()
        advance = self._itemised_confirmed(order)
        self._pay(advance)
        advance.action_create_invoice_direct_for_advance()  # left in draft

        invoice = order._create_invoices(final=True)
        deductions = self._deductions(invoice)
        self.assertEqual(len(deductions), 1)
        self.assertFalse(deductions.tax_ids)
        self.assertAlmostEqual(deductions.price_subtotal, -2980.0, places=2)

    # === ON A STANDALONE ADVANCE, VIA THE LINK WIZARD ===#

    def _standalone(self):
        advance = self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "is_advance_invoice": True,
            "order_line": [
                Command.create({
                    "product_id": self.printer.id, "product_uom_qty": 1,
                    "price_unit": 1000.0,
                    "tax_ids": [Command.set(self.tax_standard.ids)],
                }),
                Command.create({
                    "product_id": self.filament.id, "product_uom_qty": 5,
                    "price_unit": 100.0,
                    "tax_ids": [Command.set(self.tax_reduced.ids)],
                }),
            ],
        })
        advance.action_confirm()
        return advance  # 1210 + 560 = 1770 gross

    def _final_invoice(self):
        return self.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": self.partner.id,
            "invoice_line_ids": [
                Command.create({
                    "product_id": self.printer.id, "quantity": 1, "price_unit": 1000.0,
                    "tax_ids": [Command.set(self.tax_standard.ids)],
                }),
                Command.create({
                    "product_id": self.filament.id, "quantity": 5, "price_unit": 100.0,
                    "tax_ids": [Command.set(self.tax_reduced.ids)],
                }),
            ],
        })

    def _wizard(self, move):
        return self.env["account.move.link.advance.invoice.wizard"].with_context(
            active_model="account.move", active_id=move.id,
        ).create({"move_id": move.id})

    def test_a_documented_standalone_advance_can_be_linked(self):
        """Its tax document used to count as 'linked to another invoice'."""
        self._configure_advance_accounts()
        advance = self._standalone()
        self._pay(advance)
        self._document(advance)
        move = self._final_invoice()
        wizard = self._wizard(move)
        self.assertIn(advance, wizard.available_advance_invoice_ids)

    def test_every_line_and_rate_of_a_standalone_advance_is_deducted(self):
        self._configure_advance_accounts()
        advance = self._standalone()
        self._pay(advance)
        self._document(advance)
        move = self._final_invoice()
        wizard = self._wizard(move)
        wizard.advance_invoice_ids = advance
        wizard.action_link_advance_invoices()
        deductions = self._deductions(move)
        self.assertEqual(
            {tuple(line.tax_ids.mapped("amount")): line.price_subtotal for line in deductions},
            {(21.0,): -1000.0, (12.0,): -500.0},
        )
        self.assertAlmostEqual(move.amount_total, 0.0, places=2)
        self.assertEqual(
            deductions.account_id, self.env.company.advance_tax_doc_account_id,
        )

    def test_a_draft_tax_document_is_not_a_tax_document(self):
        self._configure_advance_accounts()
        advance = self._standalone()
        self._pay(advance)
        advance.action_create_invoice_direct_for_advance()  # left in draft
        move = self._final_invoice()
        wizard = self._wizard(move)
        wizard.advance_invoice_ids = advance
        wizard.action_link_advance_invoices()
        deductions = self._deductions(move)
        self.assertEqual(len(deductions), 1)
        self.assertFalse(deductions.tax_ids, "no VAT is given back that was never declared")
        self.assertAlmostEqual(deductions.price_subtotal, -1770.0, places=2)

    def test_an_unpaid_standalone_advance_is_not_offered(self):
        self._configure_advance_accounts()
        advance = self._standalone()
        move = self._final_invoice()
        self.assertNotIn(advance, self._wizard(move).available_advance_invoice_ids)

    # === THE TAX DOCUMENT DEADLINE ===#

    def _company_in(self, code):
        company = self.env.company
        country = self.env.ref("base.%s" % code.lower())
        company.country_id = country
        company.account_fiscal_country_id = country
        return company

    def test_czech_deadline_is_fifteen_days_without_a_month_cap(self):
        company = self._company_in("CZ")
        # § 28 odst. 8: paid on the 25th, due on the 9th of the next month.
        self.assertEqual(
            advance_tax_doc_deadline(company, date(2026, 3, 25)), date(2026, 4, 9))
        self.assertEqual(
            advance_tax_doc_deadline(company, date(2026, 3, 2)), date(2026, 3, 17))

    def test_slovak_deadline_is_the_later_of_fifteen_days_and_month_end(self):
        company = self._company_in("SK")
        # § 73 ods. 1 písm. b): early in the month the month end is later ...
        self.assertEqual(
            advance_tax_doc_deadline(company, date(2026, 3, 2)), date(2026, 3, 31))
        # ... late in the month the 15 days are.
        self.assertEqual(
            advance_tax_doc_deadline(company, date(2026, 3, 25)), date(2026, 4, 9))
        # Before 2016 the month-end alternative did not exist.
        self.assertEqual(
            advance_tax_doc_deadline(company, date(2015, 3, 2)), date(2015, 3, 17))

    def test_the_advance_list_shows_the_statutory_deadline(self):
        self._company_in("SK")
        self._configure_advance_accounts()
        advance = self._itemised_confirmed(self._order())
        self._pay(advance)
        paid = advance.advance_invoice_paid_date
        self.assertEqual(
            advance.advance_invoice_accounting_date_due,
            advance_tax_doc_deadline(advance.company_id, paid),
        )
