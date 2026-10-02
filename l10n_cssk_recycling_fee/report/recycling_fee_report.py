# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, tools


class RecyclingFeeReport(models.Model):
    """Pieces, kilograms and fee per category, country and period.

    What a producer declares to its collective scheme (or, individually, to the
    ministry) is quantities placed on the market per category — pieces and
    kilograms — and the scheme bills the fee from those. This view gives both
    sides of that, from posted customer invoices and credit notes, with the
    credit notes negative so a return nets out in the period it is booked.

    The amounts are in the RATE currency (CZK for a CZ scheme, EUR for SK)
    whatever the invoice currency, because that is the currency the scheme
    bills in and the one the declaration is reconciled against.
    """

    _name = "recycling.fee.report"
    _description = "Recycling Fee Report"
    _auto = False
    _order = "date desc"

    date = fields.Date(readonly=True)
    company_id = fields.Many2one("res.company", readonly=True)
    move_id = fields.Many2one("account.move", string="Invoice", readonly=True)
    move_type = fields.Selection(
        [("out_invoice", "Customer Invoice"), ("out_refund", "Customer Credit Note")],
        readonly=True,
    )
    partner_id = fields.Many2one("res.partner", readonly=True)
    product_id = fields.Many2one("product.product", readonly=True)
    country_id = fields.Many2one("res.country", string="Scheme Country", readonly=True)
    classification_id = fields.Many2one(
        "account.ecotax.classification", readonly=True
    )
    categ_id = fields.Many2one(
        "account.ecotax.category", string="Category", readonly=True
    )
    collector_id = fields.Many2one(
        "ecotax.collector", string="Collective Scheme", readonly=True
    )
    ecotax_type = fields.Selection(
        [("fixed", "Per piece"), ("weight_based", "Per kg")],
        string="Rate Basis",
        readonly=True,
    )
    product_status = fields.Selection(
        [("M", "Domestic"), ("P", "Professional")], readonly=True
    )
    currency_id = fields.Many2one("res.currency", readonly=True)
    pieces = fields.Float(digits="Product Unit", readonly=True, aggregator="sum")
    weight_kg = fields.Float(
        string="Weight (kg)", digits="Stock Weight", readonly=True, aggregator="sum"
    )
    fee_amount = fields.Monetary(
        string="Fee", currency_field="currency_id", readonly=True, aggregator="sum"
    )

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT
                    fee.id AS id,
                    COALESCE(move.invoice_date, move.date) AS date,
                    move.company_id AS company_id,
                    move.id AS move_id,
                    move.move_type AS move_type,
                    move.commercial_partner_id AS partner_id,
                    line.product_id AS product_id,
                    cls.country_id AS country_id,
                    cls.id AS classification_id,
                    cls.categ_id AS categ_id,
                    cls.collector_id AS collector_id,
                    cls.ecotax_type AS ecotax_type,
                    cls.product_status AS product_status,
                    fee.rate_currency_id AS currency_id,
                    sign.factor * fee.product_qty AS pieces,
                    sign.factor * fee.product_qty * fee.unit_weight AS weight_kg,
                    sign.factor * fee.amount_total_rate_currency AS fee_amount
                FROM account_move_line_ecotax fee
                JOIN account_move_line line ON line.id = fee.account_move_line_id
                JOIN account_move move ON move.id = line.move_id
                JOIN account_ecotax_classification cls
                    ON cls.id = fee.classification_id
                CROSS JOIN LATERAL (
                    SELECT CASE WHEN move.move_type = 'out_refund'
                                THEN -1 ELSE 1 END AS factor
                ) sign
                WHERE move.state = 'posted'
                  AND move.move_type IN ('out_invoice', 'out_refund')
                  AND cls.country_id IS NOT NULL
            )
            """
        )
