# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import datetime

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTravelOrder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env["hr.employee"].create({"name": "Cesta Testovacia"})
        brand = cls.env["fleet.vehicle.model.brand"].create({"name": "Brand"})
        model = cls.env["fleet.vehicle.model"].create({"name": "M", "brand_id": brand.id})
        cls.vehicle = cls.env["fleet.vehicle"].create({"model_id": model.id})

    def _order(self, **vals):
        values = {
            "employee_id": self.employee.id,
            "date_start": datetime(2026, 6, 8, 6, 0),
            "date_end": datetime(2026, 6, 8, 19, 0),
            "destination": "Košice",
            "purpose": "Audit",
        }
        values.update(vals)
        return self.env["l10n.sk.travel.order"].create(values)

    def _trip(self, start, end, odo_start, odo_end, **vals):
        values = {
            "vehicle_id": self.vehicle.id, "driver_id": self.employee.id,
            "date_start": start, "date_end": end, "origin": "BA", "destination": "KE",
            "purpose": "Audit", "odometer_start": odo_start, "odometer_end": odo_end,
        }
        values.update(vals)
        return self.env["l10n.sk.vehicle.trip"].create(values)

    def test_thirteen_hour_day_with_own_car_settles(self):
        order = self._order(
            vehicle_mode="own", kilometres=100.0, consumption=6.6,
            fuel_price=1.5, advance=10.0,
        )
        order.action_approve()
        self.assertEqual(order.meal_amount, 13.80)
        self.assertEqual(order.kilometre_amount, 31.30)
        self.assertEqual(order.fuel_amount, 9.90)
        self.assertAlmostEqual(order.amount_due, 45.0, places=2)
        order.action_settle()
        self.assertEqual(order.state, "settled")
        self.assertAlmostEqual(order.expense_id.total_amount_currency, 45.0, places=2)

    def test_advance_above_the_total_creates_no_expense(self):
        order = self._order(advance=50.0)
        order.action_approve()
        order.action_settle()
        self.assertFalse(order.expense_id)

    def test_recompute_keeps_ticked_meals(self):
        order = self._order()
        order.action_compute_days()
        order.day_ids.lunch = True
        order.action_compute_days()
        self.assertTrue(order.day_ids.lunch)

    def test_kilometres_come_from_linked_trips(self):
        trip = self._trip(datetime(2026, 6, 8, 6), datetime(2026, 6, 8, 9), 1000, 1200)
        order = self._order(vehicle_mode="own", trip_ids=[(6, 0, trip.ids)])
        order.action_compute_days()
        self.assertEqual(order.kilometres, 200.0)

    def test_odometer_cannot_precede_the_previous_trip(self):
        self._trip(datetime(2026, 6, 8, 6), datetime(2026, 6, 8, 9), 1000, 1200)
        with self.assertRaises(ValidationError):
            self._trip(datetime(2026, 6, 9, 6), datetime(2026, 6, 9, 9), 1100, 1300)

    def test_business_trip_needs_a_purpose(self):
        with self.assertRaises(ValidationError):
            self._trip(datetime(2026, 6, 8, 6), datetime(2026, 6, 8, 9), 1, 2, purpose=False)
