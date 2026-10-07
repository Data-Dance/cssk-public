"""Characterisation of the advance invoice as it behaves today.

These tests describe current behaviour, not desired behaviour. Some of what they
assert is wrong - the VAT on an advance does not follow the order it advances -
and each such case says so. They exist so that changing any of it is a deliberate
act with a visible diff, because this module carries 2000 lines of money and VAT
logic and had no tests at all.

Written before adding itemised advance invoices (a customer request, ticket 39/87).
"""

from odoo.tests import tagged

from .common import AdvanceInvoiceCommon


@tagged("post_install", "-at_install")
class TestAdvanceInvoiceCharacterisation(AdvanceInvoiceCommon):

    # === WHAT THE WIZARD BUILDS ===#

    def test_full_advance_makes_one_line_per_order_line(self):
        order = self._order()
        advance = self._advance(order)
        self.assertTrue(advance.is_advance_invoice)
        self.assertEqual(len(advance.order_line), 2)

    def test_percentage_advance_makes_a_single_summary_line(self):
        advance = self._advance(self._order(), "percentage", amount=50.0)
        self.assertEqual(len(advance.order_line), 1)
        self.assertAlmostEqual(advance.amount_untaxed, 1250.0, places=2)

    def test_fixed_advance_makes_a_single_summary_line(self):
        advance = self._advance(self._order(), "fixed", fixed_amount=1000.0)
        self.assertEqual(len(advance.order_line), 1)
        self.assertAlmostEqual(advance.amount_untaxed, 1000.0, places=2)

    def test_every_advance_line_is_the_generic_advance_product(self):
        """The order's own products do not reach the advance.

        This is why quantity, unit of measure and unit price cannot be shown:
        each line is one unit of "Advance" priced at the order line's subtotal.
        """
        order = self._order()
        advance = self._advance(order)
        advance_product = self.env["sale.order"]._get_advance_product()
        self.assertEqual(set(advance.order_line.mapped("product_id")), {advance_product})
        self.assertEqual(set(advance.order_line.mapped("product_uom_qty")), {1.0})
        self.assertEqual(
            sorted(advance.order_line.mapped("price_unit")), [500.0, 2000.0],
            "the price carried is the order line's subtotal, not its unit price",
        )

    def test_the_order_line_description_is_the_only_thing_carried_over(self):
        order = self._order()
        expected = sorted(order.order_line.mapped("name"))
        advance = self._advance(order)
        self.assertEqual(sorted(advance.order_line.mapped("name")), expected)

    def test_raising_an_advance_adds_tracking_lines_to_the_order(self):
        """The order gains a section heading and a zero-quantity line per advance.

        Both are flagged `is_advance_tracking`, so anything counting the order's
        real lines has to exclude the section as well as the tracking line.
        """
        order = self._order()
        before = len(order.order_line)
        advance = self._advance(order)
        tracking = order.order_line.filtered("is_advance_tracking")
        self.assertEqual(len(tracking), 2)

        section = tracking.filtered(lambda line: line.display_type == "line_section")
        entry = tracking - section
        self.assertEqual(len(section), 1, "a section heading is added once")
        self.assertEqual(len(entry), 1, "and one line per advance beneath it")
        self.assertIn(advance.name, entry.name)
        self.assertEqual(entry.product_uom_qty, 0.0)
        self.assertGreater(len(order.order_line), before)

    # === WHAT IS WRONG, PINNED DELIBERATELY ===#

    def test_advance_vat_comes_from_the_advance_product_not_the_order(self):
        """WRONG, AND PINNED: the advance is taxed at whatever the Advance
        product carries, which has nothing to do with the order it advances.

        Every line of the advance is the same product, so an advance can express
        exactly one VAT rate however the product is configured. An order at two
        rates therefore cannot be advanced correctly, and the tax document raised
        on payment inherits the error into the VAT return.
        """
        order = self._order()
        advance = self._advance(order)
        order_rates = set(self._product_lines(order).tax_ids.mapped("amount"))
        advance_rates = set(advance.order_line.tax_ids.mapped("amount"))
        self.assertEqual(order_rates, {21.0, 12.0})
        self.assertNotEqual(
            advance_rates, order_rates,
            "if this ever passes, the advance has started following the order's"
            " VAT and this characterisation is out of date",
        )

    def test_a_full_advance_does_not_total_the_order_it_advances(self):
        """WRONG, AND PINNED: a 100 % advance should be the order's gross."""
        order = self._order()
        advance = self._advance(order)
        self.assertAlmostEqual(
            advance.amount_untaxed, order.amount_untaxed, places=2,
            msg="the net is right - only the VAT is not",
        )
        self.assertNotAlmostEqual(
            advance.amount_total, order.amount_total, places=2,
            msg="if this ever passes, the VAT bug is fixed and this test should go",
        )

    # === WHERE THE ERROR ACTUALLY LANDS ===#

    def test_the_tax_document_inherits_the_advance_s_wrong_rate(self):
        """WRONG, AND PINNED - this is where the error stops being cosmetic.

        An advance invoice is not a tax document and accounts nothing, so the VAT
        printed on it is informative and the report is right to hide it. But the
        tax document raised when the advance is paid is built from the advance's
        own lines, and that document *is* accounted. So the rate taken from the
        Advance product reaches the ledger and the VAT return one step later:
        here the order bears 480 of VAT and the tax document accounts 375.

        Fixing the advance's lines therefore fixes the tax document too, because
        the one is the template for the other.
        """
        self._configure_advance_accounts()
        order = self._order()
        advance = self._advance(order)
        advance.action_confirm()

        tax_document = advance._create_invoices()
        self.assertTrue(tax_document.is_advance_invoice_tax_document)

        order_vat = order.amount_total - order.amount_untaxed
        document_vat = tax_document.amount_total - tax_document.amount_untaxed
        self.assertAlmostEqual(order_vat, 480.0, places=2)
        self.assertNotAlmostEqual(
            document_vat, order_vat, places=2,
            msg="if this passes, the tax document has started following the"
                " order's VAT and this characterisation is out of date",
        )
        self.assertEqual(
            set(tax_document.invoice_line_ids.tax_ids.mapped("amount")),
            set(advance.order_line.tax_ids.mapped("amount")),
            "the document's rates are the advance's, not the order's",
        )

    def test_a_lump_sum_advance_settles_the_vat_difference(self):
        """A lump-sum advance is taxed at ONE rate, the advance product's; the
        order here is at two. The deduction gives back exactly the VAT the tax
        document declared, and the final invoice settles the difference
        between the order's VAT and the advance's: nothing is left behind,
        nothing is charged twice.

        The amount depends on the chart's default rate (15 % without a chart:
        480 - 375 = 105 due; CZ 21 %: 480 - 525 = 45 back; SK 23 %: 95 back),
        so the test states the rule, not a number. Itemising the advance
        makes the difference zero; see ``test_advance_invoice_items``.
        """
        self._configure_advance_accounts()
        order = self._order()
        advance = self._advance(order)
        advance.action_confirm()
        self._pay(advance)
        advance.action_create_invoice_direct_for_advance()
        tax_doc = advance.invoice_ids.filtered(lambda m: m.state == "draft")
        tax_doc.action_post()

        invoice = order._create_invoices(final=True)
        self.assertAlmostEqual(invoice.amount_untaxed, 0.0, places=2)
        # Signed: a larger advance VAT turns the final document into a refund.
        self.assertAlmostEqual(
            invoice.amount_total_signed, order.amount_tax - tax_doc.amount_tax,
            places=2)
