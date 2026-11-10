# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class L10nSkTravelRate(models.Model):
    _name = "l10n.sk.travel.rate"
    _description = "Slovak domestic travel rates"
    _order = "date_from desc"
    _rec_name = "date_from"

    date_from = fields.Date(string="Valid from", required=True)
    meal_5_12 = fields.Float(string="Meals, 5 to 12 hours", digits=(6, 2), required=True)
    meal_12_18 = fields.Float(string="Meals, over 12 to 18 hours", digits=(6, 2), required=True)
    meal_18 = fields.Float(string="Meals, over 18 hours", digits=(6, 2), required=True)
    km_car = fields.Float(string="Per km, passenger car", digits=(6, 3), required=True)
    km_two_wheel = fields.Float(
        string="Per km, two- and three-wheelers, quads", digits=(6, 3), required=True
    )
    source = fields.Char(help="The published notice these amounts come from.")

    _date_from_uniq = models.Constraint(
        "UNIQUE (date_from)", "One set of rates per start date."
    )

    def _for_date(self, day):
        return self.search([("date_from", "<=", day)], limit=1)


class L10nSkTravelForeignRate(models.Model):
    _name = "l10n.sk.travel.foreign.rate"
    _description = "Slovak foreign meal allowance rates"
    _order = "country_id, date_from desc"
    _rec_name = "country_id"

    date_from = fields.Date(string="Valid from", required=True)
    country_id = fields.Many2one("res.country", required=True, index=True)
    currency_id = fields.Many2one("res.currency", required=True)
    rate = fields.Float(
        string="Base rate", digits=(10, 2), required=True,
        help="Základná sadzba stravného, § 13 ods. 2 zákona 283/2002 Z. z.",
    )
    special_rate = fields.Float(
        string="Road transport rate", digits=(10, 2),
        help="Osobitná základná sadzba stravného for mobile workers in road "
             "transport (§ 13 ods. 2 druhá veta); empty where none is set.",
    )
    source = fields.Char(help="The published notice these amounts come from.")

    _country_date_uniq = models.Constraint(
        "UNIQUE (country_id, date_from)", "One rate per country and start date."
    )

    def _for(self, country, day):
        return self.search(
            [("country_id", "=", country.id), ("date_from", "<=", day)], limit=1
        )

    def _base(self, road_transport):
        """The rate that applies; a special rate replaces the basic one."""
        self.ensure_one()
        return self.special_rate if road_transport and self.special_rate else self.rate
