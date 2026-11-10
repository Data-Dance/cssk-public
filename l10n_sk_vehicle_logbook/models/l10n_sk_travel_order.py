# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import date, datetime, time, timedelta

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from .. import travel_rules

# What the employee may still change once the order is approved: the trip as
# it actually went (§ 36 ods. 7 settlement). Everything else is the order the
# employer set in writing before the trip (§ 3) and stays as approved.
ACTUAL_FIELDS = {
    "date_start", "date_end", "border_out", "border_in", "stay_ids", "day_ids",
    "kilometres", "consumption", "fuel_price", "fuel_line_ids", "trip_ids",
    "expense_ids",
}
# Set only by the process methods, never by a client: writing them directly
# would skip the approval.
PROCESS_FIELDS = {
    "state", "approved_by_id", "approval_date", "planned_date_start",
    "planned_date_end", "reported_date", "settled_by_id", "settlement_date",
    "report_deadline", "advance_expense_id", "expense_id",
}
SETTLEMENT_DEADLINE_DAYS = 10  # § 36 ods. 7 and 8 zákona 283/2002 Z. z.
# When a free meal is usually eaten, Slovak time: the default for whether it
# was provided at home or abroad on a day the border is crossed. The
# employee corrects it where the trip went otherwise.
MEAL_TIMES = {"breakfast": time(8), "lunch": time(12), "dinner": time(18)}


def _working_days_after(calendar, moment, days):
    """The date ``days`` working days after the day of ``moment``.

    The deadline runs from the day after the event, so the count starts at
    the next midnight. Without a calendar, Monday to Friday count.
    """
    tz = pytz.timezone(calendar.tz if calendar and calendar.tz else "Europe/Bratislava")
    local = pytz.utc.localize(moment).astimezone(tz)
    start = tz.localize(datetime.combine(local.date() + timedelta(days=1), time.min))
    if calendar:
        end = calendar.plan_days(days, start, compute_leaves=True)
        if end:
            return end.astimezone(tz).date()
    day, found = start.date(), 0
    while True:
        if day.weekday() < 5:
            found += 1
            if found == days:
                return day
        day += timedelta(days=1)


