"""Itemised advance invoices (ADATEX ID 39/87).

The generic Advance product carries one VAT rate, so an order mixing rates could
never be advanced correctly: the rate reached the ledger through the tax
document raised on payment. Listing the ordered items on the advance, each with
its own product and its own taxes, is what fixes it - see
``test_advance_invoice_characterisation`` for the behaviour these tests replace.
"""

from odoo.tests import tagged

from .common import AdvanceInvoiceCommon


@tagged("post_install", "-at_install")
class TestAdvanceInvoiceItems(AdvanceInvoiceCommon):

    def _itemised(self, order, method="full", **values):
        return self._advance(order, method, include_items=True, **values)

    # === THE DOCUMENT ===#

    def test_an_itemised_advance_carries_the_order_s_own_products(self):
        order = self._order()
        advance = self._itemised(order)
        self.assertEqual(
            advance.order_line.mapped("product_id"),
            self._product_lines(order).mapped("product_id"),
        )
        self.assertEqual(advance.order_line.mapped("product_uom_qty"), [2.0, 5.0])
        self.assertEqual(advance.order_line.mapped("price_unit"), [1000.0, 100.0])

    def test_a_full_itemised_advance_totals_the_order_it_advances(self):
        """What the characterisation pins as impossible without items."""
        order = self._order()
        advance = self._itemised(order)
        self.assertAlmostEqual(advance.amount_untaxed, order.amount_untaxed, places=2)
        self.assertAlmostEqual(advance.amount_total, order.amount_total, places=2)
        self.assertAlmostEqual(advance.amount_total, 2980.0, places=2)

    def test_each_line_keeps_the_rate_it_was_ordered_at(self):
        advance = self._itemised(self._order())
        rates = {
            line.product_id.name: line.tax_ids.mapped("amount")
            for line in advance.order_line
        }
        self.assertEqual(rates, {"3D printer": [21.0], "Filament": [12.0]})

    def test_the_generic_advance_product_is_not_used_at_all(self):
        advance = self._itemised(self._order())
        advance_product = self.env["sale.order"]._get_advance_product()
        self.assertNotIn(advance_product, advance.order_line.mapped("product_id"))

    # === PARTIAL AMOUNTS ===#

    def test_a_percentage_advance_scales_the_prices_not_the_quantities(self):
        """Half an order is a smaller payment for the same goods.

        Halving the quantities would say the customer ordered one printer, and
        would reserve half the stock once fulfilment follows the items.
        """
        order = self._order()
        advance = self._itemised(order, "percentage", amount=50.0)
        self.assertEqual(advance.order_line.mapped("product_uom_qty"), [2.0, 5.0])
        self.assertEqual(advance.order_line.mapped("price_unit"), [500.0, 50.0])
        self.assertAlmostEqual(advance.amount_untaxed, 1250.0, places=2)
        self.assertAlmostEqual(advance.amount_total, 1490.0, places=2)

    def test_a_percentage_advance_keeps_the_rate_mix(self):
        advance = self._itemised(self._order(), "percentage", amount=50.0)
        vat = advance.amount_total - advance.amount_untaxed
        self.assertAlmostEqual(vat, 240.0, places=2, msg="half of 420 + half of 60")

    def test_a_fixed_advance_totals_exactly_the_amount_asked(self):
        """Scaling every price by one ratio and rounding each does not add up.

        333.33 over this order leaves two cents unallocated; they are put on the
        largest line rather than dropped.
        """
        advance = self._itemised(self._order(), "fixed", fixed_amount=333.33)
        self.assertAlmostEqual(advance.amount_untaxed, 333.33, places=2)

    def test_a_partial_advance_says_so_on_every_line(self):
        advance = self._itemised(self._order(), "percentage", amount=50.0)
        for line in advance.order_line:
            self.assertIn("50.0%", line.name)

    def test_a_full_advance_does_not_annotate_the_lines(self):
        order = self._order()
        advance = self._itemised(order)
        self.assertEqual(
            advance.order_line.mapped("name"),
            self._product_lines(order).mapped("name"),
        )

    # === WHERE IT MATTERS: THE TAX DOCUMENT ===#

    def test_the_tax_document_of_an_itemised_advance_follows_the_order(self):
        """The advance accounts nothing; the document raised on its payment does.

        This is the whole point of the change: 480 of VAT split 420 at 21 % and
        60 at 12 %, instead of 375 at whatever rate the Advance product carried.
        """
        self._configure_advance_accounts()
        order = self._order()
        advance = self._itemised(order)
        advance.action_confirm()

        tax_document = advance._create_invoices()
        self.assertTrue(tax_document.is_advance_invoice_tax_document)

        document_vat = tax_document.amount_total - tax_document.amount_untaxed
        self.assertAlmostEqual(document_vat, 480.0, places=2)
        self.assertAlmostEqual(
            document_vat, order.amount_total - order.amount_untaxed, places=2
        )
        self.assertEqual(
            set(tax_document.invoice_line_ids.tax_ids.mapped("amount")), {21.0, 12.0}
        )

    def test_the_tax_document_still_posts_to_the_advance_account(self):
        """Real products must not book revenue: nothing has been delivered.

        Raised through the action the paid advance offers, which is the path
        that forces the account.
        """
        self._configure_advance_accounts()
        advance = self._itemised(self._order())
        advance.action_confirm()
        self._pay(advance)

        advance.action_create_invoice_direct_for_advance()
        tax_document = advance.invoice_ids[-1]
        net_account = self.env.company.advance_tax_doc_account_id
        self.assertEqual(
            set(tax_document.invoice_line_ids.filtered(
                lambda line: line.display_type == "product"
            ).mapped("account_id")),
            {net_account},
        )
        document_vat = tax_document.amount_total - tax_document.amount_untaxed
        self.assertAlmostEqual(document_vat, 480.0, places=2)
        self.assertEqual(
            set(tax_document.invoice_line_ids.tax_ids.mapped("amount")), {21.0, 12.0}
        )

    # === FULFILMENT BELONGS TO THE PARENT ORDER ===#

    def test_confirming_an_itemised_advance_delivers_nothing(self):
        """Otherwise the same goods would be reserved on two delivery orders."""
        if "stock.picking" not in self.env:
            self.skipTest("sale_stock is not installed")
        advance = self._itemised(self._order())
        advance.action_confirm()
        self.assertFalse(advance.picking_ids)

    # === AND THE FINAL INVOICE, WHICH DEDUCTS IT ===#

    def test_a_fully_advanced_order_invoices_to_nothing(self):
        """The advance is deducted with the VAT it actually carried.

        An advance covering the whole order leaves nothing to pay: the goods and
        the VAT on the final invoice are cancelled by the deduction of an advance
        that charged exactly the same. If the deduction reverses VAT at one rate
        the difference lands on the customer's balance and on the VAT return.
        """
        self._configure_advance_accounts()
        order = self._order()
        advance = self._itemised(order)
        advance.action_confirm()
        self._pay(advance)
        advance.action_create_invoice_direct_for_advance()
        advance.invoice_ids.filtered(lambda m: m.state == "draft").action_post()

        invoice = order._create_invoices(final=True)
        self.assertAlmostEqual(invoice.amount_untaxed, 0.0, places=2)
        self.assertAlmostEqual(
            invoice.amount_total, 0.0, places=2,
            msg="the deduction gave back VAT at a rate the advance never charged",
        )

    def test_the_deduction_is_split_by_rate(self):
        """One deduction line per rate, because one line can carry one tax."""
        self._configure_advance_accounts()
        order = self._order()
        advance = self._itemised(order)
        advance.action_confirm()
        self._pay(advance)
        advance.action_create_invoice_direct_for_advance()
        advance.invoice_ids.filtered(lambda m: m.state == "draft").action_post()

        invoice = order._create_invoices(final=True)
        deductions = invoice.invoice_line_ids.filtered(
            lambda line: line.price_subtotal < 0
        )
        self.assertEqual(len(deductions), 2)
        self.assertEqual(
            {
                tuple(line.tax_ids.mapped("amount")): line.price_subtotal
                for line in deductions
            },
            {(21.0,): -2000.0, (12.0,): -500.0},
        )

    def test_two_partial_advances_deduct_to_nothing_between_them(self):
        """Each advance is deducted at its own rates, and the order closes.

        Two halves are the case where a deduction that split once could be
        split again, or where one advance's lines could be attributed to the
        other.
        """
        self._configure_advance_accounts()
        order = self._order()
        for _half in range(2):
            advance = self._itemised(order, "percentage", amount=50.0)
            advance.action_confirm()
            self._pay(advance)
            advance.action_create_invoice_direct_for_advance()
            advance.invoice_ids.filtered(lambda m: m.state == "draft").action_post()

        self.assertEqual(len(order.advance_invoice_ids), 2)
        invoice = order._create_invoices(final=True)
        deductions = invoice.invoice_line_ids.filtered(
            lambda line: line.price_subtotal < 0
        )
        self.assertEqual(len(deductions), 4, "two advances at two rates each")
        self.assertAlmostEqual(sum(deductions.mapped("price_subtotal")), -2500.0, places=2)
        self.assertAlmostEqual(invoice.amount_total, 0.0, places=2)

    def test_a_fixed_advance_on_awkward_quantities_still_totals_exactly(self):
        """The residual is absorbed by the line whose quantity can express it."""
        order = self._order()
        advance = self._itemised(order, "fixed", fixed_amount=1000.01)
        self.assertAlmostEqual(advance.amount_untaxed, 1000.01, places=2)
