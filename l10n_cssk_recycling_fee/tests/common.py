# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class RecyclingFeeCommon(AccountTestInvoicingCommon):
    """Fixtures shared by the CZ and SK suites.

    Each suite runs on a company with that country's real chart, because the
    fee is chosen by the company's fiscal country and priced in the scheme's
    currency — a chart-less company would hide both.
    """

    @classmethod
    def _classification(cls, name, country, ecotax_type, rates, **extra):
        return cls.env["account.ecotax.classification"].create(
            {
                "name": name,
                "code": name.upper().replace(" ", "_"),
                "ecotax_type": ecotax_type,
                "product_status": "M",
                "supplier_status": "MAN",
                "country_id": country.id,
                "rate_ids": [
                    Command.create(
                        {"date_from": date_from, "date_to": date_to, "amount": amount}
                    )
                    for date_from, date_to, amount in rates
                ],
                **extra,
            }
        )

    @classmethod
    def _product(cls, name, classifications, weight=0.0, force=0.0):
        return cls.env["product.product"].create(
            {
                "name": name,
                "list_price": 100.0,
                "weight": weight,
                "ecotax_line_product_ids": [
                    Command.create(
                        {"classification_id": classification.id, "force_amount": force}
                    )
                    for classification in classifications
                ],
            }
        )

    @classmethod
    def _invoice(cls, lines, invoice_date="2026-03-15", move_type="out_invoice",
                 currency=None, post=False):
        return cls._create_invoice(
            move_type=move_type,
            invoice_date=invoice_date,
            currency_id=(currency or cls.company.currency_id).id,
            invoice_line_ids=[
                Command.create(
                    {
                        "product_id": product.id,
                        "quantity": qty,
                        "price_unit": price,
                        "tax_ids": [Command.set(cls.tax_sale_a.ids)],
                        **extra,
                    }
                )
                for product, qty, price, *rest in lines
                for extra in [rest[0] if rest else {}]
            ],
            post=post,
        )

    def _render(self, invoice):
        return self.env["ir.actions.report"]._render_qweb_html(
            "account.account_invoices", invoice.ids
        )[0].decode()
