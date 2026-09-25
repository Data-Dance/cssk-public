"""Shared fixture for the advance-invoice tests.

An order at two VAT rates, because a single rate hides every question this
module has to answer.
"""

from odoo import Command
from odoo.tests import TransactionCase


class AdvanceInvoiceCommon(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tax_standard = cls.env["account.tax"].create({
            "name": "VAT 21", "amount_type": "percent", "amount": 21.0,
            "type_tax_use": "sale",
        })
        cls.tax_reduced = cls.env["account.tax"].create({
            "name": "VAT 12", "amount_type": "percent", "amount": 12.0,
            "type_tax_use": "sale",
        })
        cls.printer = cls.env["product.product"].create({
            "name": "3D printer", "list_price": 1000.0,
            "taxes_id": [Command.set(cls.tax_standard.ids)],
        })
        cls.filament = cls.env["product.product"].create({
            "name": "Filament", "list_price": 100.0,
            "taxes_id": [Command.set(cls.tax_reduced.ids)],
        })
        cls.partner = cls.env["res.partner"].create({"name": "Customer"})

    def _product_lines(self, order):
        """The order's own lines, without the advance-tracking ones.

        Raising an advance adds a zero-quantity tracking line to the *order*,
        carrying the Advance product and a description naming the advance. It is
        bookkeeping, not something the customer ordered.
        """
        return order.order_line.filtered(
            lambda line: not line.is_advance_tracking and not line.display_type
        )

    def _order(self):
        """Two lines at two different VAT rates: 2000 @ 21% + 500 @ 12%."""
        order = self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "order_line": [
                Command.create({
                    "product_id": self.printer.id, "product_uom_qty": 2,
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
        order.action_confirm()
        return order

    def _advance(self, order, method="full", **values):
        wizard = self.env["sale.advance.invoice.wizard"].with_context(
            active_model="sale.order", active_id=order.id, active_ids=order.ids,
        ).create(dict({
            "sale_order_id": order.id, "advance_payment_method": method,
        }, **values))
        wizard.create_advance_invoice()
        return self.env["sale.order"].search(
            [("advance_invoice_parent_order_id", "=", order.id)], limit=1
        )

    def _configure_advance_accounts(self):
        """The company settings without which no tax document is raised."""
        company = self.env.company
        Account = self.env["account.account"]

        def account(code, name, account_type):
            """Always a fresh account.

            Reusing one the chart already has by code is how this fixture used
            to pick up a 324000 typed as a liability, which the tax document
            then cannot use as its payment term line.
            """
            while Account.search_count(
                [("code", "=", code), ("company_ids", "in", company.id)]
            ):
                code = str(int(code) + 1)
            return Account.create({
                "code": code, "name": name, "account_type": account_type,
            })

        # The clearing account has to be receivable-typed: it stands in for the
        # customer on the tax document's payment term line, and Odoo refuses a
        # payment term line on anything else.
        company.advance_received_account_id = account(
            "324000", "Advances received", "asset_receivable"
        ).id
        company.advance_tax_doc_account_id = account(
            "324100", "Advances - tax doc", "liability_current"
        ).id
        company.advance_invoice_journal_id = self.env["account.journal"].search(
            [("type", "=", "sale")], limit=1
        ).id

    def _pay(self, advance, amount=None):
        """Register a manual payment in full, the way a bank transfer arrives."""
        journal = self.env["account.journal"].search(
            [("type", "=", "bank"), ("company_id", "=", self.env.company.id)], limit=1
        )
        wizard = self.env["sale.order.manual.payment.wizard"].create({
            "sale_order_id": advance.id,
            "amount": advance.amount_total if amount is None else amount,
            "journal_id": journal.id,
            "payment_method_line_id": journal._get_available_payment_method_lines(
                "inbound"
            )[:1].id,
        })
        wizard.action_create_payment()
        return advance

