# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""A foreign-currency advance is deducted at the rate it was taxed at.

The tax document for a received advance (daňový doklad k přijaté platbě)
declares its VAT in the company currency at the rate of ITS date. The final
invoice gives that VAT back when it deducts the advance, and must give back
exactly the same amount — at the advance's rate, not its own — or the VAT
return declares one figure and reverses another.
"""

from odoo import Command
from odoo.tests import tagged

from .common import AdvanceInvoiceCommon


@tagged("post_install", "-at_install")
class TestAdvanceInvoiceCurrency(AdvanceInvoiceCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.eur = cls.env.ref("base.EUR")
        cls.eur.active = True
        if cls.env.company.currency_id == cls.eur:
            cls.skipTest(cls, "the test company must not keep its books in EUR")
        Rate = cls.env["res.currency.rate"]
        Rate.search([("currency_id", "=", cls.eur.id)]).unlink()
        # company currency per EUR: 25 in January, 20 from February
        Rate.create({"currency_id": cls.eur.id, "name": "2026-01-01",
                     "rate": 1 / 25.0, "company_id": cls.env.company.id})
        Rate.create({"currency_id": cls.eur.id, "name": "2026-02-01",
                     "rate": 1 / 20.0, "company_id": cls.env.company.id})
        cls.pricelist_eur = cls.env["product.pricelist"].create({
            "name": "EUR", "currency_id": cls.eur.id})

    def _duzp(self, move, date):
        """With l10n_cz the rate is the one of the DUZP (§ 38 ZDPH), which
        defaults to today; the dates these tests set must include it."""
        if "taxable_supply_date" in move._fields:
            move.taxable_supply_date = date

    def _order_eur(self):
        order = self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "pricelist_id": self.pricelist_eur.id,
            "order_line": [Command.create({
                "product_id": self.printer.id, "product_uom_qty": 1,
                "price_unit": 1000.0,
                "tax_ids": [Command.set(self.tax_standard.ids)],
            })],
        })
        order.action_confirm()
        return order

    def test_the_deduction_gives_back_the_vat_the_advance_declared(self):
        self._configure_advance_accounts()
        order = self._order_eur()
        self.assertEqual(order.currency_id, self.eur)
        # Itemised, so the advance carries the order's own taxes; a lump-sum
        # advance takes the generic advance product's default tax instead.
        advance = self._advance(order, include_items=True)
        advance.action_confirm()
        self._pay(advance)
        advance.action_create_invoice_direct_for_advance()
        tax_doc = advance.invoice_ids.filtered(lambda m: m.state == "draft")
        tax_doc.invoice_date = "2026-01-10"
        tax_doc.date = "2026-01-10"
        self._duzp(tax_doc, "2026-01-10")
        tax_doc.action_post()
        tax_line = tax_doc.line_ids.filtered("tax_line_id")
        rate = tax_line.tax_line_id.amount / 100.0
        # The tax document declares its VAT at 25 per EUR.
        self.assertAlmostEqual(tax_line.balance, -1000.0 * rate * 25, places=2)

        final = order._create_invoices(final=True)
        final.invoice_date = "2026-02-10"
        final.date = "2026-02-10"
        self._duzp(final, "2026-02-10")
        final.action_post()
        deduction = final.invoice_line_ids.filtered(lambda l: l.price_subtotal < 0)
        self.assertTrue(deduction)
        # The deducted base and its VAT in company currency must reverse
        # exactly what the tax document declared, at ITS rate (25), not at the
        # final invoice's (20).
        self.assertAlmostEqual(
            sum(deduction.mapped("balance")), 25000.0, places=2,
            msg="the deducted base is valued at the final invoice's rate, not "
                "at the rate of the advance's tax document")
        # The advance paid for the whole supply, so the supply is valued at
        # the advance's rate too (§ 38 ZDPH; a received advance is a
        # non-monetary item): revenue 25 000, and the VAT nets to zero.
        supply = final.invoice_line_ids.filtered(lambda l: l.price_subtotal > 0)
        self.assertAlmostEqual(sum(supply.mapped("balance")), -25000.0, places=2)
        self.assertAlmostEqual(
            sum(final.line_ids.filtered("tax_line_id").mapped("balance")),
            0.0, places=2)
        receivable = final.line_ids.filtered(
            lambda l: l.account_id.account_type == "asset_receivable")
        self.assertAlmostEqual(sum(receivable.mapped("balance")), 0.0, places=2)
        self.assertAlmostEqual(
            sum(receivable.mapped("amount_currency")), 0.0, places=2)

    def test_only_the_covered_part_keeps_the_advance_rate(self):
        """Half paid in advance at 25, the rest invoiced at 20."""
        self._configure_advance_accounts()
        order = self._order_eur()
        advance = self._advance(order, method="percentage", amount=50.0,
                                include_items=True)
        advance.action_confirm()
        self._pay(advance)
        advance.action_create_invoice_direct_for_advance()
        tax_doc = advance.invoice_ids.filtered(lambda m: m.state == "draft")
        tax_doc.invoice_date = "2026-01-10"
        tax_doc.date = "2026-01-10"
        self._duzp(tax_doc, "2026-01-10")
        tax_doc.action_post()
        rate = tax_doc.line_ids.filtered("tax_line_id").tax_line_id.amount / 100.0

        final = order._create_invoices(final=True)
        final.invoice_date = "2026-02-10"
        final.date = "2026-02-10"
        self._duzp(final, "2026-02-10")
        final.action_post()
        supply = final.invoice_line_ids.filtered(lambda l: l.price_subtotal > 0)
        deduction = final.invoice_line_ids.filtered(lambda l: l.price_subtotal < 0)
        # 500 EUR covered at 25, 500 EUR remaining at 20.
        self.assertAlmostEqual(sum(supply.mapped("balance")), -22500.0, places=2)
        self.assertAlmostEqual(sum(deduction.mapped("balance")), 12500.0, places=2)
        # VAT on the invoice: only the remainder's, at the invoice's rate.
        self.assertAlmostEqual(
            sum(final.line_ids.filtered("tax_line_id").mapped("balance")),
            -500.0 * rate * 20, places=2)
        receivable = final.line_ids.filtered(
            lambda l: l.account_id.account_type == "asset_receivable")
        self.assertAlmostEqual(
            sum(receivable.mapped("amount_currency")), 500.0 * (1 + rate), places=2)
        self.assertAlmostEqual(
            sum(receivable.mapped("balance")), 500.0 * (1 + rate) * 20, places=2)

    def test_a_posted_invoice_keeps_its_rates(self):
        """Resetting the advance's tax document does not move a posted invoice."""
        self._configure_advance_accounts()
        order = self._order_eur()
        advance = self._advance(order, include_items=True)
        advance.action_confirm()
        self._pay(advance)
        advance.action_create_invoice_direct_for_advance()
        tax_doc = advance.invoice_ids.filtered(lambda m: m.state == "draft")
        tax_doc.invoice_date = "2026-01-10"
        tax_doc.date = "2026-01-10"
        self._duzp(tax_doc, "2026-01-10")
        tax_doc.action_post()
        final = order._create_invoices(final=True)
        final.invoice_date = "2026-02-10"
        final.date = "2026-02-10"
        self._duzp(final, "2026-02-10")
        final.action_post()
        rates = final.invoice_line_ids.mapped("currency_rate")
        tax_doc.button_draft()
        final.invoice_line_ids.invalidate_recordset(["currency_rate"])
        self.assertEqual(final.invoice_line_ids.mapped("currency_rate"), rates)
