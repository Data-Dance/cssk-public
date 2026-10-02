# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date
from unittest.mock import MagicMock, patch

from odoo.tests import TransactionCase, tagged

GET = "odoo.addons.currency_rate_update_cz.models.res_currency_rate_provider_CNB.requests.get"

CNB_SAMPLE = """12 Jun 2026 #112
Country|Currency|Amount|Code|Rate
EMU|euro|1|EUR|24.170
Japan|yen|100|JPY|13.043
USA|dollar|1|USD|20.894
"""


YEAR_2022 = """Date|1 EUR|100 HUF|100 RUB
01.03.2022|24.800|6.700|22.000
02.03.2022|24.900|6.650|21.000
Date|1 EUR|100 HUF
30.12.2022|24.100|6.500
"""

YEAR_2023 = """Date|1 EUR|100 HUF
02.01.2023|24.200|6.400
03.01.2023|24.250|6.410
"""

DAILY_2022_12_30 = """30 Dec 2022 #250
Country|Currency|Amount|Code|Rate
EMU|euro|1|EUR|24.100
"""


@tagged("post_install", "-at_install")
class TestCzFx(TransactionCase):
    def setUp(self):
        super().setUp()
        # Per test, not per class: a new() record lives only in the cache,
        # which each test's rollback clears — a class-level one comes back
        # with no service and falls through to the base provider, which
        # fetches nothing and fails nothing.
        self.provider = self.env["res.currency.rate.provider"].new({"service": "CNB"})

    def test_parse_foreign_per_czk(self):
        content = self.provider._cnb_parse(CNB_SAMPLE, ["EUR", "JPY", "USD"])
        self.assertEqual(list(content.keys()), [date(2026, 6, 12)])
        rates = content[date(2026, 6, 12)]
        # 1 EUR = 24.170 CZK -> EUR per CZK = 1/24.170
        self.assertAlmostEqual(float(rates["EUR"]), 1 / 24.170, places=6)
        # 100 JPY = 13.043 CZK -> JPY per CZK = 100/13.043
        self.assertAlmostEqual(float(rates["JPY"]), 100 / 13.043, places=6)
        self.assertAlmostEqual(float(rates["USD"]), 1 / 20.894, places=6)

    def _fake(self, text):
        fake = MagicMock()
        fake.raise_for_status.return_value = None
        fake.text = text
        return fake

    def test_a_single_day_uses_the_daily_feed(self):
        with patch(GET, return_value=self._fake(CNB_SAMPLE)) as mock_get:
            content = self.provider._obtain_rates(
                "CZK", ["EUR"], date(2026, 6, 12), date(2026, 6, 12))
        # the date param is passed in DD.MM.YYYY
        self.assertEqual(mock_get.call_args.kwargs["params"]["date"], "12.06.2026")
        self.assertIn("EUR", content[date(2026, 6, 12)])

    def test_a_range_stores_every_fixing_in_it(self):
        """It used to fetch the daily feed for date_to only, so *Update
        rates* over a range stored its last day and nothing else."""
        def get(url, params=None, **kw):
            self.assertIn("year.txt", url)
            return self._fake(YEAR_2022 if params["year"] == 2022 else YEAR_2023)

        with patch(GET, side_effect=get) as mock_get:
            content = self.provider._obtain_rates(
                "CZK", ["EUR", "RUB", "HUF"], date(2022, 3, 1), date(2023, 1, 3))
        self.assertEqual(mock_get.call_count, 2)  # one request a year
        self.assertEqual(
            sorted(content),
            [date(2022, 3, 1), date(2022, 3, 2), date(2022, 12, 30),
             date(2023, 1, 2), date(2023, 1, 3)])
        self.assertAlmostEqual(
            float(content[date(2022, 3, 1)]["EUR"]), 1 / 24.8, places=6)
        # 100 HUF per 6.5 CZK -> HUF per CZK = 100 / 6.5
        self.assertAlmostEqual(
            float(content[date(2022, 12, 30)]["HUF"]), 100 / 6.5, places=6)

    def test_the_column_set_restarts_at_a_repeated_header(self):
        """2022 drops the rouble mid-year; the columns after the second
        header must not be read against the first."""
        content = self.provider._cnb_parse_year(YEAR_2022, ["EUR", "RUB", "HUF"])
        self.assertIn("RUB", content[date(2022, 3, 1)])
        self.assertNotIn("RUB", content[date(2022, 12, 30)])
        self.assertAlmostEqual(
            float(content[date(2022, 12, 30)]["EUR"]), 1 / 24.1, places=6)

    def test_a_range_starting_on_a_holiday_takes_the_last_fixing_before_it(self):
        def get(url, params=None, **kw):
            if "year.txt" in url:
                return self._fake(YEAR_2023)
            self.assertEqual(params["date"], "01.01.2023")
            return self._fake(DAILY_2022_12_30)

        with patch(GET, side_effect=get):
            content = self.provider._obtain_rates(
                "CZK", ["EUR"], date(2023, 1, 1), date(2023, 1, 3))
        self.assertIn(date(2022, 12, 30), content)
        self.assertIn(date(2023, 1, 2), content)


