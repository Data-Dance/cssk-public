# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""ČNB's actual daily fixings, kept beside a fixed monthly rate.

A company using a fixed rate (pevný kurz, § 24 odst. 6 ZoÚ, and for VAT § 38
ZDPH) books every document of a month at one rate, which is what the ordinary
rate table then holds. The balance-sheet date is the exception: open items and
foreign-currency accounts are revalued at ČNB's rate OF THAT DAY, not at the
fixed one. Those rates live here, where no document picks them up, and are
read only when a caller asks for them with the context key
``cssk_actual_rates`` — the Czech revaluation does.
"""

from odoo import api, fields, models


class CsskCurrencyRateActual(models.Model):
    _name = "cssk.currency.rate.actual"
    _description = "Actual ČNB rate (beside a fixed monthly rate)"
    _order = "name desc"

    name = fields.Date(string="Date", required=True, index=True)
    currency_id = fields.Many2one("res.currency", required=True, index=True)
    company_id = fields.Many2one("res.company", index=True)
    rate = fields.Float(
        digits=0, required=True,
        help="Units of the currency per unit of the company currency, as on "
        "res.currency.rate.")

    _day_uniq = models.Constraint(
        "UNIQUE (name, currency_id, company_id)",
        "One actual rate per currency, company and day.")


class ResCurrency(models.Model):
    _inherit = "res.currency"

    def _get_rates(self, company, date):
        rates = super()._get_rates(company, date)
        if not self.env.context.get("cssk_actual_rates"):
            return rates
        Actual = self.env["cssk.currency.rate.actual"].sudo()
        root = company.root_id
        for currency in self:
            actual = Actual.search([
                ("currency_id", "=", currency.id),
                ("company_id", "in", (False, root.id)),
                ("name", "<=", date),
            ], order="company_id, name desc", limit=1)
            if actual:
                rates[currency.id] = actual.rate
        return rates

    # The conversion goes through the cached inverse_rate compute; a context
    # key it does not declare would be served a value computed without it.
    @api.depends_context("to_currency", "date", "company", "company_id",
                         "cssk_actual_rates")
    def _compute_current_rate(self):
        return super()._compute_current_rate()
