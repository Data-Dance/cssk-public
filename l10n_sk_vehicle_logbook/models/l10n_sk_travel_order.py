# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from .. import travel_rules


class L10nSkTravelOrder(models.Model):
    _name = "l10n.sk.travel.order"
    _description = "Domestic travel order"
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

    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        for order in self:
            if order.date_end <= order.date_start:
                raise ValidationError(_("The return must be after the departure."))

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        for order in orders:
            if order.name == "/":
                order.name = self.env["ir.sequence"].with_company(
                    order.company_id
                ).next_by_code("l10n.sk.travel.order") or "/"
        return orders

    def _rate(self):
        self.ensure_one()
        day = fields.Date.to_date(self.date_start)
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
            rate = order._rate()
            order.day_ids.unlink()
            values = []
            hours = travel_rules.hours_by_local_day(order.date_start, order.date_end)
            for day, day_hours in hours.items():
                breakfast, lunch, dinner = kept.get(day, (False, False, False))
                values.append({
                    "order_id": order.id,
                    "date": day,
                    "hours": day_hours,
                    "rate": travel_rules.meal_rate(
                        day_hours, rate.meal_5_12, rate.meal_12_18, rate.meal_18
                    ),
                    "rate_18": rate.meal_18,
                    "breakfast": breakfast,
                    "lunch": lunch,
                    "dinner": dinner,
                })
            self.env["l10n.sk.travel.order.day"].create(values)
            if order.trip_ids:
                order.kilometres = sum(order.trip_ids.mapped("distance"))

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
    hours = fields.Float(readonly=True)
    rate = fields.Float(digits=(6, 2), readonly=True)
    rate_18 = fields.Float(digits=(6, 2), readonly=True)
    breakfast = fields.Boolean(string="Free breakfast")
    lunch = fields.Boolean(string="Free lunch")
    dinner = fields.Boolean(string="Free dinner")
    amount = fields.Monetary(compute="_compute_amount", store=True)

    @api.depends("rate", "rate_18", "breakfast", "lunch", "dinner")
    def _compute_amount(self):
        for day in self:
            day.amount = travel_rules.meal_allowance(
                day.rate, day.rate_18, day.breakfast, day.lunch, day.dinner
            )
