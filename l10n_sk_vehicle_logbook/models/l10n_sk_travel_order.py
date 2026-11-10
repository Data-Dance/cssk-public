# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from .. import travel_rules


class L10nSkTravelOrder(models.Model):
    _name = "l10n.sk.travel.order"
    _description = "Travel order"
    _inherit = ["mail.thread"]
    _order = "date_start desc, id desc"

    name = fields.Char(default="/", copy=False, readonly=True)
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    employee_id = fields.Many2one("hr.employee", required=True, tracking=True)
    date_start = fields.Datetime(string="Departure", required=True)
    date_end = fields.Datetime(string="Return", required=True)
    destination = fields.Char(required=True)
    trip_kind = fields.Selection(
        [("domestic", "Domestic"), ("foreign", "Foreign")],
        string="Domestic or foreign", required=True, default="domestic",
    )
    border_out = fields.Datetime(
        string="Leaves Slovakia",
        help="Crossing of the Slovak border, or the scheduled departure of the "
             "flight (§ 16 ods. 2 zákona 283/2002 Z. z.).",
    )
    border_in = fields.Datetime(
        string="Returns to Slovakia",
        help="Crossing of the Slovak border, or the scheduled arrival of the flight.",
    )
    stay_ids = fields.One2many("l10n.sk.travel.order.stay", "order_id", string="Countries")
    road_transport = fields.Boolean(
        string="Mobile worker in road transport",
        help="Uses the special base rates of § 1a opatrenia 401/2012 Z. z. where "
             "a country has one (§ 13 ods. 2 druhá veta).",
    )
    pocket_money_percent = fields.Float(
        string="Pocket money (%)",
        help="§ 14: optional, up to 40 % of the foreign meal allowance.",
    )
    purpose = fields.Char(required=True)
    state = fields.Selection(
        [("draft", "Draft"), ("approved", "Approved"), ("settled", "Settled")],
        default="draft", required=True, tracking=True, copy=False,
    )
    vehicle_mode = fields.Selection(
        [("none", "Public transport or company vehicle"), ("own", "Employee's own vehicle")],
        required=True, default="none",
    )
    vehicle_category = fields.Selection(
        [("car", "Passenger car"), ("two_wheel", "Two- or three-wheeler, quad")],
        default="car",
    )
    trailer = fields.Boolean(help="§ 7 ods. 2: a trailer adds 15 % to the basic rate.")
    kilometres = fields.Float(help="Filled from the linked logbook trips when there are any.")
    consumption = fields.Float(
        string="Consumption (per 100 km)",
        help="Consumption from the vehicle document including the increase "
             "under § 7 ods. 6 zákona 283/2002 Z. z.",
    )
    fuel_price = fields.Float(
        digits=(8, 3), help="Unit price from the purchase receipt (§ 7 ods. 5)."
    )
    advance = fields.Monetary()
    trip_ids = fields.One2many("l10n.sk.vehicle.trip", "travel_order_id")
    day_ids = fields.One2many("l10n.sk.travel.order.day", "order_id", copy=False)
    expense_id = fields.Many2one("hr.expense", readonly=True, copy=False)
    meal_amount = fields.Monetary(compute="_compute_amounts", store=True)
    kilometre_amount = fields.Monetary(compute="_compute_amounts", store=True)
    fuel_amount = fields.Monetary(compute="_compute_amounts", store=True)
    total_amount = fields.Monetary(compute="_compute_amounts", store=True)
    amount_due = fields.Monetary(compute="_compute_amounts", store=True)

    @api.constrains("date_start", "date_end", "trip_kind", "border_out", "border_in")
    def _check_dates(self):
        for order in self:
            if order.date_end <= order.date_start:
                raise ValidationError(_("The return must be after the departure."))
            if order.trip_kind != "foreign":
                continue
            if not (order.border_out and order.border_in):
                raise ValidationError(
                    _("A foreign trip needs the times it leaves and returns to Slovakia.")
                )
            if not (
                order.date_start <= order.border_out < order.border_in <= order.date_end
            ):
                raise ValidationError(
                    _("The time abroad must lie within the trip and leaving must "
                      "precede returning.")
                )

    @api.constrains("pocket_money_percent")
    def _check_pocket_money(self):
        for order in self:
            if not 0 <= order.pocket_money_percent <= 40:
                raise ValidationError(_("Pocket money is at most 40 % (§ 14)."))

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        for order in orders:
            if order.name == "/":
                order.name = self.env["ir.sequence"].with_company(
                    order.company_id
                ).next_by_code("l10n.sk.travel.order") or "/"
        return orders

    def _rate(self, day=None):
        self.ensure_one()
        day = day or fields.Date.to_date(self.date_start)
        rate = self.env["l10n.sk.travel.rate"]._for_date(day)
        if not rate:
            raise UserError(_("No travel rates are valid on %(day)s.", day=day))
        return rate

    @api.depends(
        "day_ids.amount", "vehicle_mode", "vehicle_category", "trailer",
        "kilometres", "consumption", "fuel_price", "advance", "date_start",
    )
    def _compute_amounts(self):
        for order in self:
            meals = sum(order.day_ids.mapped("amount"))
            km_amount = fuel = 0.0
            if order.vehicle_mode == "own" and order.date_start:
                rate = order._rate()
                km_rate = rate.km_car if order.vehicle_category == "car" else rate.km_two_wheel
                km_amount = travel_rules.kilometre_allowance(
                    order.kilometres, km_rate, order.trailer
                )
                fuel = travel_rules.fuel_allowance(
                    order.kilometres, order.consumption, order.fuel_price
                )
            order.meal_amount = meals
            order.kilometre_amount = km_amount
            order.fuel_amount = fuel
            order.total_amount = meals + km_amount + fuel
            order.amount_due = order.total_amount - order.advance

    def action_compute_days(self):
        """Rebuild the calendar days, keeping meals already ticked."""
        for order in self:
            kept = {
                d.date: (d.breakfast, d.lunch, d.dinner) for d in order.day_ids
            }
            values = []
            for day, (home_hours, abroad) in order._split_days().items():
                # § 5 amounts change mid-year (280/2025 from 1. 12. 2025), so
                # each day takes the set in force on that day.
                rate = order._rate(day)
                breakfast, lunch, dinner = kept.get(day, (False, False, False))
                vals = {
                    "order_id": order.id,
                    "date": day,
                    "hours": home_hours,
                    "rate": travel_rules.meal_rate(
                        home_hours, rate.meal_5_12, rate.meal_12_18, rate.meal_18
                    ),
                    "rate_18": rate.meal_18,
                    "breakfast": breakfast,
                    "lunch": lunch,
                    "dinner": dinner,
                }
                if abroad:
                    vals.update(order._foreign_day_values(day, abroad))
                    vals["meals_abroad"] = vals["hours_abroad"] >= home_hours
                values.append(vals)
            order.day_ids.unlink()
            self.env["l10n.sk.travel.order.day"].create(values)
            if order.trip_ids:
                order.kilometres = sum(order.trip_ids.mapped("distance"))

    def _split_days(self):
        """``{date: (home hours, {stay: hours abroad})}`` for every calendar day."""
        self.ensure_one()
        if self.trip_kind != "foreign":
            return {
                day: (hours, {})
                for day, hours in travel_rules.hours_by_local_day(
                    self.date_start, self.date_end
                ).items()
            }
        if not self.stay_ids:
            raise UserError(_("Add the countries the trip goes to."))
        stays = self.stay_ids.sorted(lambda s: (bool(s.date_arrival), s.date_arrival or s.id))
        for stay in stays[1:]:
            if not stay.date_arrival:
                raise UserError(_(
                    "Only the first country may go without an arrival time; "
                    "enter when the trip reached %(country)s.",
                    country=stay.country_id.name,
                ))
            if not self.border_out < stay.date_arrival < self.border_in:
                raise UserError(_(
                    "The arrival in %(country)s must lie between leaving and "
                    "returning to Slovakia.",
                    country=stay.country_id.name,
                ))
        # Keyed by country, so a country visited twice in one day adds up
        # its hours for § 13 ods. 5.
        return travel_rules.split_foreign_trip(
            self.date_start, self.date_end, self.border_out, self.border_in,
            [(stay.date_arrival or self.border_out, stay.country_id) for stay in stays],
        )

    def _conversion_date(self):
        """§ 36 ods. 6: the rate valid on the first day of the month the trip began."""
        start = fields.Date.to_date(self.date_start)
        return date(start.year, start.month, 1)

    def _conversion_rate(self, currency):
        """Company currency per unit of ``currency``, refusing to guess one."""
        self.ensure_one()
        company_currency = self.currency_id
        if currency == company_currency:
            return 1.0
        day = self._conversion_date()
        known = self.env["res.currency.rate"].search_count([
            ("currency_id", "=", currency.id),
            ("name", "<=", day),
            ("company_id", "in", [False, self.company_id.id]),
        ])
        if not known:
            raise UserError(_(
                "No %(currency)s exchange rate is known on %(day)s, the first day "
                "of the month the trip began (§ 36 ods. 6 zákona 283/2002 Z. z.). "
                "Activate the currency and load the ECB or NBS rates.",
                currency=currency.name, day=day,
            ))
        return currency._get_conversion_rate(
            currency, company_currency, self.company_id, day
        )

    def _foreign_day_values(self, day, abroad):
        """Rate and amounts of the country that decides the day (§ 13 ods. 5)."""
        self.ensure_one()
        rates = {}
        for country in abroad:
            rate = self.env["l10n.sk.travel.foreign.rate"]._for(country, day)
            if not rate:
                raise UserError(_(
                    "No foreign meal rate for %(country)s is valid on %(day)s.",
                    country=country.name, day=day,
                ))
            base = rate._base(self.road_transport)
            rates[country] = (rate, base, base * self._conversion_rate(rate.currency_id))
        country = travel_rules.decisive_country(abroad, lambda key: rates[key][2])
        rate, base, _value = rates[country]
        hours_abroad = sum(abroad.values())
        return {
            "hours_abroad": hours_abroad,
            "country_id": country.id,
            "foreign_currency_id": rate.currency_id.id,
            "foreign_base": base,
            "foreign_rate": self._conversion_rate(rate.currency_id),
            "pocket_money": travel_rules.pocket_money(
                base, hours_abroad, self.pocket_money_percent
            ),
        }

    def action_approve(self):
        for order in self:
            if not order.day_ids:
                order.action_compute_days()
        self.state = "approved"

    def action_draft(self):
        if self.expense_id:
            raise UserError(_("This order already has an expense."))
        self.state = "draft"

    def action_settle(self):
        """Hand the amount due to the expense approval flow."""
        product = self.env.ref("l10n_sk_vehicle_logbook.product_travel_settlement")
        for order in self:
            if order.state != "approved":
                raise UserError(_("Only an approved order can be settled."))
            if order.currency_id.compare_amounts(order.amount_due, 0.0) > 0:
                order.expense_id = self.env["hr.expense"].create({
                    "name": order.name,
                    "employee_id": order.employee_id.id,
                    "company_id": order.company_id.id,
                    "product_id": product.id,
                    "payment_mode": "own_account",
                    "date": fields.Date.to_date(order.date_end),
                    "total_amount_currency": order.amount_due,
                })
            order.state = "settled"


