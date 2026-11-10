# Copyright 2026 Data Dance s.r.o., votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Section 138(13): floor the daily limit before multiplying insured days."""

from datetime import date

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSocialDailyCap(TransactionCase):
    def _version(self, start, end=False):
        employee = self.env["hr.employee"].create(
            {
                "name": "Daily cap fixture",
                "company_id": self.env.company.id,
                "date_version": start,
                "contract_date_start": start,
                "contract_date_end": end,
            }
        )
        return employee.version_id

    def test_daily_cent_rounding_precedes_partial_month_multiplication(self):
        cases = (
            # The 2026 maximum is 16,764 EUR. 540.77 x 5, not floor(16764*5/31).
            (date(2026, 3, 16), date(2026, 3, 20), 16764, 2703.85),
            (date(2026, 1, 16), date(2026, 1, 31), 16764, 8652.32),
            (date(2026, 2, 1), date(2026, 2, 5), 16764, 2993.55),
            # Leap February; the 2024 maximum is 9,128 EUR.
            (date(2024, 2, 1), date(2024, 2, 5), 9128, 1573.75),
        )
        for start, end, maximum, expected in cases:
            with self.subTest(start=start, end=end):
                version = self._version(start, end)
                self.assertEqual(
                    version.l10n_sk_employee_social_cap(maximum, start), expected
                )

    def test_full_month_and_no_insured_days_keep_their_boundaries(self):
        version = self._version(date(2026, 1, 1), date(2026, 3, 31))
        self.assertEqual(
            version.l10n_sk_employee_social_cap(16764, date(2026, 3, 1)), 16764
        )
        self.assertEqual(
            version.l10n_sk_employee_social_cap(16764, date(2025, 12, 1)), 0
        )
        self.assertEqual(
            version.l10n_sk_employee_social_cap(16764, date(2026, 4, 1)), 0
        )
