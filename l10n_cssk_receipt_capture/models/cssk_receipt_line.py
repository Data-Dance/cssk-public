# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models

from ..tools.amounts import split_gross


class CSSKReceiptLine(models.Model):
    """One item from a fiscal receipt.

    ``amount_total`` is the authoritative figure: receipts state the
    **VAT-inclusive line total**, not a unit price, and the two are not
    interchangeable. 31.17 litres for €57.85 is €1.855951… a litre, so any
    stored unit price is already wrong by construction; the quantity is kept
    here because it is useful (litres pumped, portions ordered) and left out of
    the posted document because it would not foot.
    """

    _name = "cssk.receipt.line"
    _description = "Fiscal Receipt Line"
    _order = "receipt_id, sequence, id"

    receipt_id = fields.Many2one(
        "cssk.receipt", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one(related="receipt_id.company_id", store=True)
    currency_id = fields.Many2one(related="receipt_id.currency_id")
    sequence = fields.Integer(default=10)

    name = fields.Char(string="Description", required=True)
    quantity = fields.Float(default=1.0, digits=(16, 3))
    uom_label = fields.Char(
        string="Unit",
        help="The unit as the receipt words it. Informative: the posted "
             "document carries the line total, not a unit price.")
    vat_rate = fields.Float(string="VAT rate (%)", digits=(16, 2))
    amount_total = fields.Monetary(
        string="Line total", help="VAT-inclusive, exactly as the receipt states it.")
    amount_untaxed = fields.Monetary(compute="_compute_amounts", store=True)
    amount_tax = fields.Monetary(compute="_compute_amounts", store=True)
    is_negative = fields.Boolean(
        help="A return / correction item (eKasa itemType 'Z').")

    @api.depends("amount_total", "vat_rate", "currency_id")
    def _compute_amounts(self):
        for line in self:
            rounding = line.currency_id.rounding or 0.01
            base, tax = split_gross(line.amount_total, line.vat_rate, rounding)
            line.amount_untaxed = base
            line.amount_tax = tax


class CSSKReceiptTax(models.Model):
    """One VAT bucket from the receipt's own recap.

    This is what gets posted. It is a separate model rather than a pair of
    fields because a receipt can carry three rates at once — in Slovak
    hospitality that is routine, not exotic: food at 5 %, non-alcoholic drinks
    at 19 %, alcohol at 23 % — and because the two-slot "basic / reduced" recap
    some authorities still emit alongside it is unreliable: observed carrying
    stale rate labels on one receipt and arriving entirely null on another.
    """

    _name = "cssk.receipt.tax"
    _description = "Fiscal Receipt VAT Recap Row"
    _order = "receipt_id, vat_rate desc"

    receipt_id = fields.Many2one(
        "cssk.receipt", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one(related="receipt_id.company_id", store=True)
    currency_id = fields.Many2one(related="receipt_id.currency_id")

    vat_rate = fields.Float(string="VAT rate (%)", required=True, digits=(16, 2))
    amount_untaxed = fields.Monetary(string="Taxable base", required=True)
    amount_tax = fields.Monetary(string="VAT amount", required=True)
    amount_total = fields.Monetary(compute="_compute_amount_total")

    _rate_receipt_uniq = models.Constraint(
        "unique(receipt_id, vat_rate)",
        "The same VAT rate appears twice in this receipt's recap.",
    )

    @api.depends("amount_untaxed", "amount_tax")
    def _compute_amount_total(self):
        for row in self:
            row.amount_total = row.amount_untaxed + row.amount_tax
