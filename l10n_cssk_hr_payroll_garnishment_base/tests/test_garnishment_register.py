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

    # --- § 282a o. s. ř.: deductions start the month after delivery ------
    def test_cz_deductions_start_the_month_after_delivery(self):
        """§ 282a: "od prvního dne prvního kalendářního měsíce následujícího
        po doručení". An order served in March is not deducted from the
        March wage."""
        order = self._order(date_delivered="2026-03-10")
        self.assertEqual(str(order.date_start), "2026-04-01")
        self.assertEqual(
            str(self._order(date_delivered="2026-03-01").date_start),
            "2026-04-01", "delivery on the 1st still waits a month")
        Garnishment = self.env["hr.wage.garnishment"]
        orders, result = Garnishment._allocate(
            self.employee, 39270.0, "2026-03-01", "2026-03-31", self.company)
        self.assertNotIn(order, orders)
        orders, result = Garnishment._allocate(
            self.employee, 39270.0, "2026-04-01", "2026-04-30", self.company)
        self.assertIn(order, orders)

    def test_sk_start_stays_on_delivery_day(self):
        sk = self.env["res.company"].create(
            {"name": "Garnishment SK", "country_id": self.env.ref("base.sk").id})
        employee = self.env["hr.employee"].create(
            {"name": "Dlžník", "company_id": sk.id})
        order = self._order(company_id=sk.id, employee_id=employee.id,
                            date_delivered="2026-03-10")
        self.assertEqual(str(order.date_start), "2026-03-10")

    # --- NV 595/2006 § 4: amounts as at 1 January of the PAYMENT year ----
    def test_cz_rates_follow_the_payment_year(self):
        Garnishment = self.env["hr.wage.garnishment"]
        self.assertEqual(
            str(Garnishment._rate_date("CZ", "2025-12-31")), "2026-01-01",
            "a December wage is paid in January: the new year's amounts")
        self.assertEqual(
            str(Garnishment._rate_date("CZ", "2026-03-31")), "2026-01-01")
        self.assertEqual(
            str(Garnishment._rate_date("CZ", "2026-12-31", "2026-12-20")),
            "2026-01-01", "a known payday in December keeps that year")
        self.assertEqual(
            str(Garnishment._rate_date("SK", "2026-03-31")), "2026-03-31")

    def test_cz_december_wage_uses_the_new_year_amounts(self):
        """Only 2026 Czech amounts ship. A December 2025 wage paid in January
        2026 must be computed on them — on the period end it found no rates
        at all and the payslip failed."""
        self._order(date_delivered="2025-10-10")
        orders, result = self.env["hr.wage.garnishment"]._allocate(
            self.employee, 39270.0, "2025-12-01", "2025-12-31", self.company)
        self.assertTrue(orders)
        self.assertEqual(result.protected, 14102.0)

    # --- dependants recorded on the payroll contract -----------------------
    def test_register_dependants_win(self):
        self.employee.l10n_cssk_garnishment_dependents = 2
        self.assertEqual(
            self.env["hr.wage.garnishment"]._dependents(
                self.employee, "CZ", "2026-03-31"), 2)

    def test_contract_dependants_are_the_fallback(self):
        version = self.employee.version_id
        if "l10n_cz_garnishment_dependents" not in version._fields:
            self.skipTest("needs the Czech payroll's contract field")
        version.l10n_cz_garnishment_dependents = 2
        self.employee.l10n_cssk_garnishment_dependents = 0
        Garnishment = self.env["hr.wage.garnishment"]
        self.assertEqual(
            Garnishment._dependents(self.employee, "CZ", "2026-03-31"), 2)
        self._order()
        _orders, result = Garnishment._allocate(
            self.employee, 39270.0, "2026-03-01", "2026-03-31", self.company)
        # 14 101,50 x (1 + 2 x 1/4) = 21 152,25 -> 21 153 (NV 595/2006 § 3)
        self.assertEqual(result.protected, 21153.0)

    def test_four_executions_trigger_the_two_thirds_rule(self):
        """§ 279 odst. 4 o. s. ř. counts výkony rozhodnutí: four executions
        switch it on; an agreement on deductions does not count."""
        for i in range(3):
            self._order(case_number="10%s EX 1/2026" % i,
                        date_delivered="2026-01-%02d" % (10 + i))
        self._order(case_number="DOHODA 1", garnishment_type="agreement",
                    date_delivered="2026-01-20")
        Garnishment = self.env["hr.wage.garnishment"]
        _orders, result = Garnishment._allocate(
            self.employee, 39270.0, "2026-03-01", "2026-03-31", self.company)
        self.assertEqual(result.total, 8389.0)
        self.assertFalse(result.detail["two_thirds"])
        self._order(case_number="104 EX 1/2026", garnishment_type="administrative",
                    date_delivered="2026-01-21")
        _orders, result = Garnishment._allocate(
            self.employee, 39270.0, "2026-03-01", "2026-03-31", self.company)
        self.assertTrue(result.detail["two_thirds"])
        self.assertEqual(result.total, 16778.0)

    def test_two_thirds_rule_lifted_for_a_low_paid_pensioner(self):
        for i in range(4):
            self._order(case_number="20%s EX 1/2026" % i,
                        date_delivered="2026-01-%02d" % (10 + i))
        self.employee.l10n_cssk_garnishment_is_pensioner = True
        _orders, result = self.env["hr.wage.garnishment"]._allocate(
            self.employee, 16000.0, "2026-03-01", "2026-03-31", self.company)
        self.assertEqual(result.total, 632.0)

    def test_notice_cites_the_right_paragraph(self):
        """Joining is notified under § 294 odst. 2 o. s. ř., leaving under
        § 295 odst. 2 — both used to cite § 294 odst. 1, the duty to ASK the
        previous employer for a certificate."""
        self._order()
        Notice = self.env["hr.wage.garnishment.notice"]
        start = Notice.create({"notice_type": "employment_start",
                               "employee_id": self.employee.id,
                               "company_id": self.company.id})
        end = Notice.create({"notice_type": "employment_end",
                             "employee_id": self.employee.id,
                             "company_id": self.company.id})
        self.assertEqual(start._legal_basis(),
                         "Oznámení podle § 294 odst. 2 o. s. ř.")
        self.assertEqual(end._legal_basis(),
                         "Oznámení podle § 295 odst. 2 o. s. ř.")
        html = self.env["ir.actions.report"]._render_qweb_html(
            "l10n_cssk_hr_payroll_garnishment_base.report_garnishment_notice",
            end.ids)[0].decode()
        self.assertIn("§ 295 odst. 2", html)
        self.assertNotIn("§ 294 odst. 1", html)