class L10nSkTravelOrderDay(models.Model):
    _name = "l10n.sk.travel.order.day"
    _description = "Travel order calendar day"
    _order = "date"

    order_id = fields.Many2one("l10n.sk.travel.order", required=True, ondelete="cascade")
    currency_id = fields.Many2one(related="order_id.currency_id")
    date = fields.Date(required=True)
    hours = fields.Float(string="Hours in Slovakia", readonly=True)
    hours_abroad = fields.Float(readonly=True)
    country_id = fields.Many2one("res.country", readonly=True)
    foreign_currency_id = fields.Many2one("res.currency", readonly=True)
    foreign_base = fields.Float(string="Base rate", digits=(10, 2), readonly=True)
    foreign_rate = fields.Float(
        string="Exchange rate", digits=(16, 8), readonly=True,
        help="Company currency per unit, valid on the first day of the month "
             "the trip began (§ 36 ods. 6).",
    )
    pocket_money = fields.Float(digits=(10, 2), readonly=True)
    meals_abroad = fields.Boolean(
        help="The free meals of this day were abroad, so they cut the foreign "
             "allowance (§ 13 ods. 7) instead of the domestic one (§ 5 ods. 6).",
    )
    foreign_amount = fields.Float(
        string="Foreign meals", digits=(10, 2), compute="_compute_amount", store=True,
    )
    rate = fields.Float(digits=(6, 2), readonly=True)
    rate_18 = fields.Float(digits=(6, 2), readonly=True)
    breakfast = fields.Boolean(string="Free breakfast")
    lunch = fields.Boolean(string="Free lunch")
    dinner = fields.Boolean(string="Free dinner")
    amount = fields.Monetary(compute="_compute_amount", store=True)

    @api.depends(
        "rate", "rate_18", "breakfast", "lunch", "dinner", "meals_abroad",
        "hours_abroad", "foreign_base", "foreign_rate", "pocket_money",
    )
    def _compute_amount(self):
        for day in self:
            meals = (day.breakfast, day.lunch, day.dinner)
            abroad = bool(day.foreign_base) and day.meals_abroad
            domestic = travel_rules.meal_allowance(
                day.rate, day.rate_18, *((False,) * 3 if abroad else meals)
            )
            foreign = travel_rules.foreign_meal_allowance(
                day.foreign_base, day.hours_abroad, *(meals if abroad else (False,) * 3)
            ) if day.foreign_base else 0.0
            day.foreign_amount = foreign
            day.amount = domestic + travel_rules._cents(
                (foreign + day.pocket_money) * (day.foreign_rate or 1.0)
            )


class L10nSkTravelOrderStay(models.Model):
    _name = "l10n.sk.travel.order.stay"
    _description = "Country visited on a foreign trip"
    _order = "date_arrival, id"

    order_id = fields.Many2one("l10n.sk.travel.order", required=True, ondelete="cascade")
    country_id = fields.Many2one("res.country", required=True)
    date_arrival = fields.Datetime(
        string="Arrival",
        help="When the trip enters this country. Empty on the first country "
             "means the moment it leaves Slovakia.",
    )
