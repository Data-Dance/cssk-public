# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The child bonus of a child of 18 or over (2023 and 2024) and the exact
hourly rate."""

import calendar
from datetime import date
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSkRates(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {"name": "SK rates", "country_id": cls.env.ref("base.sk").id}
        )
        cls.env.user.company_ids |= cls.company
        cls.calendar = cls.env["resource.calendar"].create(
            {"name": "SK 40h/week", "company_id": cls.company.id}
        )
        cls.structure = cls.env.ref(
            "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_employee_salary"
        )

    def setUp(self):
        super().setUp()
        # The minimum wage top-up of the surcharges has its own tests.
        Payslip = type(self.env["hr.payslip"])
        if hasattr(Payslip, "_l10n_sk_min_wage_claim_applies"):
            patcher = patch.object(
                Payslip, "_l10n_sk_min_wage_claim_applies", return_value=False
            )
            patcher.start()
            self.addCleanup(patcher.stop)

    def _contract(self, name, wage=0.0, calendar_=None, structure=None, **vals):
        calendar_ = calendar_ or self.calendar
        employee = self.env["hr.employee"].create(
            {
                "name": name,
                "company_id": self.company.id,
                "resource_calendar_id": calendar_.id,
            }
        )
        values = {
            "contract_date_start": date(2024, 1, 1),
            "date_version": date(2024, 1, 1),
            "wage": wage,
            "resource_calendar_id": calendar_.id,
            "struct_id": (structure or self.structure).id,
        }
        values.update(vals)
        employee.version_id.write(values)
        return employee.version_id, employee

    def _slip(self, contract, employee, year, month):
        slip = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "name": "Slip %s/%s" % (month, year),
                    "employee_id": employee.id,
                    "contract_id": contract.id,
                    "struct_id": contract.struct_id.id,
                    "company_id": self.company.id,
                    "date_from": date(year, month, 1),
                    "date_to": date(year, month, calendar.monthrange(year, month)[1]),
                }
            )
        )
        # What the form does: fill the worked-day lines.
        slip.onchange_dates()
        slip.compute_sheet()
        return slip

    # ------------------------------------------------------------------
    # § 52zzp ods. 4 and 5 zákona 595/2003: a child of 18 or over
    # ------------------------------------------------------------------
    def _bonus(self, year, month, wage, **children):
        contract, employee = self._contract(
            "Bonus %s-%s %s" % (year, month, wage), wage,
            l10n_sk_tax_declaration_signed=True, **children)
        slip = self._slip(contract, employee, year, month)
        return slip.get_salary_line_total("CHILD_BONUS")

    def test_child_of_18_or_over_has_50_in_december_2024(self):
        self.assertEqual(self._bonus(2024, 12, 2000.0, l10n_sk_children_over_18=1), 50.0)

    def test_child_of_18_or_over_counts_for_the_limit_in_2024(self):
        """1 000 € in December 2024: tax base 866,00.

        Two children under 18 and one over: 140 + 140 + 50 = 330, limited to
        34 % for three children, 294,44 (27 % for two would be 233,82).
        """
        bonus = self._bonus(2024, 12, 1000.0, l10n_sk_children_under_15=2,
                            l10n_sk_children_over_18=1)
        self.assertEqual(bonus, 294.44)

    def test_count_left_filled_gives_nothing_from_january_2025(self):
        self.assertEqual(self._bonus(2025, 1, 2000.0, l10n_sk_children_over_18=1), 0.0)

    def test_count_left_filled_does_not_raise_the_limit_from_2025(self):
        """850 € in January 2025: tax base 736,10, four children under 15.

        400 limited to 50 % for four children, 368,05; a fifth child counted
        would give 57 % and the whole 400.
        """
        bonus = self._bonus(2025, 1, 850.0, l10n_sk_children_under_15=4,
                            l10n_sk_children_over_18=1)
        self.assertEqual(bonus, 368.05)

    def test_annual_settlement_knows_the_child_of_18_or_over(self):
        contract, employee = self._contract(
            "Annual over 18", 2000.0, l10n_sk_children_over_18=1)
        Settlement = self.env["l10n.sk.tax.reconciliation"]
        vals = {"employee_id": employee.id, "company_id": self.company.id,
                "gather_from_payslips": False, "annual_tax_base": 20000.0}
        self.assertEqual(
            Settlement.create(dict(vals, year=2024)).child_bonus_entitlement, 600.0)
        self.assertEqual(
            Settlement.create(dict(vals, year=2025)).child_bonus_entitlement, 0.0)

    # ------------------------------------------------------------------
    # An hourly rate with three decimals (§ 2 ods. 2 zákona 663/2007)
    # ------------------------------------------------------------------
    def test_hourly_rate_keeps_three_decimals(self):
        """The 2026 minimum hourly wage for June's 176 hours: 925,584."""
        contract, employee = self._contract("Hourly minimum", l10n_sk_hourly_wage=5.259)
        self.assertEqual(contract.l10n_sk_hourly_wage, 5.259)
        slip = self._slip(contract, employee, 2026, 6)
        self.assertEqual(slip.get_salary_line_total("BASIC"), 925.59)
        self.assertEqual(slip.get_salary_line_total("GROSS"), 925.59)

    def test_hourly_rate_with_fractional_hours(self):
        """165 hours of a 7,5-hour day at 5,259: 867,735, so 867,74."""
        short_days = self.env["resource.calendar"].create(
            {
                "name": "SK 37,5 h",
                "company_id": self.company.id,
                "hours_per_day": 7.5,
                "attendance_ids": [
                    (0, 0, {"name": "Day %s" % day, "dayofweek": str(day),
                            "hour_from": 8.0, "hour_to": 15.5,
                            "day_period": "morning"})
                    for day in range(5)
                ],
            }
        )
        contract, employee = self._contract(
            "Hourly short day", calendar_=short_days, l10n_sk_hourly_wage=5.259)
        slip = self._slip(contract, employee, 2026, 6)
        worked = slip.worked_days_line_ids.filtered(lambda x: x.code == "WORK100")
        self.assertEqual(worked.number_of_hours, 165.0)
        self.assertEqual(slip.get_salary_line_total("BASIC"), 867.74)

    def test_probable_earnings_of_an_hourly_wage_are_the_rate(self):
        """No payslip of the previous quarter: the hourly rate itself."""
        contract, employee = self._contract("Hourly probable", l10n_sk_hourly_wage=10.123)
        slip = self._slip(contract, employee, 2026, 6)
        self.assertEqual(slip.l10n_sk_average_hourly_earnings(), 10.123)

    def test_agreement_rate_under_the_minimum_by_a_fraction_of_a_cent_warns(self):
        """5,255 is under the 2026 minimum of 5,259; to the cent it is 5,26."""
        dopc = self.env.ref("l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_dopc")
        contract, _employee = self._contract(
            "Agreement rate", structure=dopc, l10n_sk_agreement_type="dopc",
            l10n_sk_hourly_wage=5.255, contract_date_end=date(2026, 6, 30))
        self.assertTrue(contract.l10n_sk_agreement_wage_warning)