class L10nSkTravelOrder(models.Model):
    _name = "l10n.sk.travel.order"
    _description = "Travel order"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_start desc, id desc"

    name = fields.Char(default="/", copy=False, readonly=True)
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    employee_id = fields.Many2one(
        "hr.employee", required=True, tracking=True, index=True,
        default=lambda self: self.env.user.employee_id,
    )
    user_id = fields.Many2one(related="employee_id.user_id", string="Employee user")
    department_id = fields.Many2one(related="employee_id.department_id", store=True)
    manager_id = fields.Many2one(
        "res.users", string="Approver", tracking=True, copy=False, index=True,
        help="Who approves the order and its settlement. Filled on submission "
             "from the employee's expense approver, department manager or "
             "manager, as for expenses.",
    )
    date_start = fields.Datetime(string="Departure", required=True)
    date_end = fields.Datetime(string="Return", required=True)
    planned_date_start = fields.Datetime(
        string="Planned departure", readonly=True, copy=False,
        help="The departure as approved, before the trip (§ 3).",
    )
    planned_date_end = fields.Datetime(string="Planned return", readonly=True, copy=False)
    origin = fields.Char(
        string="Place of departure",
        help="Where the trip starts and ends; usually the regular workplace.",
    )
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
        [
            ("draft", "Draft"),
            ("submitted", "To Approve"),
            ("approved", "Approved"),
            ("reported", "Settlement to Approve"),
            ("settled", "Settled"),
            ("refused", "Refused"),
            ("cancel", "Cancelled"),
        ],
        default="draft", required=True, tracking=True, copy=False, index=True,
    )
    approved_by_id = fields.Many2one("res.users", readonly=True, copy=False)
    approval_date = fields.Datetime(readonly=True, copy=False)
    reported_date = fields.Datetime(
        string="Settlement submitted", readonly=True, copy=False,
    )
    settled_by_id = fields.Many2one("res.users", readonly=True, copy=False)
    settlement_date = fields.Datetime(readonly=True, copy=False)
    report_deadline = fields.Date(
        string="Settle by", readonly=True, copy=False,
        help="10 working days after the return (§ 36 ods. 7 zákona "
             "283/2002 Z. z.): the employee hands in the documents and returns "
             "the unused advance.",
    )
    can_approve = fields.Boolean(compute="_compute_can_approve")
    is_traveller = fields.Boolean(
        compute="_compute_is_traveller",
        help="The current user travels on this order or is an expense officer.",
    )
    vehicle_mode = fields.Selection(
        [("none", "Public transport or company vehicle"), ("own", "Employee's own vehicle")],
        string="Transport", required=True, default="none",
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
        digits=(8, 3), help="Unit price from the purchase receipt (§ 7 ods. 5). "
        "Used when the order has no fuel lines.",
    )
    fuel_line_ids = fields.One2many(
        "l10n.sk.travel.order.fuel", "order_id", string="Fuel",
        help="Fuel reimbursement by part of the trip, each at its own unit "
             "price and currency: abroad at the price on the foreign receipt "
             "(§ 15 zákona 283/2002 Z. z.). Replaces the single fuel price.",
    )
    fuel_km_mismatch = fields.Boolean(compute="_compute_fuel_km_mismatch")
    advance = fields.Monetary(
        help="Requested advance. Approving the order creates it as an approved "
             "employee advance for accounting to pay out; the settlement clears "
             "it. Mandatory on a foreign trip unless the employee declines "
             "(§ 36 ods. 1).",
    )
    advance_expense_id = fields.Many2one(
        "hr.expense", string="Advance expense", readonly=True, copy=False,
    )
    advance_state = fields.Selection(
        related="advance_expense_id.state", string="Advance status", tracking=False,
    )
    advance_residual = fields.Monetary(
        related="advance_expense_id.clearing_residual", string="Advance to clear",
    )
    trip_ids = fields.One2many("l10n.sk.vehicle.trip", "travel_order_id")
    day_ids = fields.One2many("l10n.sk.travel.order.day", "order_id", copy=False)
    expense_ids = fields.One2many(
        "hr.expense", "l10n_sk_travel_order_id", string="Other costs",
        domain=[("advance", "=", False), ("l10n_sk_travel_allowance", "=", False)],
        help="Tickets, accommodation, parking and other costs of the trip, "
             "each with its receipt. They are approved with the settlement.",
    )
    expense_id = fields.Many2one(
        "hr.expense", string="Allowance expense", readonly=True, copy=False,
    )
    meal_amount = fields.Monetary(
        string="Meals and pocket money", compute="_compute_amounts", store=True,
    )
    kilometre_amount = fields.Monetary(compute="_compute_amounts", store=True)
    fuel_amount = fields.Monetary(compute="_compute_amounts", store=True)
    allowance_amount = fields.Monetary(
        string="Allowances", compute="_compute_amounts", store=True,
    )
    other_amount = fields.Monetary(
        string="Other costs total", compute="_compute_amounts", store=True,
    )
    total_amount = fields.Monetary(compute="_compute_amounts", store=True)
    amount_due = fields.Monetary(
        compute="_compute_amounts", store=True,
        help="Total less the advance: positive is paid to the employee, "
             "negative is returned by the employee.",
    )

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

    def _check_process_fields(self, vals):
        if self.env.su:
            return
        forced = PROCESS_FIELDS & set(vals)
        # The approver comes from the HR data; letting the traveller pick one
        # would let them choose who approves their own trip.
        if "manager_id" in vals and not self._is_expense_officer():
            forced.add("manager_id")
        if forced:
            raise AccessError(_(
                "%(fields)s change only through the travel order's buttons.",
                fields=", ".join(
                    self._fields[f]._description_string(self.env) for f in sorted(forced)
                ),
            ))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals = {k: v for k, v in vals.items() if not (k == "state" and v == "draft")}
            self._check_process_fields(vals)
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
        "expense_ids.total_amount", "expense_ids.payment_mode",
        "fuel_line_ids.amount", "fuel_line_ids.currency_id",
    )
    def _compute_amounts(self):
        for order in self:
            costs = order.expense_ids
            own_costs = sum(
                costs.filtered(lambda e: e.payment_mode == "own_account").mapped("total_amount")
            )
            order.other_amount = sum(costs.mapped("total_amount"))
            meals = sum(order.day_ids.mapped("amount"))
            km_amount = fuel = 0.0
            if order.vehicle_mode == "own" and order.date_start:
                rate = order._rate()
                km_rate = rate.km_car if order.vehicle_category == "car" else rate.km_two_wheel
                km_amount = travel_rules.kilometre_allowance(
                    order.kilometres, km_rate, order.trailer
                )
                if order.fuel_line_ids:
                    fuel = sum(
                        travel_rules._cents(
                            line.amount * order._conversion_rate(line.currency_id)
                        )
                        for line in order.fuel_line_ids
                    )
                else:
                    fuel = travel_rules.fuel_allowance(
                        order.kilometres, order.consumption, order.fuel_price
                    )
            order.meal_amount = meals
            order.kilometre_amount = km_amount
            order.fuel_amount = fuel
            order.allowance_amount = meals + km_amount + fuel
            order.total_amount = order.allowance_amount + order.other_amount
            # Costs the company paid directly are not owed to the employee.
            order.amount_due = order.allowance_amount + own_costs - order.advance

    @api.depends("fuel_line_ids.kilometres", "kilometres", "vehicle_mode")
    def _compute_fuel_km_mismatch(self):
        for order in self:
            lines = order.fuel_line_ids
            order.fuel_km_mismatch = bool(lines) and order.vehicle_mode == "own" and (
                round(sum(lines.mapped("kilometres")), 2) != round(order.kilometres, 2)
            )

    def _meal_abroad_default(self, day, meal):
        """Whether ``meal`` of ``day`` falls in the time abroad, by MEAL_TIMES."""
        self.ensure_one()
        if self.trip_kind != "foreign" or not (self.border_out and self.border_in):
            return False
        moment = travel_rules.TIMEZONE.localize(datetime.combine(day, MEAL_TIMES[meal]))
        moment = moment.astimezone(pytz.utc).replace(tzinfo=None)
        return self.border_out <= moment < self.border_in

    def action_compute_days(self):
        """Rebuild the calendar days, keeping meals already ticked."""
        meals = ("breakfast", "lunch", "dinner")
        for order in self:
            kept = {
                d.date: {f: d[f] for m in meals for f in (m, f"{m}_abroad")}
                for d in order.day_ids
            }
            values = []
            for day, (home_hours, abroad) in order._split_days().items():
                # § 5 amounts change mid-year (280/2025 from 1. 12. 2025), so
                # each day takes the set in force on that day.
                rate = order._rate(day)
                vals = {
                    "order_id": order.id,
                    "date": day,
                    "hours": home_hours,
                    "rate": travel_rules.meal_rate(
                        home_hours, rate.meal_5_12, rate.meal_12_18, rate.meal_18
                    ),
                    "rate_18": rate.meal_18,
                }
                if abroad:
                    vals.update(order._foreign_day_values(day, abroad))
                if day in kept:
                    vals.update(kept[day])
                else:
                    vals.update({
                        f"{meal}_abroad": bool(abroad) and order._meal_abroad_default(day, meal)
                        for meal in meals
                    })
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

    # ------------------------------------------------------------------
    # Who may do what
    # ------------------------------------------------------------------

    def _is_expense_officer(self):
        return self.env.su or self.env.user.has_group("hr_expense.group_hr_expense_user")

    def _get_cannot_approve_reason(self):
        """``{order id: reason or False}``, modelled on hr.expense's own check.

        Unlike expenses, nobody approves their own trip, not even an expense
        manager: the order is the employer's instruction to the employee.
        """
        user = self.env.user
        officer = self._is_expense_officer()
        team_approver = user.has_group("hr_expense.group_hr_expense_team_approver")
        subordinates = set()
        if team_approver and user.employee_ids:
            subordinates = set(self.env["hr.employee"].sudo().search([
                ("id", "in", self.employee_id.ids),
                ("id", "child_of", user.employee_ids.ids),
                ("id", "not in", user.employee_ids.ids),
            ]).ids)
        reasons = {}
        for order in self:
            employee = order.employee_id.sudo()
            reason = False
            if self.env.su:
                pass
            elif employee.user_id == user:
                reason = _("%(order)s: it is your own trip.", order=order.name)
            elif order.company_id not in self.env.companies:
                reason = _("%(order)s: not a company you work in.", order=order.name)
            elif not officer and user not in (
                order.manager_id
                | employee.expense_manager_id
                | employee.department_id.manager_id.user_id
            ) and employee.id not in subordinates:
                reason = _(
                    "%(order)s: you are neither its approver nor an expense officer.",
                    order=order.name,
                )
            reasons[order.id] = reason
        return reasons

    @api.depends_context("uid")
    @api.depends("employee_id", "manager_id", "company_id")
    def _compute_can_approve(self):
        reasons = self._get_cannot_approve_reason()
        for order in self:
            order.can_approve = not reasons.get(order.id)

    @api.depends_context("uid")
    @api.depends("employee_id")
    def _compute_is_traveller(self):
        officer = self._is_expense_officer()
        for order in self:
            order.is_traveller = officer or order.employee_id.sudo().user_id == self.env.user

    def _check_can_approve(self):
        reasons = [r for r in self._get_cannot_approve_reason().values() if r]
        if reasons:
            raise AccessError("\n".join(reasons))

    def _check_is_traveller_or_officer(self):
        """Submitting is for the employee who travels, or an expense officer
        acting for them."""
        if self._is_expense_officer():
            return
        for order in self:
            if order.employee_id.sudo().user_id != self.env.user:
                raise AccessError(_(
                    "%(order)s: only the employee or an expense officer can do this.",
                    order=order.name,
                ))

    def _check_state(self, *states):
        for order in self:
            if order.state not in states:
                raise UserError(_(
                    "%(order)s is %(state)s; this step is not available.",
                    order=order.name,
                    state=dict(self._fields["state"]._description_selection(self.env))[order.state],
                ))

    def _default_approver(self):
        """The expense approver, the department manager or the manager, as
        hr.expense resolves it, never the employee themself."""
        self.ensure_one()
        employee = self.employee_id.sudo()
        candidates = (
            employee.expense_manager_id,
            employee.department_id.manager_id.user_id,
            employee.parent_id.user_id,
        )
        for user in candidates:
            user = user - employee.user_id
            if user:
                return user
        return self.env["res.users"]

    def write(self, vals):
        self._check_process_fields(vals)
        if not (self.env.su):
            changed = {
                field for field in vals
                if field in self._fields
                and not field.startswith(("message_", "activity_"))
            }
            for order in self:
                if order.state == "draft":
                    continue
                allowed = set()
                if order.state == "approved" and (
                    self._is_expense_officer()
                    or order.employee_id.sudo().user_id == self.env.user
                ):
                    allowed = ACTUAL_FIELDS
                if self._is_expense_officer() and order.state in ("submitted", "reported"):
                    allowed = allowed | {"manager_id"}
                blocked = changed - allowed
                if blocked:
                    raise UserError(_(
                        "%(order)s is no longer a draft; %(fields)s cannot be "
                        "changed. Reset it to draft first.",
                        order=order.name,
                        fields=", ".join(
                            self._fields[f]._description_string(self.env) for f in sorted(blocked)
                        ),
                    ))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_only_drafts(self):
        for order in self:
            if order.state not in ("draft", "cancel"):
                raise UserError(_(
                    "%(order)s can only be deleted as a draft or once cancelled.",
                    order=order.name,
                ))

    def _set_state(self, vals):
        # sudo, not a context flag: a client can send any context, never sudo.
        return self.sudo().write(vals)

    def _deadline_calendar(self):
        self.ensure_one()
        return self.employee_id.sudo().resource_calendar_id or self.company_id.resource_calendar_id

    # ------------------------------------------------------------------
    # The process: order before the trip, settlement after it
    # ------------------------------------------------------------------

    def action_submit(self):
        """Send the order to the approver."""
        self._check_state("draft", "refused")
        self._check_is_traveller_or_officer()
        for order in self:
            # The approver sees what the trip is expected to cost.
            order.sudo().action_compute_days()
            approver = order.manager_id or order._default_approver()
            order._set_state({"state": "submitted", "manager_id": approver.id})
            if approver:
                order.activity_schedule(
                    "l10n_sk_vehicle_logbook.mail_act_travel_order_approval",
                    user_id=approver.id,
                    date_deadline=fields.Date.to_date(order.date_start),
                )

    def action_approve(self):
        """The employer sets the trip's conditions in writing (§ 3)."""
        self._check_state("submitted")
        self._check_can_approve()
        for order in self:
            if not order.day_ids:
                order.sudo().action_compute_days()
            calendar = order._deadline_calendar()
            order._set_state({
                "state": "approved",
                "planned_date_start": order.date_start,
                "planned_date_end": order.date_end,
                "approved_by_id": self.env.user.id,
                "approval_date": fields.Datetime.now(),
                "report_deadline": _working_days_after(
                    calendar, order.date_end, SETTLEMENT_DEADLINE_DAYS
                ),
            })
            order.activity_feedback(["l10n_sk_vehicle_logbook.mail_act_travel_order_approval"])
            if order.currency_id.compare_amounts(order.advance, 0.0) > 0:
                order._create_advance()
            employee_user = order.employee_id.sudo().user_id
            if employee_user:
                order.activity_schedule(
                    "l10n_sk_vehicle_logbook.mail_act_travel_order_report",
                    user_id=employee_user.id,
                    date_deadline=order.report_deadline,
                )

    def action_refuse(self):
        """Refuse the order, or send a settlement back for correction."""
        self._check_state("submitted", "reported")
        self._check_can_approve()
        for order in self:
            if order.state == "submitted":
                order._set_state({"state": "refused"})
                order.activity_unlink(["l10n_sk_vehicle_logbook.mail_act_travel_order_approval"])
                order.message_post(body=_("Travel order refused."))
            else:
                order._set_state({"state": "approved", "reported_date": False})
                order.activity_unlink(["l10n_sk_vehicle_logbook.mail_act_travel_order_settlement"])
                order.message_post(body=_("Settlement returned for correction."))
                employee_user = order.employee_id.sudo().user_id
                if employee_user:
                    order.activity_schedule(
                        "l10n_sk_vehicle_logbook.mail_act_travel_order_report",
                        user_id=employee_user.id,
                        date_deadline=order.report_deadline or fields.Date.today(),
                    )

    def action_draft(self):
        """Back to draft: the employee withdraws a submitted or refused order;
        an approved one only an expense officer reopens, before its advance
        is booked."""
        self._check_state("submitted", "refused", "approved", "cancel")
        if self.filtered(lambda o: o.state in ("approved", "cancel")):
            if not self._is_expense_officer():
                raise AccessError(_(
                    "Only an expense officer can reopen an approved or cancelled order."
                ))
        else:
            self._check_is_traveller_or_officer()
        self._drop_advance()
        self._set_state({
            "state": "draft", "approved_by_id": False, "approval_date": False,
            "planned_date_start": False, "planned_date_end": False,
            "report_deadline": False,
        })
        self.activity_unlink([
            "l10n_sk_vehicle_logbook.mail_act_travel_order_approval",
            "l10n_sk_vehicle_logbook.mail_act_travel_order_report",
        ])

    def action_cancel(self):
        """The trip does not take place. Once the advance is booked, settle
        the order with no days instead, so the advance is returned."""
        self._check_state("draft", "submitted", "approved", "refused")
        if self.filtered(lambda o: o.state == "approved"):
            self._check_can_approve()
        else:
            self._check_is_traveller_or_officer()
        self._drop_advance()
        self._set_state({"state": "cancel"})
        self.activity_unlink([
            "l10n_sk_vehicle_logbook.mail_act_travel_order_approval",
            "l10n_sk_vehicle_logbook.mail_act_travel_order_report",
        ])

    def action_submit_settlement(self):
        """After the trip: the actual times, meals and costs go to the approver
        (§ 36 ods. 7), who has 10 working days to settle (ods. 8)."""
        self._check_state("approved")
        self._check_is_traveller_or_officer()
        for order in self:
            order.action_compute_days()
            now = fields.Datetime.now()
            order._set_state({"state": "reported", "reported_date": now})
            order.activity_feedback(["l10n_sk_vehicle_logbook.mail_act_travel_order_report"])
            approver = order.manager_id or order.approved_by_id
            if approver:
                order.activity_schedule(
                    "l10n_sk_vehicle_logbook.mail_act_travel_order_settlement",
                    user_id=approver.id,
                    date_deadline=_working_days_after(
                        order._deadline_calendar(), now, SETTLEMENT_DEADLINE_DAYS
                    ),
                )

    def action_settle(self):
        """Approve the settlement: the allowances and the other costs become
        approved expenses, clearing the advance when one was paid."""
        self._check_state("reported")
        self._check_can_approve()
        product = self.env.ref("l10n_sk_vehicle_logbook.product_travel_settlement")
        for order in self:
            advance = order._advance_to_clear()
            expenses = order.expense_ids.sudo()
            if expenses.filtered(lambda e: e.state != "draft"):
                raise UserError(_(
                    "%(order)s: the other costs must still be drafts; they are "
                    "approved here, with the settlement.",
                    order=order.name,
                ))
            if order.currency_id.compare_amounts(order.allowance_amount, 0.0) > 0:
                allowance = self.env["hr.expense"].sudo().create({
                    "name": _("%(order)s travel allowances", order=order.name),
                    "description": order._allowance_description(),
                    "employee_id": order.employee_id.id,
                    "company_id": order.company_id.id,
                    "product_id": product.id,
                    "payment_mode": "own_account",
                    "date": fields.Date.to_date(order.date_end),
                    "total_amount_currency": order.allowance_amount,
                    "tax_ids": [(5, 0, 0)],
                    "l10n_sk_travel_order_id": order.id,
                    "l10n_sk_travel_allowance": True,
                })
                order._set_state({"expense_id": allowance.id})
                expenses |= allowance
            if advance:
                expenses.filtered(
                    lambda e: e.payment_mode == "own_account"
                ).advance_id = advance
            if expenses:
                expenses.action_submit()
                expenses._do_approve()
            order._set_state({
                "state": "settled",
                "settled_by_id": self.env.user.id,
                "settlement_date": fields.Datetime.now(),
            })
            order.activity_feedback(["l10n_sk_vehicle_logbook.mail_act_travel_order_settlement"])
            if advance and order.currency_id.compare_amounts(order.amount_due, 0.0) < 0:
                order.message_post(body=_(
                    "The employee returns %(amount)s of the advance %(advance)s; "
                    "record it with Return Advance once the clearing is posted.",
                    amount=order.currency_id.format(-order.amount_due),
                    advance=advance.display_name,
                ))

    def action_open_expenses(self):
        self.ensure_one()
        expenses = self.advance_expense_id | self.expense_id | self.expense_ids
        return {
            "type": "ir.actions.act_window",
            "name": _("Expenses of %(order)s", order=self.name),
            "res_model": "hr.expense",
            "view_mode": "list,form",
            "domain": [("id", "in", expenses.ids)],
        }

    # ------------------------------------------------------------------
    # The advance
    # ------------------------------------------------------------------

    def _create_advance(self):
        """An approved employee advance for accounting to post and pay."""
        self.ensure_one()
        if self.advance_expense_id:
            return
        product = self.env.ref("hr_expense_advance_clearing.product_emp_advance")
        account = product.with_company(self.company_id).property_account_expense_id
        if not account:
            raise UserError(_(
                "The Employee Advance product has no account for %(company)s. "
                "Set it (account 335000 in the Slovak chart, with Allow "
                "Reconciliation) before approving an order with an advance.",
                company=self.company_id.name,
            ))
        advance = self.env["hr.expense"].sudo().with_company(self.company_id).create({
            "name": _("Advance %(order)s", order=self.name),
            "employee_id": self.employee_id.id,
            "company_id": self.company_id.id,
            "product_id": product.id,
            "account_id": account.id,
            "advance": True,
            "payment_mode": "own_account",
            "date": fields.Date.context_today(self),
            "total_amount_currency": self.advance,
            "tax_ids": [(5, 0, 0)],
            "l10n_sk_travel_order_id": self.id,
        })
        advance.action_submit()
        advance._do_approve()
        self._set_state({"advance_expense_id": advance.id})

    def _drop_advance(self):
        """Withdraw an advance that is not booked yet."""
        for order in self:
            advance = order.advance_expense_id.sudo()
            if not advance or advance.state == "refused":
                continue
            if advance.account_move_id:
                raise UserError(_(
                    "%(order)s: the advance %(advance)s is already booked. "
                    "Settle the order instead, with no days if the trip did "
                    "not take place, so the advance is returned.",
                    order=order.name, advance=advance.display_name,
                ))
            advance._do_refuse(_("Travel order %(order)s withdrawn", order=order.name))
            order._set_state({"advance_expense_id": False})

    def _advance_to_clear(self):
        """The paid advance the settlement clears, or nothing."""
        self.ensure_one()
        advance = self.advance_expense_id.sudo()
        if not advance or advance.state == "refused":
            return self.env["hr.expense"]
        if advance.state not in ("in_payment", "paid"):
            raise UserError(_(
                "%(order)s: the advance %(advance)s is not paid out yet. Pay it, "
                "or have it refused if it was never handed over, before "
                "approving the settlement.",
                order=self.name, advance=advance.display_name,
            ))
        if self.currency_id.is_zero(advance.clearing_residual):
            return self.env["hr.expense"]
        return advance

    def _allowance_description(self):
        self.ensure_one()
        fmt = self.currency_id.format
        lines = [_("Meal allowance and pocket money: %(amount)s", amount=fmt(self.meal_amount))]
        if self.vehicle_mode == "own":
            lines += [
                _("Kilometre allowance, %(km)s km: %(amount)s",
                  km=self.kilometres, amount=fmt(self.kilometre_amount)),
                _("Fuel: %(amount)s", amount=fmt(self.fuel_amount)),
            ]
        return "\n".join(lines)



