# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

# The words the statute uses, which is what goes on the document. Czech: MŽP's
# guideline on § 73 zákona č. 542/2020 Sb. (26. 10. 2021, point 2.3) asks for
# "Recyklační příspěvek" / "Příspěvek na recyklaci" and explicitly NOT any
# phrase with "poplatek". Slovak: § 34 ods. 1 písm. d) and § 37 ods. 1 písm. a)
# zákona č. 79/2015 Z. z. call it "recyklačný poplatok".
STATUTORY_PHRASES = {
    "CZ": {
        "included": "z toho recyklační příspěvek",
        "on_top": "recyklační příspěvek (samostatná položka)",
        "total": "Recyklační příspěvek celkem bez DPH",
        "piece": "ks",
        "without_vat": "bez DPH",
        "fx": "kurz",
        "fee_line": "Recyklační příspěvek",
    },
    "SK": {
        "included": "z toho recyklačný poplatok",
        "on_top": "recyklačný poplatok (samostatná položka)",
        "total": "Recyklačný poplatok spolu bez DPH",
        "piece": "ks",
        "without_vat": "bez DPH",
        "fx": "kurz",
        "fee_line": "Recyklačný poplatok",
    },
}


class AccountEcotaxClassification(models.Model):
    _inherit = "account.ecotax.classification"

    country_id = fields.Many2one(
        "res.country",
        string="Scheme Country",
        help="Market whose take-back law the fee belongs to (CZ or SK). A "
        "classification with a country is a statutory recycling fee: it is "
        "priced from the dated rates below, applied only by companies whose "
        "fiscal country matches, and printed with that country's statutory "
        "wording. Without a country the classification behaves exactly as in "
        "OCA account_ecotax.",
    )
    currency_id = fields.Many2one(
        "res.currency",
        compute="_compute_currency_id",
        store=True,
        readonly=False,
        help="Currency of the rates: the currency the scheme bills the "
        "producer in. Invoices in another currency convert at the invoice "
        "date and print the original amount and the rate used.",
    )
    rate_ids = fields.One2many(
        "account.ecotax.classification.rate",
        "classification_id",
        string="Rates",
        copy=True,
    )
    disclose = fields.Boolean(
        string="Show on Documents",
        default=True,
        help="Uncheck for portable batteries: separate disclosure of their "
        "take-back cost is PROHIBITED (CZ § 85 odst. 3 zákona č. 542/2020 Sb.; "
        "SK § 46 ods. 2 and § 48 ods. 1 písm. d) zákona č. 79/2015 Z. z.). The "
        "fee is still computed, kept in the price and reported to the scheme; "
        "it is only never printed.",
    )

    @api.depends("country_id")
    def _compute_currency_id(self):
        for classification in self:
            classification.currency_id = (
                classification.country_id.currency_id
                or classification.company_id.currency_id
                or self.env.company.currency_id
            )

    @api.depends("rate_ids.amount", "rate_ids.date_from", "rate_ids.date_to")
    def _compute_ecotax_vals(self):
        """Mirror today's dated rate into OCA's single-amount fields.

        OCA prices products (``ecotax.line.product``, ``product.ecotax_amount``)
        from ``default_fixed_ecotax`` / ``ecotax_coef``. Keeping those in step
        with the rate in force makes every OCA screen show the current fee,
        while documents never read them — they choose the rate by their own
        date (see ``ecotax.line.mixin``). A daily cron rolls the mirror over
        when a new rate starts.
        """
        res = super()._compute_ecotax_vals()
        today = fields.Date.context_today(self)
        for classification in self.filtered("rate_ids"):
            amount = classification._get_rate(today).amount
            if classification.ecotax_type == "weight_based":
                classification.ecotax_coef = amount
            else:
                classification.default_fixed_ecotax = amount
        return res

    def _get_rate(self, date):
        """Return the rate valid on ``date`` (an empty recordset if none)."""
        self.ensure_one()
        return self.rate_ids.filtered(
            lambda r: r.date_from <= date and (not r.date_to or r.date_to >= date)
        )[:1]

    def _applies_to_company(self, company):
        """A statutory classification applies only on its own market, and a
        company-bound classification only in its company."""
        self.ensure_one()
        if self.company_id and self.company_id != company:
            return False
        return not self.country_id or self.country_id == (
            company.account_fiscal_country_id or company.country_id
        )

    def _statutory_phrases(self):
        self.ensure_one()
        return STATUTORY_PHRASES.get(self.country_id.code)

    @api.model
    def _cron_refresh_current_rate(self):
        """Roll the OCA mirror fields over to the rate that starts today."""
        classifications = self.with_context(active_test=False).search(
            [("rate_ids", "!=", False)]
        )
        today = fields.Date.context_today(self)
        for classification in classifications:
            amount = classification._get_rate(today).amount
            field = (
                "ecotax_coef"
                if classification.ecotax_type == "weight_based"
                else "default_fixed_ecotax"
            )
            if classification[field] != amount:
                classification[field] = amount
