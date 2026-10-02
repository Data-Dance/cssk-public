# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.l10n_cssk_recycling_fee.tests.common import RecyclingFeeCommon


@tagged("post_install", "-at_install")
class TestRecyclingFeeSale(RecyclingFeeCommon):
    @classmethod
    def get_default_groups(cls):
        return super().get_default_groups() | cls.quick_ref(
            "sales_team.group_sale_manager"
        )

    @classmethod
    @RecyclingFeeCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cz = cls.env.ref("base.cz")
        cls.kettle_class = cls._classification(
            "Small household appliance", cz, "fixed",
            [("2025-01-01", "2025-12-31", 5.0), ("2026-01-01", False, 6.0)],
        )
        cls.battery_class = cls._classification(
            "Portable battery", cz, "fixed", [("2025-01-01", False, 0.4)],
            disclose=False,
        )
        cls.kettle = cls._product("Kettle", cls.kettle_class)
        cls.battery = cls._product("AA cell", cls.battery_class)
        cls.fee_product = cls.env["product.product"].create(
            {"name": "Recyklační příspěvek", "type": "service", "list_price": 0.0}
        )

    def _order(self, lines, date_order="2025-06-30 10:00:00"):
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner_a.id,
                "date_order": date_order,
                "order_line": [
                    Command.create(
                        {
                            "product_id": product.id,
                            "product_uom_qty": qty,
                            "price_unit": price,
                            "tax_ids": [Command.set(self.tax_sale_a.ids)],
                        }
                    )
                    for product, qty, price in lines
                ],
            }
        )

    def _invoice_order(self, order, invoice_date="2026-03-15"):
        order.action_confirm()
        invoice = order._create_invoices()
        invoice.invoice_date = invoice_date
        return invoice

    def test_order_priced_at_order_date_invoice_at_invoice_date(self):
        order = self._order([(self.kettle, 2, 405.0)])
        self.assertEqual(order.order_line.subtotal_ecotax, 10.0)
        invoice = self._invoice_order(order)
        fee = invoice.invoice_line_ids.ecotax_line_ids
        self.assertEqual(fee.classification_id, self.kettle_class)
        self.assertEqual(fee.amount_total, 12.0)

    def test_product_fixed_amount_reaches_the_invoice(self):
        product = self._product("Import kettle", self.kettle_class, force=3.5)
        order = self._order([(product, 2, 405.0)])
        self.assertEqual(order.order_line.ecotax_line_ids.product_force_amount, 3.5)
        invoice = self._invoice_order(order)
        fee = invoice.invoice_line_ids.ecotax_line_ids
        self.assertEqual(fee.product_force_amount, 3.5)
        self.assertEqual(fee.amount_total, 7.0)

    def test_on_top_fee_lines(self):
        self.company.recycling_fee_presentation = "on_top"
        self.company.recycling_fee_product_id = self.fee_product
        order = self._order(
            [(self.kettle, 2, 400.0), (self.battery, 5, 30.0)],
            date_order="2026-02-01 10:00:00",
        )
        order.action_update_recycling_fee_lines()
        order.action_update_recycling_fee_lines()  # idempotent
        fee_lines = order.order_line.filtered("is_recycling_fee_line")
        # One line for the kettle's classification; the battery fee may not
        # be listed separately and stays in the price.
        self.assertEqual(len(fee_lines), 1)
        self.assertEqual(fee_lines.price_unit, 12.0)
        self.assertEqual(fee_lines.tax_ids, self.tax_sale_a)
        self.assertIn("Recyklační příspěvek", fee_lines.name)
        invoice = self._invoice_order(order)
        self.assertEqual(
            invoice.invoice_line_ids.filtered(
                lambda l: l.product_id == self.fee_product
            ).price_subtotal,
            12.0,
        )
        with self.assertRaisesRegex(UserError, "already invoiced"):
            order.action_update_recycling_fee_lines()

    def test_on_top_requires_a_fee_product(self):
        self.company.recycling_fee_presentation = "on_top"
        order = self._order([(self.kettle, 1, 400.0)])
        with self.assertRaisesRegex(UserError, "recycling fee product"):
            order.action_update_recycling_fee_lines()
