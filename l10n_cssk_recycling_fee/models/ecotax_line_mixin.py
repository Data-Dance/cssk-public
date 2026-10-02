# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools.misc import formatLang


class EcotaxLineMixin(models.AbstractModel):
    """Price a statutory recycling fee on a document line.

    OCA ``account_ecotax`` computes a document's ecotax from one static amount
    on the classification, in whatever currency the document happens to be
    in, per unit of whatever UoM the line is in. For the CZ/SK fee each of
    those three is wrong:

    * the rate is the scheme's tariff valid on the DOCUMENT date (§ 73 odst. 2
      zákona č. 542/2020 Sb. ties it to what the producer pays the scheme,
      which changes with the scheme's price list);
    * it is denominated in the scheme's currency, and an invoice in another
      currency must show the original amount and the rate used (MŽP guideline
      of 26. 10. 2021, point 2.5);
    * it is per PIECE (or per kg), so a line sold by the dozen owes twelve.

    Lines whose classification has no ``country_id`` keep OCA's computation
    untouched, so the vendored module behaves as upstream wherever the CZ/SK
    extension is not being used.
    """

    _inherit = "ecotax.line.mixin"

    product_force_amount = fields.Float(
        string="Product Fixed Fee",
        digits="Ecotax",
        help="Per-piece fee fixed on the product, in the classification's "
        "currency. A distributor enters here the amount its supplier actually "
        "paid, which the law makes the ceiling of what may be shown.",
    )
    rate_currency_id = fields.Many2one(
        "res.currency",
        string="Rate Currency",
        compute="_compute_ecotax",
        store=True,
    )
    rate_amount = fields.Float(
        string="Applied Rate",
        digits="Ecotax",
        compute="_compute_ecotax",
        store=True,
        help="Rate per piece or per kg that was in force on the document date.",
    )
    unit_weight = fields.Float(
        string="Weight per Piece (kg)",
        digits="Stock Weight",
        compute="_compute_ecotax",
        store=True,
    )
    product_qty = fields.Float(
        string="Pieces",
        digits="Product Unit",
        compute="_compute_ecotax",
        store=True,
        help="Quantity in the product's own unit of measure.",
    )
    amount_unit_rate_currency = fields.Float(
        string="Fee per Piece (Rate Currency)",
        digits="Ecotax",
        compute="_compute_ecotax",
        store=True,
    )
    amount_total_rate_currency = fields.Float(
        string="Fee Total (Rate Currency)",
        digits="Ecotax",
        compute="_compute_ecotax",
        store=True,
    )
    exchange_rate = fields.Float(
        digits=(12, 6),
        compute="_compute_ecotax",
        store=True,
        help="Units of the rate currency per one unit of the document "
        "currency, as printed on the document. 1 when they are the same.",
    )

    def _recycling_fee_is_frozen(self):
        """Whether this line belongs to a finished document. Overridden by the
        invoice line model; an order stays live until it is invoiced."""
        return False

    def _get_recycling_fee_context(self):
        """Return ``(date, company, pieces)`` for this line.

        Overridden by each concrete line model, which knows its document.
        """
        self.ensure_one()
        return (
            fields.Date.context_today(self),
            self.env.company,
            self.quantity,
        )

    @api.depends(
        "classification_id.country_id",
        "classification_id.currency_id",
        "classification_id.rate_ids.amount",
        "classification_id.rate_ids.date_from",
        "classification_id.rate_ids.date_to",
        "product_force_amount",
        "product_id.weight",
        "product_id.product_tmpl_id.weight",
        "currency_id",
    )
    def _compute_ecotax(self):
        statutory = self.filtered("classification_id.country_id")
        upstream = self - statutory
        if not self.env.context.get("recycling_fee_recompute"):
            # A posted document is a record of what was charged and declared.
            # Editing a tariff, a product weight or a classification later
            # must not rewrite it; leaving the stored value unassigned keeps
            # what is in the database.
            statutory = statutory.filtered(lambda l: not l._recycling_fee_is_frozen())
        if upstream:
            super(EcotaxLineMixin, upstream)._compute_ecotax()
            upstream.update(
                {
                    "rate_currency_id": False,
                    "rate_amount": 0.0,
                    "unit_weight": 0.0,
                    "product_qty": 0.0,
                    "amount_unit_rate_currency": 0.0,
                    "amount_total_rate_currency": 0.0,
                    "exchange_rate": 0.0,
                }
            )
        for line in statutory:
            line._compute_statutory_fee()

    def _compute_statutory_fee(self):
        self.ensure_one()
        date, company, pieces = self._get_recycling_fee_context()
        classification = self.classification_id
        rate_ccy = classification.currency_id or company.currency_id
        doc_ccy = self.currency_id or company.currency_id
        product = self.product_id
        weight = product.weight or product.product_tmpl_id.weight or 0.0
        rate_amount = classification._get_rate(date).amount
        if self.product_force_amount:
            unit_src = self.product_force_amount
        elif classification.ecotax_type == "weight_based":
            unit_src = rate_amount * weight
        else:
            unit_src = rate_amount
        # MŽP guideline point 2.4: at most two decimals throughout the
        # distribution chain, i.e. the currency's own rounding.
        unit_src = rate_ccy.round(unit_src)
        if rate_ccy == doc_ccy:
            exchange_rate = 1.0
        else:
            to_doc = self.env["res.currency"]._get_conversion_rate(
                rate_ccy, doc_ccy, company, date
            )
            exchange_rate = to_doc and 1.0 / to_doc or 0.0
        if self.force_amount_unit:
            unit_doc = self.force_amount_unit
            unit_src = (
                rate_ccy.round(unit_doc * exchange_rate)
                if rate_ccy != doc_ccy
                else unit_doc
            )
        elif rate_ccy == doc_ccy:
            unit_doc = unit_src
        else:
            unit_doc = rate_ccy._convert(unit_src, doc_ccy, company, date)
        self.rate_currency_id = rate_ccy
        self.rate_amount = rate_amount
        self.unit_weight = weight
        self.product_qty = pieces
        self.exchange_rate = exchange_rate
        self.amount_unit_rate_currency = unit_src
        self.amount_total_rate_currency = rate_ccy.round(unit_src * pieces)
        self.amount_unit = unit_doc
        self.amount_total = doc_ccy.round(unit_doc * pieces)

    def _get_recycling_fee_text(self, presentation="included", tax_included=False):
        """The line's statutory sentence, e.g.

        ``z toho recyklační příspěvek 100,00 Kč (0,50 Kč/kg × 2,000 kg = 1,00 Kč/ks)``

        It carries what MŽP's guideline (point 2.1, examples 1–5) requires per
        item: the rate per piece or per kg, the weight for a per-kg fee, the
        fee per piece and the fee for the whole line. Quantity is already in
        the line's own column. Returns ``""`` when nothing may be printed.
        """
        self.ensure_one()
        classification = self.classification_id
        phrases = classification._statutory_phrases()
        if not phrases or not classification.disclose or not self.amount_total:
            return ""
        env = self.env
        lang = {"CZ": "cs_CZ", "SK": "sk_SK"}.get(classification.country_id.code)
        if lang and env["res.lang"]._get_code(lang):
            env = env(context=dict(env.context, lang=lang))
        doc_ccy = self.currency_id or self.rate_currency_id
        rate_ccy = self.rate_currency_id or doc_ccy

        def money(amount, currency):
            return formatLang(env, amount, currency_obj=currency)

        piece = phrases["piece"]
        if classification.ecotax_type == "weight_based" and not (
            self.force_amount_unit or self.product_force_amount
        ):
            breakdown = "{rate}/kg × {weight} kg = {unit}/{piece}".format(
                rate=money(self.rate_amount, rate_ccy),
                weight=formatLang(env, self.unit_weight, digits=3),
                unit=money(self.amount_unit, doc_ccy),
                piece=piece,
            )
        else:
            breakdown = f"{money(self.amount_unit, doc_ccy)}/{piece}"
        text = "{lead} {total}".format(
            lead=phrases[presentation],
            total=money(self.amount_total, doc_ccy),
        )
        if tax_included:
            text += " " + phrases["without_vat"]
        text += f" ({breakdown})"
        if rate_ccy != doc_ccy:
            text += " = {src}, {fx} {rate} {src_code}/{doc_code}".format(
                src=money(self.amount_total_rate_currency, rate_ccy),
                fx=phrases["fx"],
                rate=formatLang(env, self.exchange_rate, digits=4),
                src_code=rate_ccy.name,
                doc_code=doc_ccy.name,
            )
        return text