class L10nSkTravelOrderLineMixin(models.AbstractModel):
    """Day and country lines follow the order: editable while it is a draft
    or, for the trip as it went, approved."""
    _name = "l10n.sk.travel.order.line.mixin"
    _description = "Travel order line editability"

    def _check_order_editable(self, orders):
        if self.env.su:
            return
        officer = self.env.user.has_group("hr_expense.group_hr_expense_user")
        for order in orders:
            traveller = officer or order.employee_id.sudo().user_id == self.env.user
            if order.state not in ("draft", "approved") or (
                order.state == "approved" and not traveller
            ):
                raise UserError(_(
                    "%(order)s is no longer a draft; its days and countries "
                    "cannot be changed.",
                    order=order.name,
                ))

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        self._check_order_editable(records.order_id)
        return records

    def write(self, vals):
        self._check_order_editable(self.order_id)
        res = super().write(vals)
        if "order_id" in vals:
            self._check_order_editable(self.order_id)
        return res

    @api.ondelete(at_uninstall=False)
    def _unlink_when_order_editable(self):
        self._check_order_editable(self.order_id)


class L10nSkTravelOrderDay(models.Model):
    _name = "l10n.sk.travel.order.day"
    _inherit = ["l10n.sk.travel.order.line.mixin"]
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
    breakfast_abroad = fields.Boolean(
        help="The free breakfast was provided abroad, so it cuts the foreign "
             "allowance (§ 13 ods. 7) and not the domestic one (§ 5 ods. 6).",
    )
    lunch_abroad = fields.Boolean(
        help="The free lunch was provided abroad, so it cuts the foreign "
             "allowance (§ 13 ods. 7) and not the domestic one (§ 5 ods. 6).",
    )
    dinner_abroad = fields.Boolean(
        help="The free dinner was provided abroad, so it cuts the foreign "
             "allowance (§ 13 ods. 7) and not the domestic one (§ 5 ods. 6).",
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
        "rate", "rate_18", "breakfast", "lunch", "dinner", "breakfast_abroad",
        "lunch_abroad", "dinner_abroad", "hours_abroad", "foreign_base",
        "foreign_rate", "pocket_money",
    )
    def _compute_amount(self):
        """Each free meal cuts the part of the day where it was provided, and
        each part only down to zero (§ 5 ods. 6, § 13 ods. 7, § 16 ods. 1)."""
        for day in self:
            home, abroad = travel_rules.split_meals(
                (day.breakfast, day.lunch, day.dinner),
                (day.breakfast_abroad, day.lunch_abroad, day.dinner_abroad),
                bool(day.foreign_base),
            )
            domestic = travel_rules.meal_allowance(day.rate, day.rate_18, *home)
            foreign = travel_rules.foreign_meal_allowance(
                day.foreign_base, day.hours_abroad, *abroad
            ) if day.foreign_base else 0.0
            day.foreign_amount = foreign
            day.amount = domestic + travel_rules._cents(
                (foreign + day.pocket_money) * (day.foreign_rate or 1.0)
            )


