# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The order before the trip, the settlement after it, and who may do what.

Trip times are naive UTC; June is CEST, so 06:00-19:00 UTC is 13 hours
(13.80 EUR, oznámenie 280/2025 Z. z.).
"""
from datetime import date, datetime

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import Form, tagged

from odoo.addons.hr_expense.tests.common import TestExpenseCommon
from odoo.addons.mail.tests.common import mail_new_test_user

from ..models.l10n_sk_travel_order import _working_days_after


@tagged("post_install", "-at_install")
class TestTravelProcess(TestExpenseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        company = cls.company_data["company"]
        advance_account = cls.company_data["default_account_deferred_expense"]
        advance_account.reconcile = True
        cls.advance_account = advance_account
        cls.env.ref("hr_expense_advance_clearing.product_emp_advance").with_company(
            company
        ).property_account_expense_id = advance_account
        cls.clearing_journal = cls.env["account.journal"].create({
            "name": "Advance Clearing", "code": "ACLR", "type": "general",
            "company_id": company.id,
        })
        company.clearing_journal_id = cls.clearing_journal

        companies = [Command.set(cls.env.companies.ids)]
        # A team approver who is not an expense officer.
        cls.approver = mail_new_test_user(
            cls.env, name="Approver", login="travel_approver",
            groups="base.group_user,hr_expense.group_hr_expense_team_approver",
            company_ids=companies,
        )
        cls.colleague_user = mail_new_test_user(
            cls.env, name="Colleague", login="travel_colleague",
            groups="base.group_user", company_ids=companies,
        )
        cls.officer = cls.expense_user_manager
        cls.employee = cls.expense_employee
        cls.employee.sudo().expense_manager_id = cls.approver
        cls.colleague = cls.env["hr.employee"].sudo().create({
            "name": "Colleague", "user_id": cls.colleague_user.id,
            "company_id": company.id,
            "work_contact_id": cls.colleague_user.partner_id.id,
        })
        cls.approver_employee = cls.env["hr.employee"].sudo().create({
            "name": "Approver", "user_id": cls.approver.id, "company_id": company.id,
            "expense_manager_id": cls.officer.id,
            "work_contact_id": cls.approver.partner_id.id,
        })

    def _order(self, user=None, **vals):
        values = {
            "employee_id": self.employee.id,
            "company_id": self.company_data["company"].id,
            "date_start": datetime(2026, 6, 8, 6, 0),
            "date_end": datetime(2026, 6, 8, 19, 0),
            "destination": "Košice",
            "purpose": "Audit",
        }
        values.update(vals)
        Order = self.env["l10n.sk.travel.order"]
        if user:
            Order = Order.with_user(user)
        return Order.create(values)

    def _approved(self, **vals):
        order = self._order(user=self.expense_user_employee, **vals)
        order.action_submit()
        order.with_user(self.approver).action_approve()
        return order

    def _post_and_pay(self, expenses):
        """Accounting books expenses as hr_expense_advance_clearing documents
        it: clearings through the clearing journal, all in one go."""
        expenses = expenses.with_env(self.env)
        action = expenses.action_post()
        wizard = self.env["hr.expense.post.wizard"].with_context(
            **action["context"]
        ).browse(action["res_id"])
        wizard.accounting_date = fields.Date.context_today(expenses[:1])
        if expenses[:1].advance_id:
            wizard.clearing_journal_id = self.clearing_journal
        wizard.action_post_entry()

    def _register_payment(self, action, amount):
        register = self.env["account.payment.register"].with_context(**action["context"])
        with Form(register) as form:
            form.journal_id = self.company_data["default_journal_bank"]
            form.amount = amount
        return form.save()._create_payments()

    def _pay_advance(self, order):
        advance = order.advance_expense_id.with_env(self.env)
        self._post_and_pay(advance)
        self._register_payment(advance.action_pay(), advance.total_amount)
        self.assertIn(advance.state, ("in_payment", "paid"))
        return advance

    # -- access ------------------------------------------------------------

    def test_employee_sees_own_orders_approver_sees_team(self):
        own = self._order(user=self.expense_user_employee)
        theirs = self._order(employee_id=self.colleague.id)
        Order = self.env["l10n.sk.travel.order"]
        self.assertEqual(Order.with_user(self.expense_user_employee).search([]), own)
        self.assertEqual(Order.with_user(self.colleague_user).search([]), theirs)
        self.assertEqual(Order.with_user(self.approver).search([]), own)
        self.assertEqual(Order.with_user(self.officer).search([]), own | theirs)
        # The days are only reachable through a visible order.
        theirs.action_compute_days()
        Day = self.env["l10n.sk.travel.order.day"]
        self.assertFalse(Day.with_user(self.expense_user_employee).search([
            ("order_id", "=", theirs.id),
        ]))

    def test_employee_cannot_order_a_trip_for_a_colleague(self):
        with self.assertRaises(AccessError):
            self._order(user=self.expense_user_employee, employee_id=self.colleague.id)

    def test_nobody_approves_their_own_trip(self):
        order = self._order(user=self.approver, employee_id=self.approver_employee.id)
        order.action_submit()
        self.assertEqual(order.manager_id, self.officer)
        with self.assertRaises(AccessError):
            order.with_user(self.approver).action_approve()
        # Not even an expense manager, on their own trip.
        officer_employee = self.env["hr.employee"].sudo().create({
            "name": "Officer", "user_id": self.officer.id,
            "company_id": self.company_data["company"].id,
        })
        own = self._order(user=self.officer, employee_id=officer_employee.id)
        own.action_submit()
        self.assertFalse(own.with_user(self.officer).can_approve)
        with self.assertRaises(AccessError):
            own.with_user(self.officer).action_approve()

    def test_employee_cannot_approve_by_calling_the_method(self):
        order = self._order(user=self.expense_user_employee)
        order.action_submit()
        self.assertEqual(order.manager_id, self.approver)
        with self.assertRaises(AccessError):
            order.with_user(self.expense_user_employee).action_approve()
        with self.assertRaises(AccessError):
            order.with_user(self.colleague_user).action_approve()

    def test_process_fields_cannot_be_written_directly(self):
        order = self._order(user=self.expense_user_employee)
        with self.assertRaises(AccessError):
            order.with_user(self.expense_user_employee).state = "approved"
        with self.assertRaises(AccessError):
            order.with_user(self.expense_user_employee).approved_by_id = self.approver
        with self.assertRaises(AccessError):
            self._order(user=self.expense_user_employee, state="settled")
        with self.assertRaises(UserError):
            self.env["hr.expense"].with_user(self.expense_user_employee).create({
                "name": "Fake allowance", "employee_id": self.employee.id,
                "product_id": self.product_c.id, "total_amount_currency": 99.0,
                "l10n_sk_travel_allowance": True,
            })

    def test_a_context_flag_does_not_open_the_guards(self):
        # Any client can send any context; only sudo may bypass the checks.
        order = self._order(user=self.expense_user_employee)
        forged = order.with_user(self.expense_user_employee).with_context(
            l10n_sk_travel_internal=True
        )
        with self.assertRaises(AccessError):
            forged.state = "approved"
        forged.action_submit()
        with self.assertRaises(UserError):
            forged.purpose = "Changed after submission"

    def test_traveller_cannot_choose_the_approver(self):
        with self.assertRaises(AccessError):
            self._order(user=self.expense_user_employee, manager_id=self.colleague_user.id)
        order = self._order(user=self.expense_user_employee)
        with self.assertRaises(AccessError):
            order.with_user(self.expense_user_employee).manager_id = self.colleague_user
        # An expense officer may assign one.
        order.with_user(self.officer).manager_id = self.colleague_user
        order.action_submit()
        self.assertEqual(order.manager_id, self.colleague_user)

    def test_no_new_cost_after_the_settlement_is_submitted(self):
        order = self._approved()
        order.action_submit_settlement()
        with self.assertRaises(UserError):
            self.env["hr.expense"].with_user(self.expense_user_employee).create({
                "name": "Late taxi", "employee_id": self.employee.id,
                "product_id": self.product_c.id, "total_amount_currency": 40.0,
                "tax_ids": [Command.clear()], "l10n_sk_travel_order_id": order.id,
            })
        other = self.env["hr.expense"].with_user(self.expense_user_employee).create({
            "name": "Late taxi", "employee_id": self.employee.id,
            "product_id": self.product_c.id, "total_amount_currency": 40.0,
            "tax_ids": [Command.clear()],
        })
        with self.assertRaises(UserError):
            other.l10n_sk_travel_order_id = order

    def test_order_is_locked_after_submission(self):
        order = self._order(user=self.expense_user_employee)
        order.action_submit()
        with self.assertRaises(UserError):
            order.purpose = "Something else"
        with self.assertRaises(UserError):
            order.date_end = datetime(2026, 6, 8, 20)
        order.with_user(self.approver).action_approve()
        # Approved: the order stays as set, the trip as it went is entered.
        with self.assertRaises(UserError):
            order.with_user(self.expense_user_employee).destination = "Prešov"
        order.with_user(self.expense_user_employee).date_end = datetime(2026, 6, 8, 20)
        self.assertEqual(order.planned_date_end, datetime(2026, 6, 8, 19))
        # The trip as it went is the employee's to enter, not the approver's.
        with self.assertRaises(UserError):
            order.with_user(self.approver).date_end = datetime(2026, 6, 8, 21)
        with self.assertRaises(UserError):
            order.with_user(self.approver).day_ids.lunch = True
        order.action_submit_settlement()
        with self.assertRaises(UserError):
            order.with_user(self.expense_user_employee).date_end = datetime(2026, 6, 8, 21)
        with self.assertRaises(UserError):
            order.with_user(self.expense_user_employee).day_ids.lunch = True

    def test_only_an_officer_reopens_an_approved_order(self):
        order = self._approved()
        with self.assertRaises(AccessError):
            order.with_user(self.expense_user_employee).action_draft()
        order.with_user(self.officer).action_draft()
        self.assertEqual(order.state, "draft")
        self.assertFalse(order.planned_date_start)

    # -- the process ---------------------------------------------------------

    def test_submission_and_approval_schedule_activities(self):
        order = self._order(user=self.expense_user_employee)
        order.action_submit()
        approval = order.activity_ids
        self.assertEqual(approval.user_id, self.approver)
        order.with_user(self.approver).action_approve()
        self.assertEqual(order.approved_by_id, self.approver)
        # Monday 8 June: ten working days from Tuesday is Monday 22 June.
        self.assertEqual(order.report_deadline, date(2026, 6, 22))
        report = order.activity_ids
        self.assertEqual(report.user_id, self.expense_user_employee)
        self.assertEqual(report.date_deadline, date(2026, 6, 22))
        order.action_submit_settlement()
        self.assertEqual(order.activity_ids.user_id, self.approver)

    def test_deadline_skips_weekends(self):
        calendar = self.company_data["company"].resource_calendar_id
        # Returned on Friday 12 June: count from Monday 15th to Friday 26th.
        self.assertEqual(
            _working_days_after(calendar, datetime(2026, 6, 12, 15), 10), date(2026, 6, 26)
        )
        self.assertEqual(
            _working_days_after(False, datetime(2026, 6, 12, 15), 10), date(2026, 6, 26)
        )

    def test_refused_settlement_goes_back_to_the_employee(self):
        order = self._approved()
        order.action_submit_settlement()
        order.with_user(self.approver).action_refuse()
        self.assertEqual(order.state, "approved")
        order.with_user(self.expense_user_employee).date_end = datetime(2026, 6, 8, 20)

    def test_settlement_without_advance(self):
        order = self._approved()
        cost = self.env["hr.expense"].with_user(self.expense_user_employee).create({
            "name": "Train ticket", "employee_id": self.employee.id,
            "product_id": self.product_c.id, "total_amount_currency": 25.0,
            "tax_ids": [Command.clear()], "l10n_sk_travel_order_id": order.id,
            "payment_mode": "own_account",
        })
        self.assertEqual(order.total_amount, 13.80 + 25.0)
        with self.assertRaises(UserError):
            cost.with_user(self.expense_user_employee).action_submit()
        order.action_submit_settlement()
        with self.assertRaises(UserError):
            cost.with_user(self.expense_user_employee).total_amount_currency = 99.0
        order.with_user(self.approver).action_settle()
        self.assertEqual(order.state, "settled")
        self.assertEqual(order.settled_by_id, self.approver)
        self.assertEqual(order.expense_id.total_amount, 13.80)
        self.assertTrue(order.expense_id.l10n_sk_travel_allowance)
        self.assertEqual((order.expense_id | cost).mapped("state"), ["approved", "approved"])
        self.assertFalse((order.expense_id | cost).advance_id)

    def test_advance_is_created_cleared_and_returned(self):
        order = self._approved(advance=100.0)
        advance = order.advance_expense_id
        self.assertTrue(advance.advance)
        self.assertEqual(advance.state, "approved")
        self.assertEqual(advance.total_amount, 100.0)
        self._pay_advance(order)
        cost = self.env["hr.expense"].with_user(self.expense_user_employee).create({
            "name": "Hotel", "employee_id": self.employee.id,
            "product_id": self.product_c.id, "total_amount_currency": 30.0,
            "tax_ids": [Command.clear()], "l10n_sk_travel_order_id": order.id,
            "payment_mode": "own_account",
        })
        order.action_submit_settlement()
        order.with_user(self.approver).action_settle()
        clearings = (order.expense_id | cost).with_env(self.env)
        self.assertEqual(clearings.advance_id, advance)
        self.assertAlmostEqual(order.amount_due, 13.80 + 30.0 - 100.0)
        # Both clearings booked together take 43.80 of the 100.
        self._post_and_pay(clearings)
        self.assertAlmostEqual(advance.clearing_residual, 56.20)
        self.assertAlmostEqual(sum(clearings.mapped("amount_to_pay")), 0.0)
        self._register_payment(advance.action_return_advance(), 56.20)
        self.assertAlmostEqual(advance.clearing_residual, 0.0)

    def test_settlement_above_the_advance_is_paid_to_the_employee(self):
        order = self._approved(advance=10.0)
        self._pay_advance(order)
        order.action_submit_settlement()
        order.with_user(self.approver).action_settle()
        self._post_and_pay(order.expense_id)
        self.assertAlmostEqual(order.expense_id.amount_to_pay, 3.80)

    def test_settlement_waits_for_the_advance_to_be_paid(self):
        order = self._approved(advance=50.0)
        order.action_submit_settlement()
        with self.assertRaises(UserError):
            order.with_user(self.approver).action_settle()

    def test_cancel_withdraws_an_unbooked_advance_only(self):
        order = self._approved(advance=50.0)
        advance = order.advance_expense_id
        order.with_user(self.approver).action_cancel()
        self.assertEqual(order.state, "cancel")
        self.assertEqual(advance.state, "refused")
        booked = self._approved(advance=50.0)
        self._pay_advance(booked)
        with self.assertRaises(UserError):
            booked.with_user(self.approver).action_cancel()