YEAR_MONTHLY = """Date|1 EUR
30.12.2022|24.100
02.01.2023|24.200
31.01.2023|24.400
01.02.2023|24.500
"""


@tagged("post_install", "-at_install")
class TestCzFixedMonthlyRate(TransactionCase):
    """Pevný kurz: one rate per month, dated the 1st; the actual fixings are
    kept apart for the balance-sheet revaluation."""

    def setUp(self):
        super().setUp()
        self.eur = self.env.ref("base.EUR")
        self.eur.active = True
        self.provider = self.env["res.currency.rate.provider"].new({
            "service": "CNB", "company_id": self.env.company.id,
            "cnb_rate_mode": "monthly",
        })

    def _fake(self, text):
        fake = MagicMock()
        fake.raise_for_status.return_value = None
        fake.text = text
        return fake

    def _obtain(self, reference):
        self.provider.cnb_monthly_reference = reference
        daily = "16 Dec 2022 #243\nCountry|Currency|Amount|Code|Rate\nEMU|euro|1|EUR|24.300\n"
        with patch(GET, side_effect=lambda url, params=None, **kw: self._fake(
                daily if "date" in params else YEAR_MONTHLY)):
            return self.provider._obtain_rates(
                "CZK", ["EUR"], date(2023, 1, 1), date(2023, 2, 28))

    def test_one_rate_a_month_dated_the_first(self):
        content = self._obtain("first_day")
        self.assertEqual(sorted(content), [date(2023, 1, 1), date(2023, 2, 1)])
        # 1. 1. has no fixing: the rate valid then is 30. 12.'s
        self.assertAlmostEqual(float(content[date(2023, 1, 1)]["EUR"]), 1 / 24.1, places=6)
        self.assertAlmostEqual(float(content[date(2023, 2, 1)]["EUR"]), 1 / 24.5, places=6)

    def test_the_previous_month_end_reference(self):
        content = self._obtain("previous_month_end")
        self.assertAlmostEqual(float(content[date(2023, 2, 1)]["EUR"]), 1 / 24.4, places=6)

    def test_the_actual_fixings_are_kept_apart(self):
        self._obtain("first_day")
        actual = self.env["cssk.currency.rate.actual"].search([
            ("currency_id", "=", self.eur.id),
            ("company_id", "=", self.env.company.id)])
        self.assertEqual(
            sorted(actual.mapped("name")),
            [date(2022, 12, 16), date(2022, 12, 30), date(2023, 1, 2),
             date(2023, 1, 31), date(2023, 2, 1)])

    def test_the_revaluation_context_reads_the_actual_rate(self):
        company = self.env.company
        if company.currency_id == self.eur:
            self.skipTest("the test company must not keep its books in EUR")
        self.env["res.currency.rate"].search([
            ("currency_id", "=", self.eur.id)]).unlink()
        self.env["res.currency.rate"].create({
            "currency_id": self.eur.id, "name": "2023-12-01",
            "rate": 1 / 25.0, "company_id": company.id})
        self.env["cssk.currency.rate.actual"].create({
            "currency_id": self.eur.id, "name": "2023-12-29",
            "rate": 1 / 24.0, "company_id": company.id})
        fixed = self.eur._convert(100.0, company.currency_id, company, date(2023, 12, 31))
        actual = self.eur.with_context(cssk_actual_rates=True)._convert(
            100.0, company.currency_id, company, date(2023, 12, 31))
        self.assertAlmostEqual(fixed, 2500.0)
        self.assertAlmostEqual(actual, 2400.0)
