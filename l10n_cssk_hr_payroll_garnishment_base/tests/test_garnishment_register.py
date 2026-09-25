# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Integration tests for the garnishment register (no payroll engine needed)."""

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestGarnishmentRegister(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {"name": "Garnishment CZ", "country_id": cls.env.ref("base.cz").id}
        )
        cls.env.user.company_ids |= cls.company
        cls.env.user.company_id = cls.company
        cls.employee = cls.env["hr.employee"].create(
            {"name": "Dlužník", "company_id": cls.company.id}
        )
        cls.bailiff = cls.env["res.partner"].create({"name": "Exekutorský úřad"})
        cls.creditor = cls.env["res.partner"].create({"name": "Věřitel a.s."})

    def _order(self, **kwargs):
        vals = {
            "case_number": "123 EX 456/2026",
            "employee_id": self.employee.id,
            "company_id": self.company.id,
            "claim_class": "ordinary",
            "date_delivered": "2026-01-10",
            "total_amount": 100000.0,
            "creditor_partner_id": self.creditor.id,
            "bailiff_partner_id": self.bailiff.id,
            "state": "running",
        }
        vals.update(kwargs)
        return self.env["hr.wage.garnishment"].create(vals)

    def test_payee_defaults_to_bailiff(self):
        order = self._order()
        self.assertEqual(order.payee_partner_id, self.bailiff)
        order.bailiff_partner_id = False
        self.assertEqual(order.payee_partner_id, self.creditor)

    def test_variable_symbol_derived_from_case_number(self):
        self.assertEqual(self._order().variable_symbol, "1234562026")

    def test_order_needs_an_amount(self):
        with self.assertRaises(ValidationError):
            self._order(total_amount=0.0, monthly_amount=0.0)

    def test_fine_class_rejected_for_czech_company(self):
        """Pokuty za priestupky are a Slovak construct only."""
        with self.assertRaises(ValidationError):
            self._order(claim_class="fine")

    def test_orders_do_not_leak_across_companies(self):
        """A payroll officer who can see two companies must not garnish from
        both at once.

        The multi-company record rule does not do this: ``company_ids`` in a
        rule resolves to the user's ALLOWED companies, not to ``env.company``.
        So an officer entitled to A and B saw B's orders while computing an A
        payslip, and because the line's ``company_id`` is
        ``related=garnishment_id.company_id`` the deduction landed in B — with
        the remittance later booked in B's journal against an A payslip.
        """
        other = self.env["res.company"].create(
            {"name": "Garnishment CZ 2", "country_id": self.env.ref("base.cz").id})
        self.env.user.company_ids |= other
        employee_b = self.env["hr.employee"].create(
            {"name": "Dlužník", "company_id": other.id})
        # Same PERSON employed by both companies is the realistic shape, but
        # employee records are per company; what matters is that the order of
        # one company is invisible to the other's allocation.
        mine = self._order()
        theirs = self._order(company_id=other.id, employee_id=employee_b.id)

        Garnishment = self.env["hr.wage.garnishment"]
        found = Garnishment._active_orders(
            self.employee, "2026-06-01", "2026-06-30", self.company)
        self.assertIn(mine, found)
        self.assertNotIn(theirs, found,
                         "another company's order must not be allocatable here")

        found_b = Garnishment._active_orders(
            employee_b, "2026-06-01", "2026-06-30", other)
        self.assertIn(theirs, found_b)
        self.assertNotIn(mine, found_b)

    def test_allocation_and_registration(self):
        order = self._order()
        orders, result = self.env["hr.wage.garnishment"]._allocate(
            self.employee, 39270.0, "2026-03-01", "2026-03-31", self.company
        )
        self.assertEqual(orders, order)
        self.assertEqual(result.allocations[order.id], 8389.0)

        self.env["hr.wage.garnishment"]._register_allocation(
            self.employee, result, orders, "hr.payslip,1", "2026-03-01", "2026-03-31"
        )
        self.assertEqual(order.paid_amount, 8389.0)
        self.assertEqual(order.remaining_amount, 100000.0 - 8389.0)

    def test_registration_is_idempotent(self):
        """Recomputing a payslip must not double-count the deduction."""
        order = self._order()
        for _i in range(3):
            orders, result = self.env["hr.wage.garnishment"]._allocate(
                self.employee, 39270.0, "2026-03-01", "2026-03-31", self.company
            )
            self.env["hr.wage.garnishment"]._register_allocation(
                self.employee, result, orders, "hr.payslip,1", "2026-03-01", "2026-03-31"
            )
        self.assertEqual(len(order.line_ids), 1)
        self.assertEqual(order.paid_amount, 8389.0)

    def test_order_settles_when_fully_paid(self):
        order = self._order(total_amount=5000.0)
        orders, result = self.env["hr.wage.garnishment"]._allocate(
            self.employee, 39270.0, "2026-03-01", "2026-03-31", self.company
        )
        self.env["hr.wage.garnishment"]._register_allocation(
            self.employee, result, orders, "hr.payslip,1", "2026-03-01", "2026-03-31"
        )
        self.assertEqual(order.paid_amount, 5000.0)
        self.assertEqual(order.state, "done")

    def test_settled_orders_are_skipped(self):
        order = self._order()
        order.action_settle()
        orders, result = self.env["hr.wage.garnishment"]._allocate(
            self.employee, 39270.0, "2026-03-01", "2026-03-31", self.company
        )
        self.assertFalse(orders)
        self.assertIsNone(result)

    def test_remitted_lines_cannot_be_deleted(self):
        order = self._order()
        orders, result = self.env["hr.wage.garnishment"]._allocate(
            self.employee, 39270.0, "2026-03-01", "2026-03-31", self.company
        )
        self.env["hr.wage.garnishment"]._register_allocation(
            self.employee, result, orders, "hr.payslip,1", "2026-03-01", "2026-03-31"
        )
        order.line_ids.state = "done"
        with self.assertRaises(UserError):
            order.line_ids.unlink()

    def test_unsupported_country_is_refused(self):
        other = self.env["res.company"].create(
            {"name": "DE Co", "country_id": self.env.ref("base.de").id}
        )
        employee = self.env["hr.employee"].create(
            {"name": "Schuldner", "company_id": other.id}
        )
        with self.assertRaises(UserError):
            self.env["hr.wage.garnishment"]._allocate(
                employee, 3000.0, "2026-03-01", "2026-03-31", other
            )

    def test_notice_wizard_requires_orders(self):
        wizard = self.env["hr.wage.garnishment.notice"].create(
            {
                "employee_id": self.employee.id,
                "company_id": self.company.id,
                "notice_type": "settlement",
                "date_from": "2026-01-01",
                "date_to": fields.Date.today(),
            }
        )
        with self.assertRaises(UserError):
            wizard.action_print()
