# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class L10nSkVehicleTrip(models.Model):
    _name = "l10n.sk.vehicle.trip"
    _description = "Vehicle logbook entry"
    _order = "date_start desc, id desc"

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    vehicle_id = fields.Many2one("fleet.vehicle", required=True, index=True)
    driver_id = fields.Many2one("hr.employee", required=True)
    date_start = fields.Datetime(string="Departure", required=True)
    date_end = fields.Datetime(string="Arrival", required=True)
    origin = fields.Char(string="From", required=True)
    destination = fields.Char(string="To", required=True)
    trip_type = fields.Selection(
        [("business", "Business"), ("private", "Private")],
        required=True,
        default="business",
    )
    purpose = fields.Char()
    odometer_start = fields.Float(required=True)
    odometer_end = fields.Float(required=True)
    distance = fields.Float(compute="_compute_distance", store=True)
    travel_order_id = fields.Many2one("l10n.sk.travel.order", ondelete="set null")

    @api.depends("odometer_start", "odometer_end")
    def _compute_distance(self):
        for trip in self:
            trip.distance = trip.odometer_end - trip.odometer_start

    @api.constrains("date_start", "date_end", "odometer_start", "odometer_end",
                    "trip_type", "purpose", "vehicle_id")
    def _check_trip(self):
        for trip in self:
            if trip.date_end <= trip.date_start:
                raise ValidationError(_("Arrival must be after departure."))
            if trip.odometer_end < trip.odometer_start:
                raise ValidationError(_("The odometer cannot go backwards."))
            if trip.trip_type == "business" and not trip.purpose:
                raise ValidationError(_("A business trip needs a purpose."))
            previous = self.sudo().search(
                [
                    ("vehicle_id", "=", trip.vehicle_id.id),
                    ("id", "!=", trip.id),
                    ("date_start", "<", trip.date_start),
                ],
                order="date_start desc",
                limit=1,
            )
            if previous and trip.odometer_start < previous.odometer_end:
                raise ValidationError(_(
                    "This trip starts at %(start)s km, below the %(end)s km "
                    "where the previous trip ended.",
                    start=trip.odometer_start, end=previous.odometer_end,
                ))
