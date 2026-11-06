# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import tagged
from datetime import date
from .test_sk_payroll import TestSkPayroll


@tagged('post_install', '-at_install')
class TestParameters2027(TestSkPayroll):
    def slip(self, wage=1000):
        contract, employee = self._make_contract(
            'Synthetic 2027 parameter case', wage, date(2026, 1, 1), self.calendar)
        slip = self._make_payslip(contract, employee, date(2026, 3, 1), date(2026, 3, 31))
        return employee, slip

    def profile(self, wage=1000, declaration=True, year=2027):
        employee, slip = self.slip(wage=wage)
        employee.version_id.l10n_sk_tax_declaration_signed = declaration
        slip.write({'date_from': f'{year}-01-01', 'date_to': f'{year}-01-31'})
        slip.compute_sheet()
        return employee, slip

    def test_dated_parameter_table_2027(self):
        _, slip = self.profile()
        expected = {'l10n_sk_monthly_taxable_max': 17820,
                    'l10n_sk_health_min_base': 295.22,
                    'l10n_sk_nczd_monthly': 516.64, 'l10n_sk_nczd_annual': 6199.62,
                    'l10n_sk_nczd_taper_threshold': 27101.20,
                    'l10n_sk_nczd_taper_const': 15233.35,
                    'l10n_sk_child_bonus_taper_threshold': 29160,
                    'l10n_sk_min_hourly_wage': 5.586,
                    'l10n_sk_pn_max_dvz': 106.5206,
                    'l10n_sk_dohoda_oop_seasonal': 810}
        for code, value in expected.items():
            with self.subTest(code=code):
                self.assertAlmostEqual(slip.rule_parameter(code), value, places=4)

    def test_monthly_nczd_changes_net(self):
        _, slip = self.profile()
        self.assertAlmostEqual(slip.get_salary_line_total('TAXBASE'), 856)
        self.assertAlmostEqual(slip.get_salary_line_total('INCOMETAX'), -64.48, places=2)
        self.assertAlmostEqual(slip.get_salary_line_total('NET'), 791.52, places=2)

    def test_2026_recalculation_keeps_old_values(self):
        self.profile()
        _, old = self.profile(year=2026)
        self.assertEqual(old.rule_parameter('l10n_sk_nczd_monthly'), 497.23)
        self.assertEqual(old.rule_parameter('l10n_sk_monthly_taxable_max'), 16764)
        self.assertAlmostEqual(old.get_salary_line_total('NET'), 787.83, places=2)

    def test_second_monthly_tax_band(self):
        _, slip = self.profile(5200, declaration=False)
        self.assertAlmostEqual(slip.get_salary_line_total('TAXBASE'), 4451.20, places=2)
        self.assertAlmostEqual(slip.get_salary_line_total('INCOMETAX'), -884.30, places=2)

    def test_social_cap_and_uncapped_health_accident(self):
        _, slip = self.profile(20000, declaration=False)
        for code, value in {'SICK': -249.48, 'PENSION': -712.80,
                            'DISABILITY': -534.60, 'UNEMPLOYMENT': -178.20,
                            'HEALTH': -1000, 'HEALTHEMPLOYER': 2200,
                            'ACCIDENT': 160}.items():
            self.assertAlmostEqual(slip.get_salary_line_total(code), value, places=2, msg=code)

    def test_health_minimum_2027(self):
        _, slip = self.profile(100)
        self.assertAlmostEqual(slip.get_salary_line_total('HEALTHDOPLATOK'), -31.23, places=2)

    def test_child_bonus_taper_2027(self):
        employee, slip = self.profile(2950)
        employee.version_id.l10n_sk_children_under_15 = 1
        slip.compute_sheet()
        self.assertAlmostEqual(slip.get_salary_line_total('TAXBASE'), 2525.20, places=2)
        self.assertAlmostEqual(slip.get_salary_line_total('CHILD_BONUS'), 90.48, places=2)

    def test_annual_nczd_and_taper(self):
        for base, nczd, tax in ((24000, 6199.62, 3382.07),
                                (30000, 5233.35, 4705.66),
                                (50000, 0, 9758.00)):
            with self.subTest(base=base):
                employee, _ = self.profile()
                annual = self.env['l10n.sk.tax.reconciliation'].create({
                    'company_id': self.company.id, 'employee_id': employee.id,
                    'year': 2027, 'gather_from_payslips': False, 'annual_tax_base': base})
                annual.action_compute()
                self.assertAlmostEqual(annual.nczd_taxpayer, nczd, places=2)
                self.assertAlmostEqual(annual.annual_tax, tax, places=2)