class L10nSkTravelOrderStay(models.Model):
    _name = "l10n.sk.travel.order.stay"
    _inherit = ["l10n.sk.travel.order.line.mixin"]
    _description = "Country visited on a foreign trip"
    _order = "date_arrival, id"

    order_id = fields.Many2one("l10n.sk.travel.order", required=True, ondelete="cascade")
    country_id = fields.Many2one("res.country", required=True)
    date_arrival = fields.Datetime(
        string="Arrival",
        help="When the trip enters this country. Empty on the first country "
             "means the moment it leaves Slovakia.",
    )


class L10nSkTravelOrderFuel(models.Model):
    """One part of the trip's fuel at one unit price (§ 7 ods. 4, § 15)."""
    _name = "l10n.sk.travel.order.fuel"
    _inherit = ["l10n.sk.travel.order.line.mixin"]
    _description = "Travel order fuel line"
    _order = "sequence, id"

    order_id = fields.Many2one("l10n.sk.travel.order", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    abroad = fields.Boolean(
        help="Kilometres driven abroad, or after re-entering Slovakia on fuel "
             "bought abroad (§ 15 ods. 1 and 2).",
    )
    kilometres = fields.Float(required=True)
    unit_price = fields.Float(
        digits=(8, 3), required=True,
        help="From the purchase receipt; abroad, the foreign receipt (an "
             "average of several receipts is allowed). Without one, the price "
             "at departure in that country, or the Štatistický úrad SR price.",
    )
    currency_id = fields.Many2one(
        "res.currency", required=True,
        default=lambda self: self.env.company.currency_id,
        help="Euro in the euro area; the local currency elsewhere (§ 15 ods. 2). "
             "Converted at the ECB or NBS rate valid on the first day of the "
             "month the trip began.",
    )
    amount = fields.Float(
        digits=(10, 2), compute="_compute_amount", store=True,
        help="In the line's currency.",
    )

    @api.depends("kilometres", "unit_price", "order_id.consumption")
    def _compute_amount(self):
        for line in self:
            line.amount = travel_rules.fuel_allowance(
                line.kilometres, line.order_id.consumption, line.unit_price
            )
