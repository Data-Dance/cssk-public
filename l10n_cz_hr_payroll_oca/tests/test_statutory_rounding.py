# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Whole-crown rounding the statutes prescribe on the payslip.

* § 5d zák. 589/1992 Sb.: "Vyměřovací základy podle § 5 až 5c se zaokrouhlují
  na celé koruny směrem nahoru."
* § 7 odst. 3 zák. 589/1992 Sb.: "Pojistné se zaokrouhluje na celé koruny
  směrem nahoru."
* § 38h odst. 1 ZDP: "Základ pro výpočet zálohy do 100 Kč se zaokrouhlí na
  celé koruny nahoru a nad 100 Kč na celé stokoruny nahoru."
* § 38h odst. 3 ZDP: "Zálohy vypočtené podle odstavce 2 se zaokrouhlují na
  celé koruny nahoru."
* § 146 odst. 1 daňového řádu: "Daň se zaokrouhluje na celé koruny nahoru."

Every expected figure is computed by hand in the test's docstring.
"""

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCzStatutoryRounding(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {"name": "CZ Rounding Co", "country_id": cls.env.ref("base.cz").id}
        )
        cls.env.user.company_ids |= cls.company
        cls.env.user.group_ids |= cls.env.ref("payroll.group_payroll_manager")
        cls.env = cls.env(context=dict(
            cls.env.context, allowed_company_ids=cls.company.ids))
        cls.calendar = cls.env["resource.calendar"].create(
            {"name": "CZ 40h/week", "company_id": cls.company.id}
        )
        cls.structure = cls.env.ref(
            "l10n_cz_hr_payroll_oca.hr_payroll_structure_cz_employee_salary"
        )

    def _employee(self, name, wage, **version_vals):
        employee = self.env["hr.employee"].with_company(self.company).create({
            "name": name,
            "company_id": self.company.id,
            "resource_calendar_id": self.calendar.id,
            "date_version": date(2024, 1, 1),
            "contract_date_start": date(2024, 1, 1),
            "wage": wage,
            "struct_id": self.structure.id,
        })
        if version_vals:
            employee.version_id.write(version_vals)
        return employee

    def _payslip(self, employee, month=3, confirm=False):
        d_from = date(2026, month, 1)
        payslip = self.env["hr.payslip"].with_company(self.company).create({
            "name": "Payslip %s %s" % (employee.name, month),
            "employee_id": employee.id,
            "contract_id": employee.version_id.id,
            "struct_id": self.structure.id,
            "company_id": self.company.id,
            "date_from": d_from,
            "date_to": d_from + relativedelta(day=31),
        })
        payslip.compute_sheet()
        if confirm:
            payslip.write({"state": "done"})
        return payslip

    def _line(self, payslip, code):
        return payslip.line_ids.filtered(lambda line: line.code == code)

    def _t(self, payslip, code):
        return round(sum(self._line(payslip, code).mapped("total")), 2)

    def _tiny_calendar(self):
        """Six minutes every Monday: half an hour in March 2026, so the
        minimum wage for the month is far below 100 Kč."""
        return self.env["resource.calendar"].create({
            "name": "CZ six minutes a week",
            "company_id": self.company.id,
            "attendance_ids": [(0, 0, {
                "name": "Monday",
                "dayofweek": "0",
                "hour_from": 8.0,
                "hour_to": 8.1,
                "day_period": "morning",
            })],
        })

    # -- Social insurance -------------------------------------------------

    def test_employee_premium_is_rounded_up(self):
        """51 263 x 7.1 % = 3 639.673 -> 3 640. Health 13.5 % = 6 920.505 ->
        6 921, a third 2 307. Advance: base 51 300 x 15 % = 7 695 - 2 570 =
        5 125. NET 51 263 - 3 640 - 2 307 - 5 125 = 40 191, whole crowns."""
        p = self._payslip(self._employee(
            "Premium Up", 51263.0, l10n_cz_tax_declaration=True))
        self.assertEqual(self._t(p, "SOCIALEE"), -3640.0)
        self.assertEqual(self._t(p, "SOCIALEETOT"), -3640.0)
        self.assertEqual(self._t(p, "NET"), 40191.0)
        # The employer's line keeps the base and the heller: 51 263 x 24.8 %.
        self.assertEqual(self._line(p, "SOCIALER").amount, 51263.0)
        self.assertEqual(self._t(p, "SOCIALER"), 12713.22)

    def test_whole_premium_is_unchanged(self):
        """50 000 x 7.1 % = 3 550 exactly: nothing to round."""
        p = self._payslip(self._employee("Premium Whole", 50000.0))
        self.assertEqual(self._t(p, "SOCIALEE"), -3550.0)
        self.assertEqual(self._t(p, "SOCIALER"), 12400.0)

    def test_fraction_below_a_heller_still_rounds_up(self):
        """30 831 x 7.1 % = 2 189.001 -> 2 190: the premium is rounded from
        the exact product, not from a figure already cut to hellers."""
        p = self._payslip(self._employee("Premium Thousandth", 30831.0))
        self.assertEqual(self._t(p, "SOCIALEE"), -2190.0)

    def test_assessment_base_is_rounded_up(self):
        """Gross 30 000.40 -> base 30 001. Employee 30 001 x 7.1 % =
        2 130.071 -> 2 131; employer 30 001 x 24.8 % = 7 440.248 -> 7 440.25
        on the payslip."""
        p = self._payslip(self._employee("Base Up", 30000.40))
        self.assertEqual(self._t(p, "GROSS"), 30000.40)
        self.assertEqual(self._line(p, "SOCIALER").amount, 30001.0)
        self.assertEqual(self._t(p, "SOCIALER"), 7440.25)
        self.assertEqual(self._t(p, "SOCIALEE"), -2131.0)

    def test_maximum_base_counts_rounded_bases(self):
        """January 1 200 000.40 is an assessment base of 1 200 001, so of the
        2026 maximum 2 350 416 February has 1 150 415 left: employee
        1 150 415 x 7.1 % = 81 679.465 -> 81 680."""
        employee = self._employee("Base Maximum", 1200000.40)
        january = self._payslip(employee, month=1, confirm=True)
        self.assertEqual(self._line(january, "SOCIALER").amount, 1200001.0)
        february = self._payslip(employee, month=2)
        self.assertEqual(self._line(february, "SOCIALER").amount, 1150415.0)
        self.assertEqual(self._t(february, "SOCIALEE"), -81680.0)

    def test_working_pensioner_pays_whole_crowns(self):
        """40 011: premium 2 840.781 -> 2 841, discount 6.5 % = 2 600.715 ->
        2 601 (§ 7e odst. 1), withheld 240."""
        p = self._payslip(self._employee(
            "Pensioner", 40011.0, l10n_cz_pensioner_discount=True))
        self.assertEqual(self._t(p, "SOCIAL_PENSIONER"), 2601.0)
        self.assertEqual(self._t(p, "SOCIALEETOT"), -240.0)

    def test_employer_discount_follows_the_rounded_base(self):
        """Under 21 on 20 010.40: base 20 011, discount line 5 % = 1 000.55."""
        calendar = self.env["resource.calendar"].create({
            "name": "CZ 20h/week",
            "company_id": self.company.id,
            "attendance_ids": [(0, 0, {
                "name": "Day %s" % day,
                "dayofweek": str(day),
                "hour_from": 8.0,
                "hour_to": 12.0,
                "day_period": "morning",
            }) for day in range(5)],
        })
        p = self._payslip(self._employee(
            "Discount", 20010.40,
            l10n_cz_social_discount_category="under21",
            resource_calendar_id=calendar.id))
        self.assertEqual(self._line(p, "SOCIALER").amount, 20011.0)
        self.assertEqual(self._t(p, "SOCIAL_DISCOUNT"), -1000.55)

    # -- Income tax advance -----------------------------------------------

    def test_advance_is_rounded_up_above_the_threshold(self):
        """150 000 in 2026: 15 % of 146 901 = 22 035.15, 23 % of 3 099 =
        712.77, together 22 747.92 -> 22 748. Less the 2 570 credit the
        advance is 20 178. NET 150 000 - 10 650 - 6 750 - 20 178 = 112 422."""
        p = self._payslip(self._employee(
            "Advance Up", 150000.0, l10n_cz_tax_declaration=True))
        self.assertEqual(self._t(p, "INCOMETAX"), -22748.0)
        self.assertEqual(self._t(p, "INCOMETAXTOT"), 22748.0)
        self.assertEqual(self._t(p, "NET"), 112422.0)

    def test_advance_below_the_threshold_is_unchanged(self):
        """50 000 x 15 % = 7 500 exactly."""
        p = self._payslip(self._employee(
            "Advance Whole", 50000.0, l10n_cz_tax_declaration=True))
        self.assertEqual(self._t(p, "INCOMETAX"), -7500.0)

    def test_base_up_to_100_is_rounded_to_crowns(self):
        """A declared DPP of 90.40 for half an hour's work: the base is 91,
        not 100, and the advance 91 x 15 % = 13.65 -> 14, cancelled by the
        taxpayer credit."""
        p = self._payslip(self._employee(
            "Small Base", 90.40,
            l10n_cz_agreement_type="dpp", l10n_cz_tax_declaration=True,
            resource_calendar_id=self._tiny_calendar().id))
        self.assertEqual(self._t(p, "TAXBASE"), 90.40)
        self.assertEqual(self._t(p, "INCOMETAX"), -14.0)
        self.assertEqual(self._t(p, "NET"), 90.40)

    # -- Annual settlement --------------------------------------------------

    def test_annual_tax_is_rounded_up(self):
        """12 x 170 000 less 40 000 of pension contributions: base 2 000 000.
        15 % of 1 762 812 = 264 421.80, 23 % of 237 188 = 54 553.24, together
        318 975.04 -> 318 976. Monthly advance 22 035.15 + 23 % of 23 099 =
        27 347.92 -> 27 348, less 2 570 = 24 778; twelve times 297 336. Tax
        after the 30 840 credit 288 136, overpayment 9 200."""
        employee = self._employee(
            "Annual", 170000.0, l10n_cz_tax_declaration=True)
        for month in range(1, 13):
            self._payslip(employee, month=month, confirm=True)
        recon = self.env["hr.payroll.cz.annual.tax.recon"].create({
            "employee_id": employee.id,
            "company_id": self.company.id,
            "year": 2026,
            "l10n_cz_pension_contrib": 40000.0,
        })
        recon.action_compute()
        self.assertEqual(recon.l10n_cz_annual_tax_base, 2000000.0)
        self.assertEqual(recon.l10n_cz_annual_tax, 318976.0)
        self.assertEqual(recon.l10n_cz_advances_withheld, 297336.0)
        self.assertEqual(recon.l10n_cz_annual_final_tax, 288136.0)
        self.assertEqual(recon.l10n_cz_overpayment, 9200.0)
