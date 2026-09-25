# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The contract-level minimum wage warning, and the job -> level inheritance.

The payslip top-up silently corrects a sub-minimum wage every month. That is
the right thing to PAY, but it means an unlawful contract can sit in the system
indefinitely without anyone noticing. These cover the warning that surfaces it,
and the part-time and dohoda cases where a lower monthly figure is perfectly
lawful and warning would be noise.
"""

from datetime import date

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestMinWageWarning(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {"name": "SK MinWage Co", "country_id": cls.env.ref("base.sk").id}
        )
        cls.env.user.company_ids |= cls.company
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=cls.company.ids)
        )
        cls.full_time = cls.env["resource.calendar"].create(
            {"name": "SK 40h/week", "company_id": cls.company.id}
        )

    def _version(self, wage, level="1", calendar=None):
        employee = self.env["hr.employee"].with_company(self.company).create(
            {
                "name": "Skusobny",
                "company_id": self.company.id,
                "resource_calendar_id": (calendar or self.full_time).id,
                "date_version": date(2026, 6, 1),
                "contract_date_start": date(2026, 6, 1),
                "wage": wage,
            }
        )
        employee.version_id.write(
            {
                "l10n_sk_wage_level": level,
                "resource_calendar_id": (calendar or self.full_time).id,
            }
        )
        return employee.version_id

    def _half_time(self):
        return self.env["resource.calendar"].create(
            {
                "name": "SK 20h/week",
                "company_id": self.company.id,
                "hours_per_day": 4.0,
                "attendance_ids": [
                    (0, 0, {
                        "name": day,
                        "dayofweek": str(i),
                        "hour_from": 8.0,
                        "hour_to": 12.0,
                        "day_period": "morning",
                    })
                    for i, day in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri"])
                ],
            }
        )

    def test_no_warning_at_the_minimum_wage(self):
        self.assertFalse(self._version(915.0).l10n_sk_min_wage_warning)

    def test_warning_below_the_level_1_claim(self):
        warning = self._version(800.0).l10n_sk_min_wage_warning
        self.assertTrue(warning)
        self.assertIn("915", warning)

    def test_a_higher_level_raises_the_bar(self):
        """€1000 clears level 1 but not the €1147 level-3 claim."""
        self.assertFalse(self._version(1000.0, level="1").l10n_sk_min_wage_warning)
        warning = self._version(1000.0, level="3").l10n_sk_min_wage_warning
        self.assertTrue(warning)
        self.assertIn("1147", warning)

    def test_a_part_timer_on_a_proportionate_wage_is_not_warned(self):
        """§ 120 ods. 4 halves the claim for a half-time contract.

        Warning here would be the false positive that trains people to ignore
        the banner.
        """
        version = self._version(500.0, calendar=self._half_time())
        self.assertFalse(version.l10n_sk_min_wage_warning)

    def test_a_part_timer_below_the_prorated_claim_is_warned(self):
        version = self._version(300.0, calendar=self._half_time())
        self.assertTrue(version.l10n_sk_min_wage_warning)

    def test_non_sk_company_is_never_warned(self):
        other = self.env["res.company"].create(
            {"name": "CZ Co", "country_id": self.env.ref("base.cz").id}
        )
        employee = self.env["hr.employee"].with_company(other).create(
            {
                "name": "Cesky",
                "company_id": other.id,
                "date_version": date(2026, 6, 1),
                "contract_date_start": date(2026, 6, 1),
                "wage": 100.0,
            }
        )
        self.assertFalse(employee.version_id.l10n_sk_min_wage_warning)


@tagged("post_install", "-at_install")
class TestJobWageLevel(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {"name": "SK Job Co", "country_id": cls.env.ref("base.sk").id}
        )
        cls.env.user.company_ids |= cls.company
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=cls.company.ids)
        )

    def _job(self, level):
        return self.env["hr.job"].with_company(self.company).create(
            {"name": "Odborny pracovnik", "l10n_sk_wage_level": level}
        )

    def test_contract_inherits_the_jobs_level(self):
        employee = self.env["hr.employee"].with_company(self.company).create(
            {"name": "Novy", "company_id": self.company.id}
        )
        version = employee.version_id
        version.job_id = self._job("4")
        version._onchange_l10n_sk_job_wage_level()
        self.assertEqual(version.l10n_sk_wage_level, "4")

    def test_an_explicit_level_is_not_overwritten(self):
        """A contract may legitimately differ from its post."""
        employee = self.env["hr.employee"].with_company(self.company).create(
            {"name": "Vynimka", "company_id": self.company.id}
        )
        version = employee.version_id
        version.l10n_sk_wage_level = "5"
        version.job_id = self._job("2")
        version._onchange_l10n_sk_job_wage_level()
        self.assertEqual(version.l10n_sk_wage_level, "5")

    def test_a_job_without_a_level_leaves_the_contract_alone(self):
        employee = self.env["hr.employee"].with_company(self.company).create(
            {"name": "Bezstupna", "company_id": self.company.id}
        )
        version = employee.version_id
        version.job_id = self.env["hr.job"].with_company(self.company).create(
            {"name": "Neklasifikovane"}
        )
        version._onchange_l10n_sk_job_wage_level()
        self.assertFalse(version.l10n_sk_wage_level)

    def test_an_unclassified_contract_is_treated_as_level_1(self):
        """Empty must behave as the plain minimum wage, not as no claim.

        The field carries no default so that the job can fill it and so that
        "unclassified" is visible. That must not turn into "no minimum wage
        applies" anywhere downstream.
        """
        employee = self.env["hr.employee"].with_company(self.company).create(
            {
                "name": "Neurcena",
                "company_id": self.company.id,
                "date_version": date(2026, 6, 1),
                "contract_date_start": date(2026, 6, 1),
                "wage": 800.0,
            }
        )
        version = employee.version_id
        self.assertFalse(version.l10n_sk_wage_level)
        warning = version.l10n_sk_min_wage_warning
        self.assertTrue(warning, "an unclassified post still owes 915")
        self.assertIn("915", warning)
